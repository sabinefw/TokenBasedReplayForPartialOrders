import unittest

from src.TokenBasedReplayForPartialOrders.user_interface import do_conformance_checking_for_partially_ordered_log
from src.TokenBasedReplayForPartialOrders.structures.partially_ordered_log_conformance_result import PartiallyOrderedLogConformanceResult


class TestUserInterface(unittest.TestCase):

    def test_conformance_checking_function_for_reviewing_log(self):
        result_reviewing_lf_precise: PartiallyOrderedLogConformanceResult = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/reviewing_alpha_logwise_oneRperPoVar.xes", "test_ressources/reviewing_5.pnml")
        self.verify_test_case_result(result_reviewing_lf_precise, True, 0.9816715542521994, 0.9816715542521994,
                                     0.9816715542521994)
        result_reviewing_lf_heuristic_only: PartiallyOrderedLogConformanceResult = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/reviewing_alpha_logwise_oneRperPoVar.xes", "test_ressources/reviewing_5.pnml",
            only_use_heuristics=True
        )
        # for reviewing we can decide by checking if there were any tokens at a "crossroad" that could co wrongly
        self.verify_test_case_result(result_reviewing_lf_heuristic_only, True, 0.9816715542521994,0.9816715542521994,
                                     0.9816715542521994)

        result_reviewing_hf_precise: PartiallyOrderedLogConformanceResult = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/reviewing_alpha_logwise_oneRperPoVar.xes", "test_ressources/reviewing_10.pnml"
        )
        self.verify_test_case_result(result_reviewing_hf_precise, True, 1, 1,
                                     1)
        result_reviewing_hf_heuristic_only: PartiallyOrderedLogConformanceResult = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/reviewing_alpha_logwise_oneRperPoVar.xes", "test_ressources/reviewing_10.pnml",
            only_use_heuristics=True
        )
        self.verify_test_case_result(result_reviewing_hf_heuristic_only, True, 1, 1, 1)

    def verify_test_case_result(self,
                                result_reviewing_heuristic_only: PartiallyOrderedLogConformanceResult,
                                is_precise_result: bool,
                                lower_bound: float,
                                upper_bound: float,
                                conformance_value: float):
        self.assertEqual(is_precise_result, result_reviewing_heuristic_only.is_precise_result, "Is result precise?")
        self.assertEqual(lower_bound, result_reviewing_heuristic_only.lower_bound_conformance, "Lower bound")
        self.assertEqual(upper_bound, result_reviewing_heuristic_only.upper_bound_conformance, "Upper bound")
        self.assertEquals(conformance_value, result_reviewing_heuristic_only.conformance_level, "Conformance value")

    def test_conformance_checking_function_for_bpi12_o_log(self):
        result_lf_precise = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/BPI12_olog_alpha_logwise_oneRperPoVar.xes", "test_ressources/bpi2012_olog_5.pnml"
        )
        self.verify_test_case_result(result_lf_precise, True, 0.9266383801965397, 0.9266383801965397, 0.9266383801965397)
        result_lf_heuristic_only = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/BPI12_olog_alpha_logwise_oneRperPoVar.xes", "test_ressources/bpi2012_olog_5.pnml",
            only_use_heuristics=True
        )
        self.verify_test_case_result(result_lf_heuristic_only, False, 0.9266383801965397, 0.9298480884648361,
                                     0.9282432343306879)
        result_hf_precise = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/BPI12_olog_alpha_logwise_oneRperPoVar.xes", "test_ressources/bpi2012_olog_10.pnml"
        )
        self.verify_test_case_result(result_hf_precise, True, 1, 1, 1)
        result_hf_heuristic_onliy = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/BPI12_olog_alpha_logwise_oneRperPoVar.xes", "test_ressources/bpi2012_olog_10.pnml",
            only_use_heuristics=True
        )
        self.verify_test_case_result(result_hf_heuristic_onliy, False, 0.9950101356619367, 1,
                                     0.9975050678309684)

    def test_conformance_checking_function_for_bpi19_c_log(self):
        result_lf_precise = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/bpi2019_C_alpha_logwise_oneRperPoVar.xes", "test_ressources/bpi2019c_5.pnml"
        )
        self.verify_test_case_result(result_lf_precise, True, 0.9588160814692789, 0.9588160814692789,
                                     0.9588160814692789)
        result_lf_heuristic_only = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/bpi2019_C_alpha_logwise_oneRperPoVar.xes", "test_ressources/bpi2019c_5.pnml",
            only_use_heuristics=True
        )
        self.verify_test_case_result(result_lf_heuristic_only, True, 0.9588160814692789, 0.9588160814692789,
                                     0.9588160814692789)
        result_hf_precise = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/bpi2019_C_alpha_logwise_oneRperPoVar.xes", "test_ressources/bpi2019c_10.pnml"
        )
        self.verify_test_case_result(result_hf_precise, True, 0.9749138994004847, 0.9749138994004847,
                                     0.9749138994004847)
        result_hf_heuristic_only = do_conformance_checking_for_partially_ordered_log(
            "test_ressources/bpi2019_C_alpha_logwise_oneRperPoVar.xes", "test_ressources/bpi2019c_10.pnml",
            only_use_heuristics=True
        )
        self.verify_test_case_result(result_hf_heuristic_only, False, 0.9749138994004847, 1,
                                     0.9874569497002423)


if __name__ == '__main__':
    unittest.main()
