import csv
import math
from statistics import mean, stdev


def load_dataset(filepath):
    with open(filepath, newline="") as file:
        return list(csv.DictReader(file))


def to_float(value):
    if value == "":
        return None

    return float(value)


def future_return(mid_prices, index, horizon):
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


def build_microprice_data(
    rows,
    horizon,
):
    mid_prices = [
        to_float(row["mid_price"])
        for row in rows
    ]

    data = []

    for i, row in enumerate(rows):
        microprice = to_float(
            row["microprice"]
        )

        mid_price = to_float(
            row["mid_price"]
        )

        if (
            microprice is None
            or mid_price is None
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
            microprice - mid_price
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


def confidence_interval_95(values):
    n = len(values)

    if n < 2:
        return None

    average = mean(values)
    standard_deviation = stdev(values)

    standard_error = (
        standard_deviation
        / math.sqrt(n)
    )

    margin = (
        1.96
        * standard_error
    )

    return (
        average - margin,
        average + margin,
    )


def analyze_bucket(
    bucket,
    bucket_number,
):
    signals = [
        item[0]
        for item in bucket
    ]

    returns = [
        item[1]
        for item in bucket
    ]

    average_signal = mean(signals)
    average_return = mean(returns)

    standard_deviation = stdev(
        returns
    )

    standard_error = (
        standard_deviation
        / math.sqrt(len(returns))
    )

    confidence_interval = (
        confidence_interval_95(
            returns
        )
    )

    print(
        f"Bucket {bucket_number}"
    )

    print(
        "  n:",
        len(returns),
    )

    print(
        "  avg signal:",
        average_signal,
    )

    print(
        "  avg return:",
        average_return,
    )

    print(
        "  std return:",
        standard_deviation,
    )

    print(
        "  standard error:",
        standard_error,
    )

    print(
        "  95% CI:",
        confidence_interval,
    )

    print()


def compare_extreme_buckets(
    bucket_1,
    bucket_5,
):
    returns_1 = [
        item[1]
        for item in bucket_1
    ]

    returns_5 = [
        item[1]
        for item in bucket_5
    ]

    mean_1 = mean(returns_1)
    mean_5 = mean(returns_5)

    difference = (
        mean_5 - mean_1
    )

    print(
        "=== BUCKET 1 vs BUCKET 5 ==="
    )

    print(
        "Bucket 1 mean:",
        mean_1,
    )

    print(
        "Bucket 5 mean:",
        mean_5,
    )

    print(
        "Difference:",
        difference,
    )

    print()


def analyze_dataset(filepath):
    rows = load_dataset(filepath)

    horizon = 10

    data = build_microprice_data(
        rows,
        horizon,
    )

    buckets = create_quantile_buckets(
        data,
        num_buckets=5,
    )

    print(
        "=== STATISTICAL ANALYSIS ==="
    )

    print(
        f"Signal: microprice deviation"
    )

    print(
        f"Horizon: {horizon} events"
    )

    print()

    for i, bucket in enumerate(
        buckets,
        start=1,
    ):
        analyze_bucket(
            bucket,
            i,
        )

    print(
        "=== EXTREME BUCKET COMPARISON ==="
    )

    compare_extreme_buckets(
        buckets[0],
        buckets[-1],
    )


if __name__ == "__main__":
    analyze_dataset(
        "data/market_states.csv"
    )