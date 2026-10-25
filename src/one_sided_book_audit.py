from src.market_data import OrderSide, OrderType
from src.simulation import Simulation


def run_audit(num_events=10_000, seed=42):
    simulation = Simulation(seed=seed)

    stats = {
        "both_present": [],
        "bid_empty": [],
        "ask_empty": [],
        "both_empty": [],
    }

    for _ in range(num_events):
        order = simulation.market.generate_order()

        previous_book = simulation.book.snapshot()

        bids = previous_book.bids
        asks = previous_book.asks

        if bids and asks:
            state = "both_present"
        elif not bids and asks:
            state = "bid_empty"
        elif bids and not asks:
            state = "ask_empty"
        else:
            state = "both_empty"

        tape_length_before = len(simulation.engine.trade_tape)

        simulation.engine.submit_order(order)

        new_trades = simulation.engine.trade_tape[tape_length_before:]

        executed_quantity = sum(
            trade.quantity
            for trade in new_trades
            if (
                (
                    order.side == OrderSide.BUY
                    and trade.buy_order_id == order.order_id
                )
                or
                (
                    order.side == OrderSide.SELL
                    and trade.sell_order_id == order.order_id
                )
            )
        )

        record = {
            "order_type": order.order_type,
            "side": order.side,
            "requested": order.quantity,
            "executed": executed_quantity,
            "expired": (
                order.order_type == OrderType.MARKET
                and executed_quantity < order.quantity
            ),
            "spread": (
                previous_book.best_ask - previous_book.best_bid
                if previous_book.best_bid is not None
                and previous_book.best_ask is not None
                else None
            ),
        }

        stats[state].append(record)

    print("=== ONE-SIDED / EMPTY BOOK AUDIT ===")

    print_summary(stats)


def print_summary(stats):
    total = sum(len(records) for records in stats.values())

    for state, records in stats.items():
        count = len(records)

        print(f"\n--- {format_state(state)} ---")
        print(f"events: {count}")
        print(f"percentage: {count / total:.2%}")

        if not records:
            continue

        spreads = [
            r["spread"]
            for r in records
            if r["spread"] is not None
        ]

        market_orders = [
            r
            for r in records
            if r["order_type"] == OrderType.MARKET
        ]

        market_buys = [
            r
            for r in market_orders
            if r["side"] == OrderSide.BUY
        ]

        market_sells = [
            r
            for r in market_orders
            if r["side"] == OrderSide.SELL
        ]

        expired = [
            r
            for r in market_orders
            if r["expired"]
        ]

        expired_buys = [
            r
            for r in expired
            if r["side"] == OrderSide.BUY
        ]

        expired_sells = [
            r
            for r in expired
            if r["side"] == OrderSide.SELL
        ]

        print(f"market orders: {len(market_orders)}")
        print(f"market BUY: {len(market_buys)}")
        print(f"market SELL: {len(market_sells)}")

        print(f"expired market orders: {len(expired)}")
        print(f"expired BUY: {len(expired_buys)}")
        print(f"expired SELL: {len(expired_sells)}")

        if spreads:
            print(
                f"avg spread: "
                f"{sum(spreads) / len(spreads):.5f}"
            )

        print(
            f"expiration rate among market orders: "
            f"{len(expired) / len(market_orders):.2%}"
            if market_orders
            else "expiration rate among market orders: N/A"
        )


def format_state(state):
    names = {
        "both_present": "BOTH SIDES PRESENT",
        "bid_empty": "BID EMPTY",
        "ask_empty": "ASK EMPTY",
        "both_empty": "BOTH SIDES EMPTY",
    }

    return names[state]


if __name__ == "__main__":
    run_audit()