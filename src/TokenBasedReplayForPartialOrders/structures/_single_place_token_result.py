class SinglePlaceTokenResult:
    def __init__(self, produced_token: int = 0, consumed_token: int = 0, missing_token_min: int = 0,
                 missing_token_max: int = 0, remaining_token_min: int = 0, remaining_token_max: int = 0,
                 is_precise: bool = True):
        self.produced_token = produced_token
        self.consumed_token = consumed_token
        self.missing_token_min = missing_token_min
        self.remaining_token_min = remaining_token_min
        self.missing_token_max = missing_token_max
        self.remaining_token_max = remaining_token_max
        self.is_precise = is_precise

    def __str__(self):
        return "Result for place: p: %d, c: %d, m_min: %d, m_max: %d, r_min: %d, r_max: %d." % (self.produced_token, self.consumed_token,
                                                                                                self.missing_token_min, self.missing_token_max,
                                                                                                self.remaining_token_min, self.remaining_token_max)

    def mark_self_as_precise_as_upper_bounds_for_missing_and_remaining_tokens_are_correct(self):
        self.missing_token_min = self.missing_token_max
        self.remaining_token_min = self.remaining_token_max
        self.is_precise = True
