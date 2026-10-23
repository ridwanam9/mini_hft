from collections import Counter

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

    current_time = market.timestamp
    fair_value = market.fair_value
    tick_size = market.tick_size

    ages = []
    distances = []
    quantities = []

    side_counts = Counter()
    stale_orders = Counter()
    stale_quantity = Counter()

    # Semua active resting orders
    for order_id, (side, price, order) in book.order_index.items():

        age = current_time - order.timestamp

        distance_ticks = abs(
            price - fair_value
        ) / tick_size

        ages.append(age)
        distances.append(distance_ticks)
        quantities.append(order.quantity)

        side_name = (
            "BUY"
            if side == OrderSide.BUY
            else "SELL"
        )

        side_counts[side_name] += 1

        # Definisi sementara stale:
        # lebih dari 100 events
        if age >= 0.1:
            stale_orders[side_name] += 1
            stale_quantity[side_name] += order.quantity

    print("\n=== RESTING ORDER AGE AUDIT ===")

    print("\n--- CURRENT MARKET ---")

    print(f"Current time: {current_time}")
    print(f"Fair value:   {fair_value}")
    print(f"Best bid:     {book.best_bid}")
    print(f"Best ask:     {book.best_ask}")
    print(f"Spread:       {book.spread}")

    print("\n--- ACTIVE ORDERS ---")

    print(f"Total active orders: {len(ages)}")

    print(f"BUY orders:  {side_counts['BUY']}")
    print(f"SELL orders: {side_counts['SELL']}")

    if ages:
        print("\n--- ORDER AGE ---")

        print(f"Average age: {sum(ages) / len(ages):.6f}")
        print(f"Minimum age: {min(ages):.6f}")
        print(f"Maximum age: {max(ages):.6f}")

        age_thresholds = [
            0.01,
            0.05,
            0.10,
            0.25,
            0.50,
            1.00,
        ]

        print("\nAge distribution:")

        for threshold in age_thresholds:
            count = sum(
                age >= threshold
                for age in ages
            )

            percentage = count / len(ages) * 100

            print(
                f">= {threshold:.2f}s : "
                f"{count:5} "
                f"({percentage:.2f}%)"
            )

    if distances:
        print("\n--- DISTANCE FROM FAIR VALUE ---")

        print(
            f"Average distance: "
            f"{sum(distances) / len(distances):.2f} ticks"
        )

        print(
            f"Minimum distance: "
            f"{min(distances):.2f} ticks"
        )

        print(
            f"Maximum distance: "
            f"{max(distances):.2f} ticks"
        )

        distance_thresholds = [
            1,
            2,
            5,
            10,
            20,
            50,
        ]

        print("\nDistance distribution:")

        for threshold in distance_thresholds:
            count = sum(
                distance >= threshold
                for distance in distances
            )

            percentage = count / len(distances) * 100

            print(
                f">= {threshold:2} ticks : "
                f"{count:5} "
                f"({percentage:.2f}%)"
            )

    print("\n--- STALE ORDERS ---")

    print("Stale threshold: >= 0.10 seconds")

    print(
        f"BUY stale orders:  "
        f"{stale_orders['BUY']}"
    )

    print(
        f"SELL stale orders: "
        f"{stale_orders['SELL']}"
    )

    print(
        f"BUY stale quantity: "
        f"{stale_quantity['BUY']}"
    )

    print(
        f"SELL stale quantity: "
        f"{stale_quantity['SELL']}"
    )

    if quantities:
        print("\n--- QUANTITY ---")

        print(
            f"Average quantity: "
            f"{sum(quantities) / len(quantities):.2f}"
        )

        print(
            f"Maximum quantity: "
            f"{max(quantities)}"
        )


if __name__ == "__main__":
    run_audit()