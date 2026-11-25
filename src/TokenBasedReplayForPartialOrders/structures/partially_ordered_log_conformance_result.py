from enum import Enum
import math
import csv
import os
import xml.etree.ElementTree as ET

from src.TokenBasedReplayForPartialOrders.structures._run import Run
from src.TokenBasedReplayForPartialOrders.structures._run_conformance_result import RunConformanceResult
from src.TokenBasedReplayForPartialOrders.structures._single_place_token_result import SinglePlaceTokenResult


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


class RunWithConformanceResult:

    def __init__(self, run: Run, conformance_result: RunConformanceResult):
        self.run = run
        self.conformance_result = conformance_result


class LevelType(Enum):
    LOWER_BOUND = -1
    MIDDLE = 0
    UPPER_BOUND = 1

class PersistationType(Enum):
    CSV = "csv"
    XML = "xml"

# Columns of the CSV file, in this order.
PERSISTATION_CSV_COLUMNS = [
    "ID", "Total result",
    "Minimum fitness value", "Average fitness values", "Maximum fitness value",
    "Produced tokens", "Consumed tokens",
    "Missing tokens (max)", "Missing tokens (min)",
    "Remaining tokens (max)", "Remaining tokens (min)",
    "Places decided with forward heuristic",
    "Places decided with backward heuristic",
    "Places decided with other method",
]

# XML element names for all columns except "ID" and "Total result" (those are an attribute / the element type).
PERSISTATION_XML_TAGS = {
    "Minimum fitness value": "minimumFitnessValue",
    "Average fitness values": "averageFitnessValue",
    "Maximum fitness value": "maximumFitnessValue",
    "Produced tokens": "producedTokens",
    "Consumed tokens": "consumedTokens",
    "Missing tokens (max)": "missingTokensMax",
    "Missing tokens (min)": "missingTokensMin",
    "Remaining tokens (max)": "remainingTokensMax",
    "Remaining tokens (min)": "remainingTokensMin",
    "Places decided with forward heuristic": "placesDecidedForwardHeuristic",
    "Places decided with backward heuristic": "placesDecidedBackwardHeuristic",
    "Places decided with other method": "placesDecidedOtherMethod",
}

class PartiallyOrderedLogConformanceResult:
    def __init__(self, is_precise_result: bool = False,
                 lower_bound_conformance: float = 0,
                 upper_bound_conformance: float = 1,
                 conformance_level: float = 0.5,
                 run_to_conformance_result: dict[Run, RunConformanceResult] = None,
                 place_to_decision_statistic: dict[str, PlaceStatistics] = None,
                 run_id_to_event_id_to_po_successor_correction_flag: dict[int, bool] = None):
        # TODO fix type hint above
        if run_to_conformance_result is None:
            run_to_conformance_result = dict()
        self.is_precise_result = is_precise_result
        self.lower_bound_conformance = lower_bound_conformance
        self.upper_bound_conformance = upper_bound_conformance
        self.conformance_level = conformance_level
        self.run_to_conformance_result = run_to_conformance_result
        self.run_id_to_event_id_to_po_successor_correction_flag = {} if run_id_to_event_id_to_po_successor_correction_flag is None \
            else run_id_to_event_id_to_po_successor_correction_flag

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
        # Just to be sure we reset the statistics how places where decided (should not be relevant in my code, but
        # it is always good to guarantee consistency)
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

    def find_runs_with_worst_conformance_values(self, number_runs: int, level_type_for_sorting: LevelType) -> list[RunWithConformanceResult]:
        if (level_type_for_sorting is None) or (not isinstance(level_type_for_sorting, LevelType)):
            raise ValueError("Need to specify which conformance level shall be used with valid LevelType argument.")
        if (number_runs is None) or (not isinstance(number_runs, int)) or (number_runs < 0):
            raise ValueError("Need to specify how many runs you want to see with a valid non-negative integer.")
        if number_runs == 0:
            return []

        def get_relevant_level(result: RunConformanceResult) -> float:
            if level_type_for_sorting is LevelType.LOWER_BOUND:
                return result.conformance_level_min
            elif level_type_for_sorting is LevelType.UPPER_BOUND:
                return result.conformance_level_max
            elif level_type_for_sorting is LevelType.MIDDLE:
                return (result.conformance_level_max + result.conformance_level_min) / 2
            else:
                raise NotImplementedError("Implementation missing for level type " + level_type_for_sorting.name)

        values_with_conformance_level_less_than_one = self._find_all_non_conforming_runs_with_conformance_result()
        values_with_conformance_level_less_than_one.sort(key=lambda rwcr: get_relevant_level(rwcr.conformance_result))
        return values_with_conformance_level_less_than_one[0:number_runs]

    def get_number_of_non_conforming_runs(self):
        values_with_conformance_level_less_tan_one = self._find_all_non_conforming_runs_with_conformance_result()
        return len(values_with_conformance_level_less_tan_one)

    def get_number_of_runs_in_log(self):
        return len(self.run_to_conformance_result)

    def _find_all_non_conforming_runs_with_conformance_result(self):
        def get_run_conformance_value(result: RunConformanceResult) -> float:
            return (result.conformance_level_max + result.conformance_level_min) / 2

        all_runs_with_conformance_result: list[RunWithConformanceResult] \
            = [RunWithConformanceResult(r, self.run_to_conformance_result[r]) for r in self.run_to_conformance_result]
        values_with_conformance_level_less_than_one = list(filter(lambda rwcr: not math.isclose(get_run_conformance_value(rwcr.conformance_result), 1),
                                                                  all_runs_with_conformance_result))
        return values_with_conformance_level_less_than_one

    def persist_result(self, path: str, persistation_type: "PersistationType") -> None:
        """
        Save the total result and the result of every run to a file.

        CSV: one line for the total result (ID "Total", column "Total result" = True) followed by one line
             per run (ID = name of the foreign source, "Total result" = False).
        XML: a root element with the total result and, nested below it, the results of all runs.

        Missing parent folders are created, an existing file is overwritten.
        """
        if (path is None) or (not isinstance(path, str)) or (path.strip() == ""):
            raise ValueError("Need to specify the path of the file with a non-empty string.")
        if (persistation_type is None) or (not isinstance(persistation_type, PersistationType)):
            raise ValueError("Need to specify how to persist the result with a valid PersistationType argument.")

        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        rows = self._rows_for_persistation()
        if persistation_type is PersistationType.CSV:
            self._write_csv(path, rows)
        elif persistation_type is PersistationType.XML:
            self._write_xml(path, rows)
        else:
            raise NotImplementedError("Implementation missing for persistation type " + persistation_type.name)

    def _rows_for_persistation(self) -> list:
        """List of (id, is_total_result, {column name: value}); the first entry is the total result."""
        rows = [("Total", True, {
            "Minimum fitness value": self.lower_bound_conformance,
            "Average fitness values": self.conformance_level,
            "Maximum fitness value": self.upper_bound_conformance,
            "Produced tokens": self.produced_tokens,
            "Consumed tokens": self.consumed_tokens,
            "Missing tokens (max)": self.missing_tokens_max,
            "Missing tokens (min)": self.missing_tokens_min,
            "Remaining tokens (max)": self.remaining_tokens_max,
            "Remaining tokens (min)": self.remaining_tokens_min,
            "Places decided with forward heuristic": self.number_places_decided_forward_heuristic,
            "Places decided with backward heuristic": self.number_places_decided_backward_heuristic,
            # Places not decided by the heuristics are decided by the flow network or, if only the heuristics
            # were used, they are only estimated. The result does not know which case it is, so take the maximum.
            "Places decided with other method": max(self.number_places_only_estimated,
                                                    self.number_places_decided_flow_network),
        })]
        for run, run_result in self.run_to_conformance_result.items():
            rows.append((run.name_foreign_source, False, {
                "Minimum fitness value": run_result.conformance_level_min,
                "Average fitness values": (run_result.conformance_level_min + run_result.conformance_level_max) / 2,
                "Maximum fitness value": run_result.conformance_level_max,
                "Produced tokens": run_result.produced_token,
                "Consumed tokens": run_result.consumed_token,
                "Missing tokens (max)": run_result.missing_token_max,
                "Missing tokens (min)": run_result.missing_token_min,
                "Remaining tokens (max)": run_result.remaining_token_max,
                "Remaining tokens (min)": run_result.remaining_token_min,
                "Places decided with forward heuristic": run_result.number_places_decided_forward_heuristic,
                "Places decided with backward heuristic": run_result.number_places_decided_backward_heuristic,
                "Places decided with other method": max(run_result.number_places_only_estimated,
                                                        run_result.number_places_decided_flow_network),
            }))
        return rows

    @staticmethod
    def _write_csv(path: str, rows: list) -> None:
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(PERSISTATION_CSV_COLUMNS)
            for identifier, is_total_result, values in rows:
                writer.writerow([identifier, is_total_result]
                                + [values[column] for column in PERSISTATION_CSV_COLUMNS[2:]])

    def _write_xml(self, path: str, rows: list) -> None:
        def fill(element: ET.Element, values: dict) -> None:
            for column, tag in PERSISTATION_XML_TAGS.items():
                ET.SubElement(element, tag).text = str(values[column])

        root = ET.Element("PartiallyOrderedLogConformanceResult")
        _, _, total_values = rows[0]
        total_element = ET.SubElement(root, "TotalResult", {"isPreciseResult": str(self.is_precise_result).lower()})
        fill(total_element, total_values)
        runs_element = ET.SubElement(total_element, "RunResults")
        for identifier, _, values in rows[1:]:
            fill(ET.SubElement(runs_element, "RunResult", {"id": str(identifier)}), values)

        ET.indent(root)  # pretty printing, needs Python 3.9+
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
