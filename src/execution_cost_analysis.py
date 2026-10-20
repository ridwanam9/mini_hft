from statistics import mean

from src.simulation import Simulation


LOWER_THRESHOLD = -0.017830188679255343
UPPER_THRESHOLD = 0.011518987341773368


def analyze(
    states,
    horizon=10,
):
    results = []

    for i, state in enumerate(states):
        if (
            state.microprice is None
            or state.mid_price is None
            or state.best_bid is None
            or state.best_ask is None
        ):
            continue

        future_index = i + horizon

        if future_index >= len(states):
            continue

        future = states[future_index]

        if (
            future.mid_price is None
            or future.best_bid is None
            or future.best_ask is None
        ):
            continue

        signal = (
            state.microprice
            - state.mid_price
        )

        # BUY
        if signal >= UPPER_THRESHOLD:
            direction = "BUY"

            # What the signal predicts:
            mid_return = (
                future.mid_price
                - state.mid_price
            ) / state.mid_price

            # Actual market-order execution:
            execution_return = (
                future.best_bid
                - state.best_ask
            ) / state.best_ask

            # Immediate entry spread component.
            entry_spread = (
                state.best_ask
                - state.mid_price
            ) / state.mid_price

            # Immediate exit spread component.
            exit_spread = (
                future.mid_price
                - future.best_bid
            ) / future.mid_price

        # SELL
        elif signal <= LOWER_THRESHOLD:
            direction = "SELL"

            mid_return = (
                state.mid_price
                - future.mid_price
            ) / state.mid_price

            execution_return = (
                state.best_bid
                - future.best_ask
            ) / state.best_bid

            entry_spread = (
                state.mid_price
                - state.best_bid
            ) / state.mid_price

            exit_spread = (
                future.best_ask
                - future.mid_price
            ) / future.mid_price

        else:
            continue

        results.append({
            "direction": direction,
            "mid_return": mid_return,
            "execution_return": execution_return,
            "entry_spread": entry_spread,
            "exit_spread": exit_spread,
        })

    return results


def summarize(results):
    if not results:
        return None

    mid_returns = [
        x["mid_return"]
        for x in results
    ]

    execution_returns = [
        x["execution_return"]
        for x in results
    ]

    entry_spreads = [
        x["entry_spread"]
        for x in results
    ]

    exit_spreads = [
        x["exit_spread"]
        for x in results
    ]

    return {
        "trades": len(results),

        "avg_mid_return": mean(
            mid_returns
        ),

        "avg_execution_return": mean(
            execution_returns
        ),

        "avg_entry_spread": mean(
            entry_spreads
        ),

        "avg_exit_spread": mean(
            exit_spreads
        ),

        "mid_positive_rate": (
            sum(
                x > 0
                for x in mid_returns
            )
            / len(mid_returns)
        ),

        "execution_positive_rate": (
            sum(
                x > 0
                for x in execution_returns
            )
            / len(execution_returns)
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

    results = analyze(
        states,
        horizon=10,
    )

    summary = summarize(
        results
    )

    print(
        "=== EXECUTION COST DECOMPOSITION ==="
    )

    print(
        "Trades:",
        summary["trades"],
    )

    print()

    print(
        "Average MID → MID return:",
        summary["avg_mid_return"],
    )

    print(
        "Average ASK/BID execution return:",
        summary["avg_execution_return"],
    )

    print()

    print(
        "Average entry spread:",
        summary["avg_entry_spread"],
    )

    print(
        "Average exit spread:",
        summary["avg_exit_spread"],
    )

    print()

    print(
        "MID positive rate:",
        summary["mid_positive_rate"],
    )

    print(
        "Execution positive rate:",
        summary["execution_positive_rate"],
    )


if __name__ == "__main__":
    main()