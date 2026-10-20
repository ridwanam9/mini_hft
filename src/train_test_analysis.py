from statistics import mean

from src.simulation import Simulation


def future_return(
    mid_prices,
    index,
    horizon,
):
    current_price = mid_prices[index]

    future_index = index + horizon

    if future_index >= len(mid_prices):
        return None

    future_price = mid_prices[future_index]

    if (
        current_price is None
        or future_price is None
    ):
        return None

    return (
        future_price - current_price
    ) / current_price


def build_data(
    states,
    horizon=10,
):
    mid_prices = [
        state.mid_price
        for state in states
    ]

    data = []

    for i, state in enumerate(states):
        if (
            state.microprice is None
            or state.mid_price is None
        ):
            continue

        future = future_return(
            mid_prices,
            i,
            horizon,
        )

        if future is None:
            continue

        deviation = (
            state.microprice
            - state.mid_price
        )

        data.append(
            (deviation, future)
        )

    return data


def split_data(
    data,
    train_ratio=0.7,
):
    split_index = int(
        len(data)
        * train_ratio
    )

    train = data[:split_index]
    test = data[split_index:]

    return train, test


def quantile_thresholds(
    train,
):
    signals = sorted(
        signal
        for signal, _ in train
    )

    n = len(signals)

    q20 = signals[
        int(n * 0.20)
    ]

    q80 = signals[
        int(n * 0.80)
    ]

    return q20, q80


def analyze_region(
    data,
    lower,
    upper,
):
    selected = [
        future
        for signal, future in data
        if (
            signal >= lower
            and signal <= upper
        )
    ]

    if not selected:
        return None

    return {
        "n": len(selected),
        "mean_return": mean(selected),
        "positive_rate": (
            sum(
                value > 0
                for value in selected
            )
            / len(selected)
        ),
    }


def analyze_train_test():
    simulation = Simulation(
        seed=42,
        start_price=100.0,
        tick_size=0.01,
        time_step=0.001,
    )

    states = simulation.run(
        10_000
    )

    data = build_data(
        states,
        horizon=10,
    )

    train, test = split_data(
        data,
        train_ratio=0.7,
    )

    lower, upper = (
        quantile_thresholds(train)
    )

    print(
        "=== TRAIN / TEST ANALYSIS ==="
    )

    print(
        "Total observations:",
        len(data),
    )

    print(
        "Train observations:",
        len(train),
    )

    print(
        "Test observations:",
        len(test),
    )

    print()

    print(
        "=== THRESHOLDS FROM TRAIN ==="
    )

    print(
        "Lower threshold:",
        lower,
    )

    print(
        "Upper threshold:",
        upper,
    )

    print()

    print(
        "=== TRAIN ==="
    )

    train_low = analyze_region(
        train,
        float("-inf"),
        lower,
    )

    train_high = analyze_region(
        train,
        upper,
        float("inf"),
    )

    print(
        "Low signal:",
        train_low,
    )

    print(
        "High signal:",
        train_high,
    )

    print()

    print(
        "=== TEST ==="
    )

    test_low = analyze_region(
        test,
        float("-inf"),
        lower,
    )

    test_high = analyze_region(
        test,
        upper,
        float("inf"),
    )

    print(
        "Low signal:",
        test_low,
    )

    print(
        "High signal:",
        test_high,
    )


if __name__ == "__main__":
    analyze_train_test()