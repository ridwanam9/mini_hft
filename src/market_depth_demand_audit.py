from src.market_data import OrderSide, OrderType
from src.simulation import Simulation


def run_audit(num_events=10_000, seed=42):
    simulation = Simulation(seed=seed)

    all_market_orders = []
    expired_market_orders = []

    for _ in range(num_events):
        order = simulation.market.generate_order()

        # IMPORTANT:
        # Ambil liquidity SEBELUM order dieksekusi.
        previous_book = simulation.book.snapshot()

        if order.order_type == OrderType.MARKET:
            if order.side == OrderSide.BUY:
                available_liquidity = sum(previous_book.asks.values())
            else:
                available_liquidity = sum(previous_book.bids.values())
        else:
            available_liquidity = None

        tape_length_before = len(simulation.engine.trade_tape)

        simulation.engine.submit_order(order)

        new_trades = simulation.engine.trade_tape[tape_length_before:]

        executed_quantity = sum(
            trade.quantity
            for trade in new_trades
            if (
                (order.side == OrderSide.BUY and trade.buy_order_id == order.order_id)
                or
                (order.side == OrderSide.SELL and trade.sell_order_id == order.order_id)
            )
        )

        if order.order_type != OrderType.MARKET:
            continue

        requested_quantity = order.quantity
        remaining_quantity = (
            simulation.book.order_history[order.order_id]["remaining_quantity"]
        )

        coverage = (
            available_liquidity / requested_quantity
            if requested_quantity > 0
            else 0
        )

        execution_rate = (
            executed_quantity / requested_quantity
            if requested_quantity > 0
            else 0
        )

        record = {
            "side": order.side.value,
            "requested": requested_quantity,
            "available": available_liquidity,
            "executed": executed_quantity,
            "remaining": remaining_quantity,
            "coverage": coverage,
            "execution_rate": execution_rate,
        }

        all_market_orders.append(record)

        if remaining_quantity > 0:
            expired_market_orders.append(record)

    print("=== MARKET DEPTH VS DEMAND AUDIT ===")

    print("\n--- ALL MARKET ORDERS ---")
    print_summary(all_market_orders)

    print("\n--- EXPIRED MARKET ORDERS ---")
    print_summary(expired_market_orders)


def print_summary(records):
    if not records:
        print("No records.")
        return

    for side in ["buy", "sell"]:
        side_records = [
            r for r in records
            if r["side"] == side
        ]

        if not side_records:
            continue

        avg_requested = (
            sum(r["requested"] for r in side_records)
            / len(side_records)
        )

        avg_available = (
            sum(r["available"] for r in side_records)
            / len(side_records)
        )

        avg_executed = (
            sum(r["executed"] for r in side_records)
            / len(side_records)
        )

        avg_coverage = (
            sum(r["coverage"] for r in side_records)
            / len(side_records)
        )

        avg_execution_rate = (
            sum(r["execution_rate"] for r in side_records)
            / len(side_records)
        )

        print(f"\n{side.upper()}")
        print(f"  orders:              {len(side_records)}")
        print(f"  avg requested:       {avg_requested:.2f}")
        print(f"  avg available:       {avg_available:.2f}")
        print(f"  avg executed:        {avg_executed:.2f}")
        print(f"  avg coverage:        {avg_coverage:.4f}")
        print(f"  avg execution rate:  {avg_execution_rate:.2%}")

        coverages = sorted(r["coverage"] for r in side_records)

        median_coverage = coverages[len(coverages) // 2]

        print(f"  median coverage:     {median_coverage:.4f}")


if __name__ == "__main__":
    run_audit()

    