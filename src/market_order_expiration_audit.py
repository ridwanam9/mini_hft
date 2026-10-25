from src.market_data import OrderSide, OrderType
from src.simulation import Simulation


NUM_EVENTS = 10_000
SEED = 42


def summarize(name, records):
    print(f"\n{name}")

    if not records:
        print("  no records")
        return

    total_orders = len(records)

    total_original = sum(
        r["original_quantity"]
        for r in records
    )

    total_executed = sum(
        r["executed_quantity"]
        for r in records
    )

    total_remaining = sum(
        r["remaining_quantity"]
        for r in records
    )

    avg_original = total_original / total_orders
    avg_executed = total_executed / total_orders
    avg_remaining = total_remaining / total_orders

    execution_rate = (
        total_executed / total_original
        if total_original > 0
        else 0.0
    )

    print(f"  orders:             {total_orders}")
    print(f"  original quantity:  {total_original}")
    print(f"  executed quantity:  {total_executed}")
    print(f"  remaining quantity: {total_remaining}")
    print(f"  avg original:       {avg_original:.2f}")
    print(f"  avg executed:       {avg_executed:.2f}")
    print(f"  avg remaining:      {avg_remaining:.2f}")
    print(f"  execution rate:     {execution_rate:.2%}")


def main():
    simulation = Simulation(seed=SEED)
    simulation.run(NUM_EVENTS)

    history = simulation.book.order_history

    expired = [
        record
        for record in history.values()
        if record["status"] == "expired"
    ]

    expired_buy = [
        record
        for record in expired
        if record["order"].side == OrderSide.BUY
    ]

    expired_sell = [
        record
        for record in expired
        if record["order"].side == OrderSide.SELL
    ]

    print()
    print("=== MARKET ORDER EXPIRATION AUDIT ===")
    print()

    print("--- SUMMARY ---")
    print(f"Expired market orders: {len(expired)}")
    print()

    summarize("BUY EXPIRED", expired_buy)
    summarize("SELL EXPIRED", expired_sell)

    print()
    print("--- ALL EXPIRED ---")
    summarize("MARKET ORDERS", expired)


if __name__ == "__main__":
    main()