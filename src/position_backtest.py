from statistics import mean

from src.simulation import Simulation


LOWER_THRESHOLD = -0.017830188679255343
UPPER_THRESHOLD = 0.011518987341773368

HORIZON = 10


def run_backtest(states):
    trades = []

    i = 7000

    while i + HORIZON < len(states):

        state = states[i]

        if (
            state.microprice is None
            or state.mid_price is None
            or state.best_bid is None
            or state.best_ask is None
        ):
            i += 1
            continue

        signal = (
            state.microprice
            - state.mid_price
        )

        exit_index = i + HORIZON
        future = states[exit_index]

        if (
            future.best_bid is None
            or future.best_ask is None
        ):
            i += 1
            continue

        # BUY
        if signal >= UPPER_THRESHOLD:

            entry = state.best_ask
            exit_price = future.best_bid

            pnl = (
                exit_price - entry
            ) / entry

            trades.append({
                "direction": "BUY",
                "entry_index": i,
                "exit_index": exit_index,
                "pnl": pnl,
            })

            i = exit_index + 1
            continue

        # SELL
        if signal <= LOWER_THRESHOLD:

            entry = state.best_bid
            exit_price = future.best_ask

            pnl = (
                entry - exit_price
            ) / entry

            trades.append({
                "direction": "SELL",
                "entry_index": i,
                "exit_index": exit_index,
                "pnl": pnl,
            })

            i = exit_index + 1
            continue

        i += 1

    return trades


def summarize(trades, label):

    print(
        f"=== {label} ==="
    )

    if not trades:
        print("No trades")
        print()
        return

    returns = [
        trade["pnl"]
        for trade in trades
    ]

    print(
        "Trades:",
        len(trades),
    )

    print(
        "Average return:",
        mean(returns),
    )

    print(
        "Positive rate:",
        sum(
            x > 0
            for x in returns
        ) / len(returns),
    )

    print(
        "Total return:",
        sum(returns),
    )

    print()


def main():

    simulation = Simulation(
        seed=42,
        start_price=100.0,
        tick_size=0.01,
        time_step=0.001,
    )

    states = simulation.run(
        10_000
    )

    trades = run_backtest(
        states
    )

    buy_trades = [
        trade
        for trade in trades
        if trade["direction"] == "BUY"
    ]

    sell_trades = [
        trade
        for trade in trades
        if trade["direction"] == "SELL"
    ]

    print(
        "=== POSITION-AWARE OOS BACKTEST ==="
    )

    print(
        "Test period:",
        "7000 → 9999",
    )

    print(
        "Horizon:",
        HORIZON,
        "events",
    )

    print()

    summarize(
        trades,
        "ALL TRADES",
    )

    summarize(
        buy_trades,
        "BUY TRADES",
    )

    summarize(
        sell_trades,
        "SELL TRADES",
    )


if __name__ == "__main__":
    main()