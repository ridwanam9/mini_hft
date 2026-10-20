import csv
from pathlib import Path
from statistics import mean

from src.simulation import Simulation


def to_float(value):
    if value == "":
        return None

    return float(value)


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


def generate_dataset(
    seed,
    num_events=1_000,
):
    simulation = Simulation(
        seed=seed,
        start_price=100.0,
        tick_size=0.01,
        time_step=0.001,
    )

    states = simulation.run(
        num_events
    )

    return states


def build_signal_returns(
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


def create_quantile_buckets(
    data,
    num_buckets=5,
):
    sorted_data = sorted(
        data,
        key=lambda x: x[0],
    )

    n = len(sorted_data)

    buckets = []

    for bucket_index in range(
        num_buckets
    ):
        start = (
            bucket_index * n
        ) // num_buckets

        end = (
            (bucket_index + 1) * n
        ) // num_buckets

        bucket = sorted_data[
            start:end
        ]

        if bucket:
            buckets.append(bucket)

    return buckets


def analyze_seed(seed):
    states = generate_dataset(
        seed=seed,
        num_events=1_000,
    )

    data = build_signal_returns(
        states,
        horizon=10,
    )

    buckets = create_quantile_buckets(
        data,
        num_buckets=5,
    )

    bucket_returns = [
        mean(
            item[1]
            for item in bucket
        )
        for bucket in buckets
    ]

    bucket_1 = bucket_returns[0]
    bucket_5 = bucket_returns[-1]

    difference = (
        bucket_5 - bucket_1
    )

    return (
        bucket_returns,
        difference,
    )


def main():
    seeds = range(1, 21)

    results = []

    print(
        "=== MULTI-SEED ANALYSIS ==="
    )

    print(
        "Signal: microprice deviation"
    )

    print(
        "Horizon: 10 events"
    )

    print()

    for seed in seeds:
        (
            bucket_returns,
            difference,
        ) = analyze_seed(seed)

        results.append(
            difference
        )

        print(
            f"Seed {seed:2d}: "
            f"B1={bucket_returns[0]: .8f} "
            f"B5={bucket_returns[-1]: .8f} "
            f"Diff={difference: .8f}"
        )

    positive_difference = sum(
        difference > 0
        for difference in results
    )

    print()

    print(
        "=== SUMMARY ==="
    )

    print(
        "Seeds tested:",
        len(results),
    )

    print(
        "B5 > B1:",
        positive_difference,
        "/",
        len(results),
    )

    print(
        "Average B5-B1 difference:",
        mean(results),
    )

    print(
        "Minimum difference:",
        min(results),
    )

    print(
        "Maximum difference:",
        max(results),
    )


if __name__ == "__main__":
    main()