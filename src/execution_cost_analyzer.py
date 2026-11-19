
from statistics import mean


class ExecutionCostAnalyzer:
    VALID_AGGRESSORS = {"BUY", "SELL"}

    def __init__(self, trade_tape):
        self.trade_tape = trade_tape

    def collect_observations(self):
        observations = []

        for trade in self.trade_tape:
            if trade.aggressor not in self.VALID_AGGRESSORS:
                raise ValueError("Invalid aggressor")

            if trade.quantity <= 0:
                raise ValueError("Trade quantity must be positive")

            mid_price = trade.arrival_mid_price

            if mid_price is None:
                continue

            if mid_price <= 0:
                raise ValueError("Arrival mid-price must be positive")

            if trade.aggressor == "BUY":
                execution_cost = trade.price - mid_price
            else:
                execution_cost = mid_price - trade.price

            execution_cost_bps = (
                execution_cost / mid_price
            ) * 10_000

            observations.append({
                "timestamp": trade.timestamp,
                "price": trade.price,
                "quantity": trade.quantity,
                "aggressor": trade.aggressor,
                "arrival_mid_price": mid_price,
                "execution_cost": execution_cost,
                "execution_cost_bps": execution_cost_bps,
                "weighted_execution_cost": (
                    execution_cost * trade.quantity
                ),
                "weighted_execution_cost_bps": (
                    execution_cost_bps * trade.quantity
                ),
            })

        return observations

    def analyze(self):
        observations = self.collect_observations()

        if not observations:
            return {
                "total_trades": 0,
                "total_quantity": 0,
                "average_execution_cost": None,
                "average_execution_cost_bps": None,
                "quantity_weighted_execution_cost": None,
                "quantity_weighted_execution_cost_bps": None,
                "buy": self._summarize([]),
                "sell": self._summarize([]),
                "observations": [],
            }

        buy_trades = [
            obs for obs in observations
            if obs["aggressor"] == "BUY"
        ]

        sell_trades = [
            obs for obs in observations
            if obs["aggressor"] == "SELL"
        ]

        return {
            "total_trades": len(observations),
            "total_quantity": sum(
                obs["quantity"] for obs in observations
            ),
            "average_execution_cost": mean(
                obs["execution_cost"] for obs in observations
            ),
            "average_execution_cost_bps": mean(
                obs["execution_cost_bps"] for obs in observations
            ),
            "quantity_weighted_execution_cost": (
                sum(obs["weighted_execution_cost"] for obs in observations)
                / sum(obs["quantity"] for obs in observations)
            ),
            "quantity_weighted_execution_cost_bps": (
                sum(
                    obs["weighted_execution_cost_bps"]
                    for obs in observations
                )
                / sum(obs["quantity"] for obs in observations)
            ),
            "buy": self._summarize(buy_trades),
            "sell": self._summarize(sell_trades),
            "observations": observations,
        }

    @staticmethod
    def _summarize(trades):
        if not trades:
            return {
                "total_trades": 0,
                "total_quantity": 0,
                "average_execution_cost": None,
                "average_execution_cost_bps": None,
                "quantity_weighted_execution_cost": None,
                "quantity_weighted_execution_cost_bps": None,
            }

        total_quantity = sum(
            trade["quantity"] for trade in trades
        )

        return {
            "total_trades": len(trades),
            "total_quantity": total_quantity,
            "average_execution_cost": mean(
                trade["execution_cost"] for trade in trades
            ),
            "average_execution_cost_bps": mean(
                trade["execution_cost_bps"] for trade in trades
            ),
            "quantity_weighted_execution_cost": (
                sum(
                    trade["weighted_execution_cost"]
                    for trade in trades
                ) / total_quantity
            ),
            "quantity_weighted_execution_cost_bps": (
                sum(
                    trade["weighted_execution_cost_bps"]
                    for trade in trades
                ) / total_quantity
            ),
        }
