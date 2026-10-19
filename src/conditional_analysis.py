import csv
from statistics import mean


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


def build_signal_returns(
    rows,
    signal_name,
    horizon,
):
    mid_prices = [
        to_float(row["mid_price"])
        for row in rows
    ]

    data = []

    for i, row in enumerate(rows):
        signal = to_float(
            row[signal_name]
        )

        if signal is None:
            continue

        future = future_return(
            mid_prices,
            i,
            horizon,
        )

        if future is None:
            continue

        data.append(
            (signal, future)
        )

    return data


def build_microprice_deviation(
    rows,
):
    derived_rows = []

    for row in rows:
        copied = dict(row)

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
            copied["microprice_deviation"] = ""
        else:
            copied["microprice_deviation"] = (
                str(microprice - mid_price)
            )

        derived_rows.append(copied)

    return derived_rows


def create_quantile_buckets(data, num_buckets=5):
    sorted_data = sorted(
        data,
        key=lambda x: x[0],
    )

    n = len(sorted_data)

    buckets = []

    for bucket_index in range(num_buckets):
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


def analyze_buckets(
    data,
    signal_name,
    horizon,
):
    print(
        f"{signal_name} "
        f"→ {horizon}-event return"
    )

    if not data:
        print("  no valid observations")
        print()
        return

    buckets = create_quantile_buckets(
        data,
        num_buckets=5,
    )

    for i, bucket in enumerate(
        buckets,
        start=1,
    ):
        signals = [
            item[0]
            for item in bucket
        ]

        returns = [
            item[1]
            for item in bucket
        ]

        positive_rate = (
            sum(
                return_value > 0
                for return_value in returns
            )
            / len(returns)
        )

        print(
            f"  Bucket {i}:"
        )

        print(
            "    n:",
            len(bucket),
        )

        print(
            "    avg signal:",
            mean(signals),
        )

        print(
            "    avg future return:",
            mean(returns),
        )

        print(
            "    positive rate:",
            positive_rate,
        )

        print(
            "    min return:",
            min(returns),
        )

        print(
            "    max return:",
            max(returns),
        )

    print()


def analyze_dataset(filepath):
    rows = load_dataset(filepath)

    print("=== CONDITIONAL ANALYSIS ===")
    print()

    derived_rows = (
        build_microprice_deviation(rows)
    )

    signals = [
        "obi",
        "ofi",
        "microprice_deviation",
    ]

    for horizon in [1, 5, 10]:
        print(
            f"--- Horizon: {horizon} events ---"
        )

        for signal_name in signals:

            data = build_signal_returns(
                derived_rows,
                signal_name,
                horizon,
            )

            analyze_buckets(
                data,
                signal_name,
                horizon,
            )


if __name__ == "__main__":
    analyze_dataset(
        "data/market_states.csv"
    )