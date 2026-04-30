from src.TokenBasedReplayForPartialOrders.structures._run import Run


class PartiallyOrderedEventLog:
    def __init__(self, run_to_frequency: dict[Run, int]):
        self.run_to_frequency = run_to_frequency
