from src.TokenBasedReplayForPartialOrders.algorithms._conformance_measure_algorithm import calculate_token_replay_conformance_norm_for_partial_order
from src.TokenBasedReplayForPartialOrders.structures.partially_ordered_log_conformance_result import PartiallyOrderedLogConformanceResult
from src.TokenBasedReplayForPartialOrders.utils._pnml_file_importer import import_pnml_file_to_workflow_net
from src.TokenBasedReplayForPartialOrders.utils._xes_file_importer import import_cco_xes_file_to_event_log


def do_conformance_checking_for_partially_ordered_log(
        event_log_file_path: str,
        net_file_path: str,
        include_runs_with_invalid_labels: bool = True,
        only_use_heuristics: bool = False,
        add_initial_and_start_events: bool = False,
        event_id_to_missing_successors: dict[int, list[int]] = None
) -> PartiallyOrderedLogConformanceResult:
    """
    TODO
    Args:
        event_log_file_path: path to the xes file containing the partially ordered event log
        net_file_path: path to the pnml file containing the Workflow net
        include_runs_with_invalid_labels: if true, runs with invalid labels will be included and there labels ignored; otherwise these runs are
                completely ignored
        only_use_heuristics: if true only the heuristics will be used to calculate lower and upper bounds for the conformance measure in linear time;
                if false the precise values are calculated using a maximal flow algorithm, with worst case cubic time
        add_initial_and_start_events: if true start and end event will be included to all runs TODO really needed or should I decide baed on the net?
        event_id_to_missing_successors: allows to overcome the rare bug when reading the xes files with partial orders by manually providing for each
                wrongly read successor field the correct successors

    Returns:

    """
    net, label_to_transition = import_pnml_file_to_workflow_net(net_file_path)
    log, run_to_invalid_label, result_flags_for_correcting_missing_successors = import_cco_xes_file_to_event_log(event_log_file_path,
                                                                                                                 label_to_transition,
                                                                                                                 include_runs_with_invalid_labels,
                                                                                                                 event_id_to_missing_successors,
                                                                                                                 add_initial_and_start_events)
    result: PartiallyOrderedLogConformanceResult = calculate_token_replay_conformance_norm_for_partial_order(log,
                                                                                                             net,
                                                                                                             not only_use_heuristics,
                                                                                                             False,
                                                                                                             False,
                                                                                                             add_initial_and_start_events)
    result.run_id_to_event_id_to_po_successor_correction_flag = result_flags_for_correcting_missing_successors
    return result
