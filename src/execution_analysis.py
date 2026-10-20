from statistics import mean

from src.simulation import Simulation


def build_trades(
    states,
    horizon=10,
    lower_threshold=-0.017830188679255343,
    upper_threshold=0.011518987341773368,
):
    trades = []

    for i, state in enumerate(states):
        if (
            state.microprice is None
            or state.mid_price is None
            or state.best_bid is None
            or state.best_ask is None
        ):
            continue

        signal = (
            state.microprice
            - state.mid_price
        )

        future_index = i + horizon

        if future_index >= len(states):
            continue

        future_state = states[future_index]

        if (
            future_state.best_bid is None
            or future_state.best_ask is None
        ):
            continue

        # BUY signal
        if signal >= upper_threshold:
            entry_price = state.best_ask
            exit_price = future_state.best_bid

            gross_return = (
                exit_price - entry_price
            ) / entry_price

            trades.append({
                "direction": "BUY",
                "signal": signal,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "gross_return": gross_return,
            })

        # SELL signal
        elif signal <= lower_threshold:
            entry_price = state.best_bid
            exit_price = future_state.best_ask

            gross_return = (
                entry_price - exit_price
            ) / entry_price

            trades.append({
                "direction": "SELL",
                "signal": signal,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "gross_return": gross_return,
            })

    return trades


def add_transaction_cost(
    trades,
    cost_rate=0.0001,
):
    """
    cost_rate:
        Total transaction cost per round trip.

        Example:
        0.0001 = 0.01%
    """

    for trade in trades:
        trade["cost"] = cost_rate

        trade["net_return"] = (
            trade["gross_return"]
            - cost_rate
        )

    return trades


def analyze_trades(trades):
    if not trades:
        return None

    gross_returns = [
        trade["gross_return"]
        for trade in trades
    ]

    net_returns = [
        trade["net_return"]
        for trade in trades
    ]

    winning_trades = [
        trade
        for trade in trades
        if trade["net_return"] > 0
    ]

    return {
        "number_of_trades": len(trades),

        "average_gross_return": mean(
            gross_returns
        ),

        "average_net_return": mean(
            net_returns
        ),

        "positive_rate": (
            len(winning_trades)
            / len(trades)
        ),

        "total_gross_return": sum(
            gross_returns
        ),

        "total_net_return": sum(
            net_returns
        ),
    }


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

    trades = build_trades(
        states,
        horizon=10,
    )

    trades = add_transaction_cost(
        trades,
        cost_rate=0.0001,
    )

    results = analyze_trades(
        trades
    )

    print(
        "=== EXECUTION ANALYSIS ==="
    )

    print(
        "Number of trades:",
        results["number_of_trades"],
    )

    print(
        "Average gross return:",
        results["average_gross_return"],
    )

    print(
        "Average net return:",
        results["average_net_return"],
    )

    print(
        "Positive rate:",
        results["positive_rate"],
    )

    print(
        "Total gross return:",
        results["total_gross_return"],
    )

    print(
        "Total net return:",
        results["total_net_return"],
    )


if __name__ == "__main__":
    main()