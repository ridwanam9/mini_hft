
from collections import defaultdict


class SpreadCostAnalyzer:
    """
    Decomposes aggressive execution cost into:
    - half-spread cost
    - beyond-touch cost

    Only TWO_SIDED trades with complete arrival data are analyzed.
    """

    def __init__(self, trade_tape):
        self.trade_tape = trade_tape

    @staticmethod
    def _empty_metrics():
        return {
            "trade_count": 0,
            "total_quantity": 0,
            "total_cost": 0.0,
            "total_half_spread_cost": 0.0,
            "total_beyond_touch_cost": 0.0,
            "total_cost_bps": 0.0,
            "total_half_spread_bps": 0.0,
            "total_beyond_touch_bps": 0.0,
            "quantity_weighted_cost": 0.0,
            "quantity_weighted_half_spread_cost": 0.0,
            "quantity_weighted_beyond_touch_cost": 0.0,
            "quantity_weighted_cost_bps": 0.0,
            "quantity_weighted_half_spread_bps": 0.0,
            "quantity_weighted_beyond_touch_bps": 0.0,
        }

    @staticmethod
    def _add_trade(metrics, trade):
        bid = trade.arrival_best_bid
        ask = trade.arrival_best_ask
        mid = trade.arrival_mid_price

        if (
            bid is None
            or ask is None
            or mid is None
            or trade.quantity <= 0
        ):
            return False

        if bid <= 0 or ask <= 0 or mid <= 0 or ask < bid:
            raise ValueError("Invalid arrival order book prices")

        if trade.aggressor == "BUY":
            total_cost = trade.price - mid
            beyond_touch_cost = trade.price - ask
        elif trade.aggressor == "SELL":
            total_cost = mid - trade.price
            beyond_touch_cost = bid - trade.price
        else:
            raise ValueError("Invalid aggressor")

        half_spread_cost = (ask - bid) / 2

        total_bps = total_cost / mid * 10_000
        half_spread_bps = half_spread_cost / mid * 10_000
        beyond_touch_bps = beyond_touch_cost / mid * 10_000

        # Keep the decomposition internally consistent.
        if abs(total_cost - (half_spread_cost + beyond_touch_cost)) > 1e-9:
            raise AssertionError("Execution cost decomposition mismatch")

        quantity = trade.quantity

        metrics["trade_count"] += 1
        metrics["total_quantity"] += quantity

        metrics["total_cost"] += total_cost
        metrics["total_half_spread_cost"] += half_spread_cost
        metrics["total_beyond_touch_cost"] += beyond_touch_cost

        metrics["total_cost_bps"] += total_bps
        metrics["total_half_spread_bps"] += half_spread_bps
        metrics["total_beyond_touch_bps"] += beyond_touch_bps

        metrics["quantity_weighted_cost"] += total_cost * quantity
        metrics["quantity_weighted_half_spread_cost"] += (
            half_spread_cost * quantity
        )
        metrics["quantity_weighted_beyond_touch_cost"] += (
            beyond_touch_cost * quantity
        )

        metrics["quantity_weighted_cost_bps"] += total_bps * quantity
        metrics["quantity_weighted_half_spread_bps"] += (
            half_spread_bps * quantity
        )
        metrics["quantity_weighted_beyond_touch_bps"] += (
            beyond_touch_bps * quantity
        )

        return True

    @classmethod
    def _finalize(cls, metrics):
        count = metrics["trade_count"]
        quantity = metrics["total_quantity"]

        if count == 0 or quantity == 0:
            return metrics

        for key in (
            "total_cost",
            "total_half_spread_cost",
            "total_beyond_touch_cost",
            "total_cost_bps",
            "total_half_spread_bps",
            "total_beyond_touch_bps",
        ):
            metrics[f"average_{key}"] = metrics[key] / count

        for key in (
            "quantity_weighted_cost",
            "quantity_weighted_half_spread_cost",
            "quantity_weighted_beyond_touch_cost",
            "quantity_weighted_cost_bps",
            "quantity_weighted_half_spread_bps",
            "quantity_weighted_beyond_touch_bps",
        ):
            metrics[key] /= quantity

        return metrics

    def analyze(self):
        overall = self._empty_metrics()
        by_aggressor = defaultdict(self._empty_metrics)

        skipped_count = 0

        for trade in self.trade_tape:
            # This analyzer requires a two-sided arrival book.
            if (
                trade.arrival_best_bid is None
                or trade.arrival_best_ask is None
                or trade.arrival_mid_price is None
            ):
                skipped_count += 1
                continue

            self._add_trade(overall, trade)
            self._add_trade(by_aggressor[trade.aggressor], trade)

        self._finalize(overall)

        finalized_by_aggressor = {}
        for aggressor, metrics in by_aggressor.items():
            finalized_by_aggressor[aggressor] = self._finalize(metrics)

        return {
            "overall": overall,
            "by_aggressor": finalized_by_aggressor,
            "skipped_count": skipped_count,
        }
