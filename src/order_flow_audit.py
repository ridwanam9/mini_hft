from collections import Counter

from src.simulation import Simulation
from src.market_data import OrderSide, OrderType


def run_audit(num_events=10_000, seed=42):
    simulation = Simulation(
        start_price=100.0,
        tick_size=0.01,
        time_step=0.001,
        seed=seed,
    )

    states = []

    # Jalankan simulation manual supaya kita bisa
    # mengamati setiap order yang dibuat.
    market = simulation.market
    book = simulation.book
    engine = simulation.engine
    recorder = simulation.state_recorder

    event_counts = Counter()
    resting_counts = Counter()
    trade_counts = Counter()

    submitted_volume = Counter()
    traded_volume = Counter()

    for _ in range(num_events):
        order = market.generate_order()

        # Klasifikasi order yang masuk
        key = (
            "LIMIT_BUY"
            if order.order_type == OrderType.LIMIT
            and order.side == OrderSide.BUY
            else "LIMIT_SELL"
            if order.order_type == OrderType.LIMIT
            and order.side == OrderSide.SELL
            else "MARKET_BUY"
            if order.order_type == OrderType.MARKET
            and order.side == OrderSide.BUY
            else "MARKET_SELL"
        )

        event_counts[key] += 1
        submitted_volume[key] += order.quantity

        previous_book = book.snapshot()

        tape_before = len(engine.trade_tape)

        fills = engine.submit_order(order)

        tape_after = len(engine.trade_tape)

        new_trades = engine.trade_tape[tape_before:tape_after]

        # Apakah order menghasilkan trade?
        if fills:
            trade_counts[key] += 1

            for trade in fills:
                traded_volume[key] += trade.quantity

        # Apakah order menjadi resting order?
        if order.order_id in book.order_index:
            resting_counts[key] += 1

        current_book = book.snapshot()

        last_trade = new_trades[-1] if new_trades else None

        recorder.record(
            previous_book=previous_book,
            current_book=current_book,
            timestamp=order.timestamp,
            trade=last_trade,
        )

    states = recorder.states

    print("\n=== ORDER FLOW & LIQUIDITY AUDIT ===")

    print("\n--- EVENT COUNTS ---")

    total_events = sum(event_counts.values())

    for key in [
        "LIMIT_BUY",
        "LIMIT_SELL",
        "MARKET_BUY",
        "MARKET_SELL",
    ]:
        count = event_counts[key]
        percentage = count / total_events * 100

        print(
            f"{key:12} : "
            f"{count:5} "
            f"({percentage:.2f}%)"
        )

    print("\n--- SUBMITTED VOLUME ---")

    for key in [
        "LIMIT_BUY",
        "LIMIT_SELL",
        "MARKET_BUY",
        "MARKET_SELL",
    ]:
        print(
            f"{key:12} : "
            f"{submitted_volume[key]}"
        )

    print("\n--- TRADES ---")

    for key in [
        "LIMIT_BUY",
        "LIMIT_SELL",
        "MARKET_BUY",
        "MARKET_SELL",
    ]:
        print(
            f"{key:12} : "
            f"{trade_counts[key]:5} "
            f"orders produced trades"
        )

    print("\n--- TRADED VOLUME ---")

    for key in [
        "LIMIT_BUY",
        "LIMIT_SELL",
        "MARKET_BUY",
        "MARKET_SELL",
    ]:
        print(
            f"{key:12} : "
            f"{traded_volume[key]}"
        )

    print("\n--- RESTING ORDERS ---")

    for key in [
        "LIMIT_BUY",
        "LIMIT_SELL",
        "MARKET_BUY",
        "MARKET_SELL",
    ]:
        print(
            f"{key:12} : "
            f"{resting_counts[key]:5} "
            f"orders became resting"
        )

    print("\n--- TRADE EXECUTION RATE ---")

    for key in [
        "MARKET_BUY",
        "MARKET_SELL",
    ]:
        count = event_counts[key]

        if count:
            rate = trade_counts[key] / count * 100
        else:
            rate = 0

        print(
            f"{key:12} : "
            f"{rate:.2f}%"
        )

    print("\n--- LIMIT ORDER RESTING RATE ---")

    for key in [
        "LIMIT_BUY",
        "LIMIT_SELL",
    ]:
        count = event_counts[key]

        if count:
            rate = resting_counts[key] / count * 100
        else:
            rate = 0

        print(
            f"{key:12} : "
            f"{rate:.2f}%"
        )

    print("\n--- FINAL BOOK ---")

    print(f"Best bid: {book.best_bid}")
    print(f"Best ask: {book.best_ask}")
    print(f"Spread:   {book.spread}")

    print("\n--- FINAL DEPTH ---")

    bids, asks = book.get_depth(5)

    print("BIDS:")
    for price, quantity in bids:
        print(f"  {price:.2f} : {quantity}")

    print("ASKS:")
    for price, quantity in asks:
        print(f"  {price:.2f} : {quantity}")


if __name__ == "__main__":
    run_audit()