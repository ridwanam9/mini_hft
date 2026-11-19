
from collections import defaultdict


class OrderBookStateAnalyzer:
    def __init__(self, trade_tape):
        self.trade_tape = trade_tape

    @staticmethod
    def classify(trade):
        bid = trade.arrival_best_bid
        ask = trade.arrival_best_ask

        if bid is not None and ask is not None:
            return "TWO_SIDED"

        if bid is None and ask is not None:
            return "ASK_ONLY"

        if bid is not None and ask is None:
            return "BID_ONLY"

        return "EMPTY"

    def analyze(self):
        summary = defaultdict(
            lambda: {
                "trade_count": 0,
                "total_quantity": 0,
                "buy_count": 0,
                "sell_count": 0,
                "buy_quantity": 0,
                "sell_quantity": 0,
            }
        )

        for trade in self.trade_tape:
            state = self.classify(trade)
            data = summary[state]

            data["trade_count"] += 1
            data["total_quantity"] += trade.quantity

            if trade.aggressor == "BUY":
                data["buy_count"] += 1
                data["buy_quantity"] += trade.quantity

            elif trade.aggressor == "SELL":
                data["sell_count"] += 1
                data["sell_quantity"] += trade.quantity

            else:
                raise ValueError("Invalid aggressor")

        categories = [
            "TWO_SIDED",
            "ASK_ONLY",
            "BID_ONLY",
            "EMPTY",
        ]

        result = {}

        for category in categories:
            result[category] = summary[category]

        # Calculate totals before adding them to result.
        total_trades = sum(
            result[category]["trade_count"]
            for category in categories
        )

        total_quantity = sum(
            result[category]["total_quantity"]
            for category in categories
        )

        result["total_trades"] = total_trades
        result["total_quantity"] = total_quantity

        return result
