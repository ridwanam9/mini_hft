class OrderBookStateMatchingAnalyzer:
    """
    Groups execution observations by their arrival order book state.
    """

    POLICIES = ("none", "random", "distance")

    @staticmethod
    def classify_spread(spread):
        if spread <= 0.03:
            return "LOW"
        elif spread <= 0.06:
            return "MEDIUM"
        elif spread <= 0.18:
            return "HIGH"
        return None

    @staticmethod
    def classify_depth(depth):
        if depth <= 110:
            return "LOW"
        elif depth <= 410:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def classify_obi(obi):
        if obi < -0.4:
            return "NEGATIVE"
        elif obi <= 0.4:
            return "BALANCED"
        return "POSITIVE"

    @classmethod
    def classify_observation(cls, observation):
        """
        Returns a tuple representing the observation's order book state.
        Returns None if the observation is outside the supported range.
        """

        spread_bin = cls.classify_spread(observation["spread"])

        if spread_bin is None:
            return None

        bid_depth_bin = cls.classify_depth(
            observation["bid_depth"]
        )

        ask_depth_bin = cls.classify_depth(
            observation["ask_depth"]
        )

        obi_bin = cls.classify_obi(observation["obi"])

        aggressor = observation["aggressor"]

        if aggressor not in ("BUY", "SELL"):
            raise ValueError(
                f"Invalid aggressor: {aggressor}"
            )

        return (
            spread_bin,
            bid_depth_bin,
            ask_depth_bin,
            obi_bin,
            aggressor,
        )
