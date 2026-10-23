from collections import defaultdict

from src.simulation import Simulation
from src.market_data import OrderSide


def run_audit(num_events=10_000, seed=42):
    simulation = Simulation(
        start_price=100.0,
        tick_size=0.01,
        time_step=0.001,
        seed=seed,
    )

    market = simulation.market
    book = simulation.book
    engine = simulation.engine
    recorder = simulation.state_recorder

    for _ in range(num_events):
        order = market.generate_order()

        previous_book = book.snapshot()

        tape_before = len(engine.trade_tape)

        engine.submit_order(order)

        tape_after = len(engine.trade_tape)

        new_trades = engine.trade_tape[tape_before:tape_after]

        last_trade = new_trades[-1] if new_trades else None

        recorder.record(
            previous_book=previous_book,
            current_book=book.snapshot(),
            timestamp=order.timestamp,
            trade=last_trade,
        )

    fair_value = market.fair_value
    tick_size = market.tick_size

    print("\n=== LIQUIDITY DISTRIBUTION AUDIT ===")

    print("\n--- MARKET ---")

    print(f"Fair value: {fair_value}")
    print(f"Best bid:   {book.best_bid}")
    print(f"Best ask:   {book.best_ask}")
    print(f"Spread:     {book.spread}")

    bid_levels = []
    ask_levels = []

    for price, queue in book.bid_orders.items():
        quantity = sum(
            order.quantity
            for order in queue
        )

        distance = (
            fair_value - price
        ) / tick_size

        bid_levels.append(
            (price, quantity, distance)
        )

    for price, queue in book.ask_orders.items():
        quantity = sum(
            order.quantity
            for order in queue
        )

        distance = (
            price - fair_value
        ) / tick_size

        ask_levels.append(
            (price, quantity, distance)
        )

    bid_levels.sort(reverse=True)
    ask_levels.sort()

    print("\n--- BID LIQUIDITY ---")

    print(
        f"Levels: {len(bid_levels)}"
    )

    total_bid_quantity = sum(
        quantity
        for _, quantity, _ in bid_levels
    )

    print(
        f"Total quantity: "
        f"{total_bid_quantity}"
    )

    for price, quantity, distance in bid_levels:
        print(
            f"BUY  {price:.2f} | "
            f"qty={quantity:4} | "
            f"{distance:.1f} ticks below FV"
        )

    print("\n--- ASK LIQUIDITY ---")

    print(
        f"Levels: {len(ask_levels)}"
    )

    total_ask_quantity = sum(
        quantity
        for _, quantity, _ in ask_levels
    )

    print(
        f"Total quantity: "
        f"{total_ask_quantity}"
    )

    for price, quantity, distance in ask_levels:
        print(
            f"SELL {price:.2f} | "
            f"qty={quantity:4} | "
            f"{distance:.1f} ticks above FV"
        )

    print("\n--- LIQUIDITY BY DISTANCE ---")

    distance_buckets = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 5),
        (5, 10),
        (10, float("inf")),
    ]

    for lower, upper in distance_buckets:

        bid_quantity = sum(
            quantity
            for _, quantity, distance in bid_levels
            if lower <= distance < upper
        )

        ask_quantity = sum(
            quantity
            for _, quantity, distance in ask_levels
            if lower <= distance < upper
        )

        print(
            f"{lower:>2}–"
            f"{'∞' if upper == float('inf') else upper:<2} ticks | "
            f"BUY={bid_quantity:5} | "
            f"SELL={ask_quantity:5}"
        )


if __name__ == "__main__":
    run_audit()