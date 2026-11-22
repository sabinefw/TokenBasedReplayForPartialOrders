import unittest


from pm4py.objects.petri_net.importer import importer as pnml_importer
from pathlib import Path

from src.TokenBasedReplayForPartialOrders.utils._pnml_file_importer import import_pnml_file_to_workflow_net
from src.TokenBasedReplayForPartialOrders.utils._xes_file_importer import import_cco_xes_file_to_event_log, import_xes_file_totally_ordered_log


class ImportTester(unittest.TestCase):
    def test_basic_imports(self):
        """
        Try to import the net from the file in the sibling folder
        :return:
        """
        # first check po example
        net, name_to_transition = import_pnml_file_to_workflow_net("ressources/8.pnml")
        log_po, invalid_run_to_invalid_label, event_id_with_wrong_successor_import_to_correction_success_flag\
            = import_cco_xes_file_to_event_log("ressources/Repair_alpha_logwise_oneRperPoVar.xes", name_to_transition)
        # now to example
        net_review, name_to_transition_review = import_pnml_file_to_workflow_net("ressources/reviewing_5.pnml")
        log_to_with_invalid, invalid_traces_with = import_xes_file_totally_ordered_log("ressources/reviewing_complete_only.xes", name_to_transition_review, True)
        log_to_without_invalid, invaid_traces_without = import_xes_file_totally_ordered_log("ressources/reviewing_complete_only.xes", name_to_transition_review, False)

        # also compared with classic import
        net, initial_marking, final_marking = pnml_importer.apply("ressources/reviewing_5.pnml")
        # TODO so far I only had a look to verify it; looks good but should write proper unit test
        self.assertEqual(True, True)  # add assertion here


    def test_import_of_bpi_a_log(self):
        current_dir = Path(__file__).resolve().parent
        file_path_net = current_dir.parent / "test_ressources" / "bpi2012_alog_5.pnml"
        file_path_log = current_dir.parent / "test_ressources" / "BPI12_alog_alpha_logwise_oneRperPoVar.xes"
        net, name_to_transistion = import_pnml_file_to_workflow_net(str(file_path_net))
        log, invalid_runs, buggy_runs_with_success_flag = import_cco_xes_file_to_event_log(str(file_path_log), name_to_transistion)

    def test_import_roadtraffic(self):
        net, name_to_transition = import_pnml_file_to_workflow_net("ressources/roadtraffic_5.pnml")

    def test_fix_for_buggy_import_situations(self):
        # first test case: olog log
        current_dir = Path(__file__).resolve().parent
        file_path_net = current_dir.parent / "test_ressources" / "bpi12_o_unc.pnml"
        file_path_log = current_dir.parent / "test_ressources" / "BPI12_olog_alpha_logwise_oneRperPoVar.xes"
        net, name_to_transition = import_pnml_file_to_workflow_net(str(file_path_net))
        bug_fix_dictionary_for_bpi112_o: dict[int, list] = {10110: [10111], 18541: [18542, 18543]}
        log, invalid_runs, buggy_runs_with_success_flag = import_cco_xes_file_to_event_log(str(file_path_log), name_to_transition)
        buggy_event_to_constructed_neighbors = {}
        for run in log.run_to_frequency.keys():
            for run_event in run.partial_order.nodes:
                if run_event.foreign_id in bug_fix_dictionary_for_bpi112_o.keys():
                    buggy_event_to_constructed_neighbors[run_event.foreign_id] = list(run.partial_order.neighbors(run_event))
        self.assertTrue(buggy_event_to_constructed_neighbors.keys().__contains__(10110))
        neighbors_first_buggy_event = buggy_event_to_constructed_neighbors[10110]
        neighbor_ids_first_buggy_event = [neighbor.foreign_id for neighbor in neighbors_first_buggy_event]
        self.assertEqual([10111], neighbor_ids_first_buggy_event)
        self.assertTrue(buggy_event_to_constructed_neighbors.keys().__contains__(18541))
        neighbor_ids_second_buggy_event = [neighbor.foreign_id for neighbor in buggy_event_to_constructed_neighbors[18541]]
        self.assertEqual([18542, 18543], neighbor_ids_second_buggy_event)

        # second test case: reviewing alpha logwise
        current_dir = Path(__file__).resolve().parent
        file_path_net = current_dir.parent / "test_ressources" / "reviewing_5.pnml"
        file_path_log = current_dir.parent / "test_ressources" / "reviewing_alpha_logwise_oneRperPoVar.xes"
        net, name_to_transition = import_pnml_file_to_workflow_net(str(file_path_net))
        bug_fix_dictionary_for_reviewing: dict[int, list] = {650: [651]}
        log, invalid_runs, buggy_runs_with_success_flag = import_cco_xes_file_to_event_log(str(file_path_log), name_to_transition)
        buggy_event_to_constructed_neighbors = {}
        for run in log.run_to_frequency.keys():
            for run_event in run.partial_order.nodes:
                if run_event.foreign_id in bug_fix_dictionary_for_reviewing.keys():
                    buggy_event_to_constructed_neighbors[run_event.foreign_id] = list(run.partial_order.neighbors(run_event))
        self.assertTrue(buggy_event_to_constructed_neighbors.keys().__contains__(650))
        neighbors_only_buggy_event = buggy_event_to_constructed_neighbors[650]
        neighbor_ids_only_buggy_event = [neighbor.foreign_id for neighbor in neighbors_only_buggy_event]
        self.assertEqual([651], neighbor_ids_only_buggy_event)

if __name__ == '__main__':
    unittest.main()
