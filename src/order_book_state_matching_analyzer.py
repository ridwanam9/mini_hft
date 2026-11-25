from collections import defaultdict

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

    
    @classmethod
    def analyze(cls, observations):
        """
        Aggregate execution cost by order book state and policy.
        """

        grouped = defaultdict(
            lambda: {
                policy: {
                    "trade_count": 0,
                    "total_quantity": 0,
                    "total_cost_bps": 0.0,
                    "quantity_weighted_cost_bps": 0.0,
                }
                for policy in cls.POLICIES
            }
        )

        excluded_count = 0

        for observation in observations:
            policy = observation["policy"]

            if policy not in cls.POLICIES:
                raise ValueError(
                    f"Invalid policy: {policy}"
                )

            state = cls.classify_observation(observation)

            if state is None:
                excluded_count += 1
                continue

            metrics = grouped[state][policy]

            quantity = observation["quantity"]
            cost_bps = observation["execution_cost_bps"]

            metrics["trade_count"] += 1
            metrics["total_quantity"] += quantity
            metrics["total_cost_bps"] += cost_bps
            metrics["quantity_weighted_cost_bps"] += (
                cost_bps * quantity
            )

        # Calculate average metrics for each state and policy.
        results = {}

        for state, policies in grouped.items():
            results[state] = {}

            for policy, metrics in policies.items():
                trade_count = metrics["trade_count"]
                total_quantity = metrics["total_quantity"]

                average_cost_bps = (
                    metrics["total_cost_bps"] / trade_count
                    if trade_count > 0
                    else None
                )

                quantity_weighted_cost_bps = (
                    metrics["quantity_weighted_cost_bps"]
                    / total_quantity
                    if total_quantity > 0
                    else None
                )

                results[state][policy] = {
                    "trade_count": trade_count,
                    "total_quantity": total_quantity,
                    "average_cost_bps": average_cost_bps,
                    "quantity_weighted_cost_bps": (
                        quantity_weighted_cost_bps
                    ),
                }

        return {
            "groups": results,
            "excluded_count": excluded_count,
            "total_observations": len(observations),
        }
    
    @classmethod
    def find_common_states(cls, analysis_result):
        """
        Find states with observations from every policy.
        """

        common_states = []

        for state, policies in analysis_result["groups"].items():
            has_all_policies = all(
                policies[policy]["trade_count"] > 0
                for policy in cls.POLICIES
            )

            if has_all_policies:
                common_states.append(state)

        return common_states

    @classmethod
    def compare_common_states(cls, analysis_result):
        """
        Compare execution costs across policies
        using only common order book states.
        """
        common_states = cls.find_common_states(analysis_result)

        comparisons = []

        for state in common_states:
            policies = analysis_result["groups"][state]

            comparisons.append({
                "state": state,
                "policies": {
                    policy: policies[policy]
                    for policy in cls.POLICIES
                },
            })

        return comparisons
