from collections import defaultdict

from src.market_data import OrderSide
from src.simulation import Simulation


NUM_EVENTS = 10_000
SEED = 42


def main():
    simulation = Simulation(seed=SEED)
    simulation.run(NUM_EVENTS)

    book = simulation.book
    engine = simulation.engine

    current_time = simulation.market.timestamp

    # ---------------------------------------------------------
    # Collect all orders that were submitted
    # ---------------------------------------------------------

    orders = {}

    for order_id, entry in book.order_index.items():
        _, _, order = entry
        orders[order_id] = {
            "order": order,
            "status": "active",
            "end_time": current_time,
        }

    # Trade tape tells us which orders were executed.
    executed_orders = defaultdict(int)
    execution_times = defaultdict(list)

    for trade in engine.trade_tape:
        executed_orders[trade.buy_order_id] += trade.quantity
        executed_orders[trade.sell_order_id] += trade.quantity

        execution_times[trade.buy_order_id].append(trade.timestamp)
        execution_times[trade.sell_order_id].append(trade.timestamp)

    # ---------------------------------------------------------
    # NOTE:
    # The current Order object does not keep a historical
    # registry of every submitted order.
    #
    # Therefore this audit can accurately inspect:
    # - active orders at the end
    # - their ages
    # - execution information available from trade tape
    #
    # But it cannot reconstruct lifetime of every fully
    # executed order unless we add historical order tracking.
    # ---------------------------------------------------------

    active_buy = []
    active_sell = []

    for data in orders.values():
        order = data["order"]

        age = current_time - order.timestamp

        if order.side == OrderSide.BUY:
            active_buy.append(age)
        else:
            active_sell.append(age)

    def summarize(name, values):
        if not values:
            print(f"{name}: no orders")
            return

        values = sorted(values)

        mean = sum(values) / len(values)
        median = values[len(values) // 2]

        print(f"{name}:")
        print(f"  count:  {len(values)}")
        print(f"  mean:   {mean:.6f} sec")
        print(f"  median: {median:.6f} sec")
        print(f"  min:    {min(values):.6f} sec")
        print(f"  max:    {max(values):.6f} sec")

        for threshold in [0.01, 0.05, 0.10, 0.25, 0.50, 1.0]:
            count = sum(age >= threshold for age in values)
            pct = count / len(values) * 100

            print(
                f"  age >= {threshold:.2f}s: "
                f"{count:4d} ({pct:6.2f}%)"
            )

    print()
    print("=== LIQUIDITY LIFETIME AUDIT ===")
    print()

    print("--- SIMULATION ---")
    print(f"Events:       {NUM_EVENTS}")
    print(f"Seed:         {SEED}")
    print(f"Current time: {current_time:.6f} sec")
    print()

    print("--- ACTIVE ORDERS AT END ---")
    print(f"Total active orders: {len(orders)}")
    print()

    summarize("BUY", active_buy)
    print()
    summarize("SELL", active_sell)

    print()
    print("--- EXECUTION SUMMARY ---")

    total_trade_records = len(engine.trade_tape)

    print(f"Trade records: {total_trade_records}")
    print(
        f"Unique executed orders: "
        f"{len(executed_orders)}"
    )

    print()
    print(
        "NOTE: historical lifetime of fully executed "
        "orders is not yet measurable."
    )
    print(
        "The current result measures lifetime of orders "
        "still active at the end."
    )


if __name__ == "__main__":
    main()