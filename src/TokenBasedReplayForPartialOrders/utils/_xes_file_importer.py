from typing import Dict, Tuple, List, Any, Hashable

import pandas as pd
import pm4py
from networkx import DiGraph
from numpy import ndarray, dtype
from pandas import DataFrame, Series
from pm4py.objects.conversion.log import converter as log_converter

from src.TokenBasedReplayForPartialOrders.structures._partially_ordered_event_log import PartiallyOrderedEventLog
from src.TokenBasedReplayForPartialOrders.structures._run import EventForRun, Run
from src.TokenBasedReplayForPartialOrders.structures._total_order_for_run import TotalOrder4Run
from src.TokenBasedReplayForPartialOrders.structures._workflow_net import TransitionWorkflowNet


# TODO why do I need a special method for totally ordered logs again?
def import_xes_file_totally_ordered_log(
        file_path: str,
        name_to_transition: dict[str, TransitionWorkflowNet],
        include_traces_with_invalid_transitions=True) \
        -> (PartiallyOrderedEventLog, dict[str, str]):
    """
    :param include_traces_with_invalid_transitions: see the importer for po xes files
    :param file_path:
    :param name_to_transition:
    :return: The totally ordered event log, which is returned as partially ordered log to be compatible with the existing
             conformance analysis code. All runs in the result will get the unique total order.
             Additionally, we return a dictionary with all invalid trace names together with the first invalid transition label.
    """
    if "START" not in name_to_transition or "END" not in name_to_transition:
        raise ValueError("Missing required transitions: 'START' and 'END' must be present in name_to_transition.")
    log_external_format = pm4py.read_xes(file_path)
    df: DataFrame = log_converter.apply(log_external_format, variant=log_converter.Variants.TO_DATA_FRAME)
    trace_to_frequency: dict[Run, int] = dict()
    # The traces are not yet grouped, so we have to do this; following dict helps us for this
    trace_class_to_represent: dict[tuple, Run] = dict()
    invalid_trace_to_false_label: dict[str, str] = dict()
    for trace_id, df_part in df.groupby("case:concept:name"):
        # Just to be sure we sort the part
        df_part = df_part.sort_values(by="time:timestamp", kind="stable")
        event_list: list[EventForRun] = list()
        # First, prepare the events; if any event has an invalid transition, we skip
        has_trace_invalid_event_label: bool = False
        start_transition: TransitionWorkflowNet = name_to_transition["START"]
        start_event: EventForRun = EventForRun(f"Start event of PO {trace_id}", start_transition)
        event_list.append(start_event)
        for transition_name in df_part["concept:name"]:
            # In the log the label of a transition in the name is used as name. Have to translate this to original
            transition_name_to_use = transition_name
            if transition_name not in name_to_transition:
                has_trace_invalid_event_label = True
                invalid_trace_to_false_label[trace_id] = transition_name
                if not include_traces_with_invalid_transitions:
                    break
                else:
                    transition_name_to_use = "INVALID"
            transition = name_to_transition[transition_name_to_use]
            event: EventForRun = EventForRun(f"Event (Label: {transition.activity_description}) from Trace {str(trace_id)}", transition)
            event_list.append(event)
        if has_trace_invalid_event_label and not include_traces_with_invalid_transitions:
            continue
        end_transition: TransitionWorkflowNet = name_to_transition["END"]
        end_event: EventForRun = EventForRun(f"End event of PO {trace_id}", end_transition)
        event_list.append(end_event)
        graph_for_po: DiGraph = DiGraph()
        edges_linear_graph = [(event_list[index], event_list[index + 1]) for index in range(len(event_list) - 1)]
        graph_for_po.add_edges_from(edges_linear_graph)
        run: Run = Run(graph_for_po)
        run.name_foreign_source = str(trace_id)
        # To be able to identify equivalent events we have to sort them now in our hashmap
        string_hash_value_for_run = tuple(event.label.activity_description for event in event_list)
        if string_hash_value_for_run in trace_class_to_represent:
            trace_to_frequency[trace_class_to_represent[string_hash_value_for_run]] += 1
        else:
            trace_class_to_represent[string_hash_value_for_run] = run
            # We only set the total order for the trace represent kept in the final log
            run.total_order = TotalOrder4Run.make_total_order_from_list(event_list)
            trace_to_frequency[run] = 1

    return PartiallyOrderedEventLog(trace_to_frequency), invalid_trace_to_false_label


def import_cco_xes_file_to_event_log(file_path: str,
                                     name_to_transition: dict[str, TransitionWorkflowNet],
                                     include_runs_with_invalid_transitions=True,
                                     event_id_to_successors: dict[int, list[int]] = None,
                                     add_start_and_end_events=True) \
        -> Tuple[PartiallyOrderedEventLog, dict[Any, str], dict[int, bool]]:
    """

    :param include_runs_with_invalid_transitions: if true all runs with invalid labels will be present in the result log, the invalid
                                                labels are then replaced by the standard invalid transition; if false they will not be included
    :param file_path:
    :param name_to_transition: parameter has the information on the corresponding transitions in the previously constructed workflow net in the internal format
    :param event_id_to_successors: required to deal with bug that occurs when reading xes-file with field for successors; this parameter allow to supply
                the correct values for events where the import failed to so (which is identified by a read None instead of an empty list)
    :param add_start_and_end_events indicates if start and end events should be added; in some models we have a dedicated start and ending transition
            which is usually not persisted in the xes file

    :return: - the event log in the internal format,
             - a dictionary of runs together with the first found invalid event label,
             - a dictionary where the keys are all event ids, where the bug with the successor reading appeared, and the values are flags
                indicating if the correct successor could be derived from the import parameter
    """
    if add_start_and_end_events and ("START" not in name_to_transition or "END" not in name_to_transition):
        raise ValueError("Missing required transitions: 'START' and 'END' must be present in name_to_transition.")
    log_external_format = pm4py.read_xes(file_path)
    df_log: pd.DataFrame = log_converter.apply(log_external_format, variant=log_converter.Variants.TO_DATA_FRAME)

    run_to_frequency: dict[Run, int] = {}
    invalid_run_to_false_label: dict[Any, str] = {}
    event_id_to_po_successor_none_correction_flag_result: dict[int, bool] = {}

    for case_id, df_part in df_log.groupby("case:po_name"):
        run, event_ids_with_po_successors_none_to_correction_flag_part, invalid_label = \
            _process_case(case_id, df_part, name_to_transition, include_runs_with_invalid_transitions, event_id_to_successors, add_start_and_end_events)
        for event_id in event_ids_with_po_successors_none_to_correction_flag_part:
            event_id_to_po_successor_none_correction_flag_result[event_id] = event_ids_with_po_successors_none_to_correction_flag_part[event_id]
        if run:
            run_to_frequency[run] = int(df_part["case:multiplicity"].iloc[0])
        if invalid_label:
            invalid_run_to_false_label[case_id] = invalid_label

    return PartiallyOrderedEventLog(run_to_frequency), invalid_run_to_false_label, event_id_to_po_successor_none_correction_flag_result


def _process_case(case_id: Any,
                  df_part: pd.DataFrame,
                  name_to_transition: Dict[str, TransitionWorkflowNet],
                  include_invalid: bool,
                  event_id_to_successors: dict[int, list[int]] = None,
                  add_start_and_end_events=True) \
        -> tuple[None, None, Any] | tuple[Run, dict[Any, bool], Any | None]:
    """
    Processes a single case and constructs a run.

    :param case_id: Case ID.
    :param df_part: DataFrame containing the events for this case.
    :param name_to_transition: Mapping of transition names.
    :param include_invalid: Whether to include invalid transitions.
    :return: A tuple containing the Run object and any invalid label found.
    """
    event_id_to_event: Dict[int, EventForRun] = {}
    event_list: list[EventForRun] = []
    invalid_label = None

    # Process events and detect invalid transitions
    for _, row in df_part.iterrows():
        transition_name = row["concept:name"]
        if transition_name not in name_to_transition:
            invalid_label = transition_name
            if not include_invalid:
                return None, None, invalid_label
            transition_name = "INVALID"

        event = EventForRun(f"Event ID {row['identity:id']} from PO {case_id}", name_to_transition[transition_name])
        event_id_to_event[row["identity:id"]] = event
        event_list.append(event)

    # Build the event graph
    run, event_ids_with_po_none_to_correction_flag = \
        _construct_run_from_event_list(df_part, event_id_to_event, case_id, name_to_transition, event_id_to_successors, add_start_and_end_events)
    return run, event_ids_with_po_none_to_correction_flag, invalid_label


def _construct_run_from_event_list(df_part: DataFrame,
                                   event_id_to_event: Dict[int, EventForRun],
                                   key_partial_order,
                                   name_to_transition,
                                   event_id_to_successors: dict[int, list[int]] = None,
                                   add_start_and_end_events=True) \
        -> Tuple[Run, dict[Any, bool]]:
    event_list: List[EventForRun] = list(event_id_to_event.values())
    graph_for_po: DiGraph = DiGraph()
    graph_for_po.add_nodes_from(event_list)
    final_events: set[EventForRun] = set()
    event_to_number_predecessors = dict()
    event_ids_with_none_po_successor_to_correcting_flag = {}
    for event in event_list:
        event_to_number_predecessors[event] = 0
    for index, row in df_part.iterrows():
        current_event: EventForRun = event_id_to_event[row["identity:id"]]
        # due to the ugly format of the po_successors attribute we have to do a bit of work
        successors_from_data = row["po_successors"]
        successors_id_pair_list: list = [] if successors_from_data is None else successors_from_data["children"]
        if successors_from_data is None:
            if row["identity:id"] in event_id_to_successors:
                event_ids_with_none_po_successor_to_correcting_flag[row["identity:id"]] = True
                # transform to the indexed way successors are saved in the xes format
                successor_ids_from_input_parameter = event_id_to_successors[row["identity:id"]]
                successor_id_pair_list_from_input_parameter = [[i, successor_ids_from_input_parameter[i]] for i in
                                                               range(len(successor_ids_from_input_parameter))]
                successors_id_pair_list = successor_id_pair_list_from_input_parameter
            else:
                event_ids_with_none_po_successor_to_correcting_flag[row["identity:id"]] = False
        if not successors_id_pair_list:
            final_events.add(current_event)
            continue
        for index_successor_pair in successors_id_pair_list:
            successor_id: int = int(index_successor_pair[1])
            successor_event = event_id_to_event[successor_id]
            graph_for_po.add_edge(current_event, successor_event)
            event_to_number_predecessors[successor_event] += 1
    initial_events: set[EventForRun] = {event for event in event_to_number_predecessors.keys() if event_to_number_predecessors[event] == 0}
    # it remains to put the "start" and "end" events, which are not yet included, in the partial order
    if add_start_and_end_events:
        start_event: EventForRun = EventForRun("Start event of PO {}".format(key_partial_order), name_to_transition["START"])
        end_event: EventForRun = EventForRun("End event of PO {}".format(key_partial_order), name_to_transition["END"])
        graph_for_po.add_edges_from([(start_event, event_after_start) for event_after_start in initial_events])
        graph_for_po.add_edges_from([(before_end_event, end_event) for before_end_event in final_events])
    run: Run = Run(graph_for_po)
    run.name_foreign_source = str(key_partial_order)
    return run, event_ids_with_none_po_successor_to_correcting_flag


def _get_actual_successors_for_buggy_field(file_path: str, id: int) \
        -> List[List[int]]:
    """
    Dirty hotfix solution to handle situations where successors are read incorrectly from xes file
    due to unclear bug.
    DEPRECATED: this info is now injected directely; I just keep the function for the time being to make it into a unit test
    :param file_path:
    :param id:
    :return:
    """
    return_list: List[List[int]] = list()
    if file_path == "data/partially_ordered_logs/BPI12_olog_alpha_logwise_oneRperPoVar.xes" and id == 10110:
        return_list.append([0, 10111])
    elif file_path == "data/partially_ordered_logs/BPI12_olog_alpha_logwise_oneRperPoVar.xes" and id == 18541:
        return_list.append([0, 18542])
        return_list.append([1, 18543])
    elif file_path == "data/partially_ordered_logs/bpi2019_C_alpha_logwise_oneRperPoVar.xes" and id == 24913:
        # no successors so nothing to do
        return_list = list()
    elif file_path == "data/partially_ordered_logs/reviewing_alpha_logwise_oneRperPoVar.xes" and id == 650:
        return_list.append([0, 651])
    else:
        raise Exception("You forgot to implement following buggy situation: log: " + file_path + ", id: " + str(id) + ".")
    return return_list
