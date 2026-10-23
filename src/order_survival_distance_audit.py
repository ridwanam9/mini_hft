from src.market_data import OrderSide
from src.simulation import Simulation


NUM_EVENTS = 10_000
SEED = 42


def main():
    simulation = Simulation(seed=SEED)
    simulation.run(NUM_EVENTS)

    book = simulation.book
    fair_value = simulation.market.fair_value
    tick_size = simulation.market.tick_size
    current_time = simulation.market.timestamp

    records = []

    for order_id, entry in book.order_index.items():
        side, price, order = entry

        age = current_time - order.timestamp
        distance_ticks = abs(price - fair_value) / tick_size

        records.append(
            {
                "order_id": order_id,
                "side": side,
                "price": price,
                "quantity": order.quantity,
                "age": age,
                "distance_ticks": distance_ticks,
            }
        )

    print()
    print("=== ORDER SURVIVAL / DISTANCE AUDIT ===")
    print()

    print("--- MARKET ---")
    print(f"Fair value:   {fair_value:.2f}")
    print(f"Current time: {current_time:.6f}")
    print()

    print("--- ACTIVE ORDERS ---")

    for record in sorted(
        records,
        key=lambda x: x["age"],
        reverse=True,
    ):
        print(
            f"{record['side'].name:4s} "
            f"price={record['price']:.2f} "
            f"qty={record['quantity']:3d} "
            f"age={record['age']:.3f}s "
            f"distance={record['distance_ticks']:.1f} ticks"
        )

    print()

    print("--- AGE BUCKETS ---")

    age_buckets = [
        ("0–0.01s", 0.00, 0.01),
        ("0.01–0.05s", 0.01, 0.05),
        ("0.05–0.10s", 0.05, 0.10),
        ("0.10–0.25s", 0.10, 0.25),
        ("0.25s+", 0.25, float("inf")),
    ]

    for name, lower, upper in age_buckets:
        bucket = [
            r
            for r in records
            if lower <= r["age"] < upper
        ]

        if not bucket:
            print(f"{name}: no orders")
            continue

        avg_distance = (
            sum(r["distance_ticks"] for r in bucket)
            / len(bucket)
        )

        total_quantity = sum(
            r["quantity"]
            for r in bucket
        )

        print(
            f"{name:12s} "
            f"orders={len(bucket):2d} "
            f"qty={total_quantity:4d} "
            f"avg_distance={avg_distance:.2f} ticks"
        )

    print()

    print("--- SIDE COMPARISON ---")

    for side in [OrderSide.BUY, OrderSide.SELL]:

        side_records = [
            r
            for r in records
            if r["side"] == side
        ]

        if not side_records:
            continue

        avg_age = (
            sum(r["age"] for r in side_records)
            / len(side_records)
        )

        avg_distance = (
            sum(r["distance_ticks"] for r in side_records)
            / len(side_records)
        )

        print(
            f"{side.name}: "
            f"orders={len(side_records)}, "
            f"avg_age={avg_age:.4f}s, "
            f"avg_distance={avg_distance:.2f} ticks"
        )


if __name__ == "__main__":
    main()