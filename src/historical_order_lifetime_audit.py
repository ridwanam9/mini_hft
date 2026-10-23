from src.market_data import OrderSide
from src.simulation import Simulation


NUM_EVENTS = 10_000
SEED = 42


def summarize(name, records):
    if not records:
        print(f"{name}: no records")
        return

    lifetimes = [
        r["completion_time"] - r["order"].timestamp
        for r in records
    ]

    first_fill_lifetimes = [
        r["first_fill_time"] - r["order"].timestamp
        for r in records
        if r["first_fill_time"] is not None
    ]

    lifetimes.sort()
    first_fill_lifetimes.sort()

    mean = sum(lifetimes) / len(lifetimes)
    median = lifetimes[len(lifetimes) // 2]

    print(f"{name}:")
    print(f"  fully filled:       {len(records)}")
    print(f"  mean lifetime:      {mean:.6f}s")
    print(f"  median lifetime:    {median:.6f}s")
    print(f"  min lifetime:       {min(lifetimes):.6f}s")
    print(f"  max lifetime:       {max(lifetimes):.6f}s")

    if first_fill_lifetimes:
        first_mean = (
            sum(first_fill_lifetimes)
            / len(first_fill_lifetimes)
        )

        first_median = first_fill_lifetimes[
            len(first_fill_lifetimes) // 2
        ]

        print(f"  mean first fill:    {first_mean:.6f}s")
        print(f"  median first fill:  {first_median:.6f}s")

    for threshold in [0.001, 0.005, 0.01, 0.05, 0.10]:
        count = sum(
            lifetime <= threshold
            for lifetime in lifetimes
        )

        pct = count / len(lifetimes) * 100

        print(
            f"  filled <= {threshold:.3f}s: "
            f"{count:5d} ({pct:6.2f}%)"
        )


def main():
    simulation = Simulation(seed=SEED)
    simulation.run(NUM_EVENTS)

    history = simulation.book.order_history

    filled = [
        record
        for record in history.values()
        if record["status"] == "filled"
    ]

    active = [
        record
        for record in history.values()
        if record["status"] == "active"
    ]

    buy_filled = [
        record
        for record in filled
        if record["order"].side == OrderSide.BUY
    ]

    sell_filled = [
        record
        for record in filled
        if record["order"].side == OrderSide.SELL
    ]

    buy_active = [
        record
        for record in active
        if record["order"].side == OrderSide.BUY
    ]

    sell_active = [
        record
        for record in active
        if record["order"].side == OrderSide.SELL
    ]

    print()
    print("=== HISTORICAL ORDER LIFETIME AUDIT ===")
    print()

    print("--- SUMMARY ---")
    print(f"Total historical orders: {len(history)}")
    print(f"Fully filled:            {len(filled)}")
    print(f"Still active:            {len(active)}")
    print()

    summarize("BUY FILLED", buy_filled)
    print()

    summarize("SELL FILLED", sell_filled)
    print()

    print("--- ACTIVE SURVIVORS ---")
    print(f"BUY:  {len(buy_active)}")
    print(f"SELL: {len(sell_active)}")


if __name__ == "__main__":
    main()