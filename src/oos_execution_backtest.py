from statistics import mean

from src.simulation import Simulation


LOWER_THRESHOLD = -0.017830188679255343
UPPER_THRESHOLD = 0.011518987341773368


def build_trades(
    states,
    start_index,
    end_index,
    horizon=10,
):
    trades = []

    for i in range(
        start_index,
        end_index,
    ):
        if i + horizon >= len(states):
            break

        state = states[i]
        future = states[i + horizon]

        if (
            state.microprice is None
            or state.mid_price is None
            or state.best_bid is None
            or state.best_ask is None
        ):
            continue

        if (
            future.best_bid is None
            or future.best_ask is None
        ):
            continue

        signal = (
            state.microprice
            - state.mid_price
        )

        # BUY
        if signal >= UPPER_THRESHOLD:

            entry = state.best_ask
            exit = future.best_bid

            pnl = (
                exit - entry
            ) / entry

            trades.append({
                "direction": "BUY",
                "pnl": pnl,
            })

        # SELL
        elif signal <= LOWER_THRESHOLD:

            entry = state.best_bid
            exit = future.best_ask

            pnl = (
                entry - exit
            ) / entry

            trades.append({
                "direction": "SELL",
                "pnl": pnl,
            })

    return trades


def summarize(
    trades,
    label,
):
    if not trades:
        print(
            f"{label}: no trades"
        )
        return

    returns = [
        trade["pnl"]
        for trade in trades
    ]

    print(
        f"=== {label} ==="
    )

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

    split_index = int(
        len(states) * 0.7
    )

    # TEST ONLY
    test_trades = build_trades(
        states,
        start_index=split_index,
        end_index=len(states),
        horizon=10,
    )

    buy_trades = [
        trade
        for trade in test_trades
        if trade["direction"] == "BUY"
    ]

    sell_trades = [
        trade
        for trade in test_trades
        if trade["direction"] == "SELL"
    ]

    print(
        "=== OOS EXECUTION BACKTEST ==="
    )

    print(
        "Total states:",
        len(states),
    )

    print(
        "Train states:",
        split_index,
    )

    print(
        "Test states:",
        len(states) - split_index,
    )

    print()

    summarize(
        test_trades,
        "ALL TEST TRADES",
    )

    summarize(
        buy_trades,
        "BUY TEST TRADES",
    )

    summarize(
        sell_trades,
        "SELL TEST TRADES",
    )


if __name__ == "__main__":
    main()