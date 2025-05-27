from MasterThesisProject.source.structures.Run import Run
from MasterThesisProject.source.structures.RunConformanceResult import RunConformanceResult
from MasterThesisProject.source.structures.SinglePlaceTokenResult import SinglePlaceTokenResult


class TokenResultsWeightedSum:
    def __init__(self, produced_token: int = 0, consumed_token: int = 0, missing_token_min: int = 0, missing_token_max: int = 0,
                 remaining_token_min: int = 0, remaining_token_max: int = 0):
        self.produced_token = produced_token
        self.consumed_token = consumed_token
        self.missing_token_min = missing_token_min
        self.missing_token_max = missing_token_max
        self.remaining_token_min = remaining_token_min
        self.remaining_token_max = remaining_token_max

    def add_result_for_run(self, frequency_run: int, run_result: RunConformanceResult):
        self.produced_token += run_result.produced_token * frequency_run
        self.consumed_token += run_result.consumed_token * frequency_run
        self.missing_token_max += run_result.missing_token_max * frequency_run
        self.missing_token_min += run_result.missing_token_min * frequency_run
        self.remaining_token_max += run_result.remaining_token_max * frequency_run
        self.remaining_token_min += run_result.remaining_token_min * frequency_run


class PlaceStatistics:
    """
    Class is intended to be used in dictionary mapping a place to the information how often the place was decided in a specific
    log - net combination by the different methods. Additionally, information on produced/consumed/missing/remaining tokens is saved.
    """

    def __init__(self, forward_heuristic: int = 0, backward_heuristic: int = 0, maximal_flow: int = 0, produced_token: int = 0,
                 consumed_token: int = 0, missing_token_max: int = 0, missing_token_min: int = 0, remaining_token_min: int = 0,
                 remaining_token_max: int = 0):
        self.forward_heuristic = forward_heuristic
        self.backward_heuristic = backward_heuristic
        self.maximal_flow = maximal_flow

        self.produced_token = produced_token
        self.consumed_token = consumed_token
        self.missing_token_max = missing_token_max
        self.missing_token_min = missing_token_min
        self.remaining_token_max = remaining_token_max
        self.remaining_token_min = remaining_token_min

    def add_single_place_result(self, result: SinglePlaceTokenResult):
        self.produced_token += result.produced_token
        self.consumed_token += result.consumed_token
        self.missing_token_max += result.missing_token_max
        self.missing_token_min += result.missing_token_min
        self.remaining_token_max += result.remaining_token_max
        self.remaining_token_min += result.remaining_token_min


class PartiallyOrderedLogConformanceResult:
    def __init__(self, is_precise_result: bool = False, lower_bound_conformance: float = 0, upper_bound_conformance: float = 1,
                 conformance_level: float = 0.5, run_to_conformance_result: dict[Run, RunConformanceResult] = None,
                 place_to_decision_statistic: dict[str, PlaceStatistics] = None):
        if run_to_conformance_result is None:
            run_to_conformance_result = dict()
        self.is_precise_result = is_precise_result
        self.lower_bound_conformance = lower_bound_conformance
        self.upper_bound_conformance = upper_bound_conformance
        self.conformance_level = conformance_level
        self.run_to_conformance_result = run_to_conformance_result

        self.number_places_decided_forward_heuristic = 0
        self.number_places_decided_backward_heuristic = 0
        self.number_places_decided_flow_network = 0
        # When we did only apply the linear heuristics, some places might only have bounds for the missing/remaining tokens.
        self.number_places_only_estimated = 0
        # Following map keeps the place specific methods used.
        self.place_to_decision_statistic = dict() if place_to_decision_statistic is None else place_to_decision_statistic

        self.missing_tokens_max = 0
        self.missing_tokens_min = 0
        self.consumed_tokens = 0
        self.remaining_tokens_max = 0
        self.remaining_tokens_min = 0
        self.produced_tokens = 0

    def fill_from_calculation_result(self, weighted_sums: TokenResultsWeightedSum, run_to_conformance_result: dict[Run, RunConformanceResult]):
        def calculate_conformance_level(produced: int, consumed: int, missing: int, remaining: int) -> float:
            first_term: float = 1 - (missing / consumed)
            second_term: float = 1 - (remaining / produced)
            return (first_term + second_term) / 2

        self.run_to_conformance_result = run_to_conformance_result
        self.lower_bound_conformance = calculate_conformance_level(
            weighted_sums.produced_token, weighted_sums.consumed_token, weighted_sums.missing_token_max, weighted_sums.remaining_token_max)
        self.upper_bound_conformance = calculate_conformance_level(
            weighted_sums.produced_token, weighted_sums.consumed_token, weighted_sums.missing_token_min, weighted_sums.remaining_token_min
        )
        self.conformance_level = (self.lower_bound_conformance + self.upper_bound_conformance) / 2
        self.is_precise_result = (self.lower_bound_conformance == self.upper_bound_conformance)
        # Just to be sure we reset the statistics how places where decided (should not be relevant in my code but
        # it is always good to guarantee consistency
        self.number_places_decided_forward_heuristic = 0
        self.number_places_decided_backward_heuristic = 0
        self.number_places_decided_flow_network = 0
        self.number_places_only_estimated = 0
        self.missing_tokens_max = 0
        self.missing_tokens_min = 0
        self.consumed_tokens = 0
        self.remaining_tokens_max = 0
        self.remaining_tokens_min = 0
        self.produced_tokens = 0
        for run_result in run_to_conformance_result.values():
            self.number_places_decided_forward_heuristic += run_result.number_places_decided_forward_heuristic
            self.number_places_decided_backward_heuristic += run_result.number_places_decided_backward_heuristic
            self.number_places_decided_flow_network += run_result.number_places_decided_flow_network
            self.number_places_only_estimated += run_result.number_places_only_estimated
            self.missing_tokens_max += run_result.missing_token_max
            self.missing_tokens_min += run_result.missing_token_min
            self.consumed_tokens += run_result.consumed_token
            self.remaining_tokens_max += run_result.remaining_token_max
            self.remaining_tokens_min += run_result.remaining_token_min
            self.produced_tokens += run_result.produced_token
