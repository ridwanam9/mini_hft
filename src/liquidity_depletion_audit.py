from src.market_data import OrderSide, OrderType
from src.simulation import Simulation


def run_audit(num_events=10_000, seed=42):
    simulation = Simulation(seed=seed)

    bid_empty_events = []
    ask_empty_events = []

    bid_replenishment = []
    ask_replenishment = []

    for _ in range(num_events):
        order = simulation.market.generate_order()

        # Book sebelum event
        previous_book = simulation.book.snapshot()

        previous_bid_liquidity = sum(previous_book.bids.values())
        previous_ask_liquidity = sum(previous_book.asks.values())

        previous_bid_empty = not previous_book.bids
        previous_ask_empty = not previous_book.asks

        tape_length_before = len(simulation.engine.trade_tape)

        simulation.engine.submit_order(order)

        # Book setelah event
        current_book = simulation.book.snapshot()

        current_bid_liquidity = sum(current_book.bids.values())
        current_ask_liquidity = sum(current_book.asks.values())

        current_bid_empty = not current_book.bids
        current_ask_empty = not current_book.asks

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

        # -----------------------------
        # BID BECAME EMPTY
        # -----------------------------
        if not previous_bid_empty and current_bid_empty:
            bid_empty_events.append({
                "order_type": order.order_type,
                "side": order.side,
                "requested": order.quantity,
                "executed": executed_quantity,
                "previous_liquidity": previous_bid_liquidity,
                "current_liquidity": current_bid_liquidity,
            })

        # -----------------------------
        # ASK BECAME EMPTY
        # -----------------------------
        if not previous_ask_empty and current_ask_empty:
            ask_empty_events.append({
                "order_type": order.order_type,
                "side": order.side,
                "requested": order.quantity,
                "executed": executed_quantity,
                "previous_liquidity": previous_ask_liquidity,
                "current_liquidity": current_ask_liquidity,
            })

        # -----------------------------
        # BID REPLENISHMENT
        # -----------------------------
        if previous_bid_empty and not current_bid_empty:
            bid_replenishment.append({
                "order_type": order.order_type,
                "side": order.side,
                "new_liquidity": current_bid_liquidity,
            })

        # -----------------------------
        # ASK REPLENISHMENT
        # -----------------------------
        if previous_ask_empty and not current_ask_empty:
            ask_replenishment.append({
                "order_type": order.order_type,
                "side": order.side,
                "new_liquidity": current_ask_liquidity,
            })

    print("=== LIQUIDITY DEPLETION & REPLENISHMENT AUDIT ===")

    print("\n--- BID DEPLETION ---")
    print_depletion_summary(bid_empty_events)

    print("\n--- ASK DEPLETION ---")
    print_depletion_summary(ask_empty_events)

    print("\n--- BID REPLENISHMENT ---")
    print_replenishment_summary(bid_replenishment)

    print("\n--- ASK REPLENISHMENT ---")
    print_replenishment_summary(ask_replenishment)


def print_depletion_summary(records):
    print(f"events: {len(records)}")

    if not records:
        return

    market_orders = [
        r for r in records
        if r["order_type"] == OrderType.MARKET
    ]

    limit_orders = [
        r for r in records
        if r["order_type"] == OrderType.LIMIT
    ]

    print(f"caused by market orders: {len(market_orders)}")
    print(f"caused by limit orders:  {len(limit_orders)}")

    if market_orders:
        avg_previous = (
            sum(r["previous_liquidity"] for r in market_orders)
            / len(market_orders)
        )

        avg_executed = (
            sum(r["executed"] for r in market_orders)
            / len(market_orders)
        )

        print(
            f"avg liquidity before market order: "
            f"{avg_previous:.2f}"
        )

        print(
            f"avg executed quantity: "
            f"{avg_executed:.2f}"
        )


def print_replenishment_summary(records):
    print(f"events: {len(records)}")

    if not records:
        return

    market_orders = [
        r for r in records
        if r["order_type"] == OrderType.MARKET
    ]

    limit_orders = [
        r for r in records
        if r["order_type"] == OrderType.LIMIT
    ]

    print(f"caused by market orders: {len(market_orders)}")
    print(f"caused by limit orders:  {len(limit_orders)}")

    avg_new_liquidity = (
        sum(r["new_liquidity"] for r in records)
        / len(records)
    )

    print(
        f"avg new liquidity: "
        f"{avg_new_liquidity:.2f}"
    )


if __name__ == "__main__":
    run_audit()