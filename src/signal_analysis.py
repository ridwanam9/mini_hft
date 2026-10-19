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



def correlation(x, y):
    if len(x) < 2:
        return 0.0

    x_mean = mean(x)
    y_mean = mean(y)

    numerator = sum(
        (a - x_mean) * (b - y_mean)
        for a, b in zip(x, y)
    )

    x_variance = sum(
        (a - x_mean) ** 2
        for a in x
    )

    y_variance = sum(
        (b - y_mean) ** 2
        for b in y
    )

    denominator = (
        x_variance * y_variance
    ) ** 0.5

    if denominator == 0:
        return 0.0

    return numerator / denominator


def analyze_signal(rows, signal_name, horizon):
    signals = []
    returns = []

    mid_prices = [
        to_float(row["mid_price"])
        for row in rows
    ]

    for i, row in enumerate(rows):
        signal = to_float(row[signal_name])

        if signal is None:
            continue

        future = future_return(
            mid_prices,
            i,
            horizon,
        )

        if future is None:
            continue

        signals.append(signal)
        returns.append(future)

    print(
        f"{signal_name} "
        f"→ {horizon}-event return"
    )

    print(
        "  observations:",
        len(signals),
    )

    if not returns:
        print("  no valid observations")
        print()
        return

    corr = correlation(
        signals,
        returns,
    )

    print(
        "  correlation:",
        corr,
    )

    print(
        "  mean return:",
        mean(returns),
    )

    print()
    


def analyze_dataset(filepath):
    rows = load_dataset(filepath)

    print("=== SIGNAL ANALYSIS ===")
    print()

    for horizon in [1, 5, 10]:

        print(
            f"--- Horizon: {horizon} events ---"
        )

        analyze_signal(
            rows,
            "obi",
            horizon,
        )

        analyze_signal(
            rows,
            "ofi",
            horizon,
        )

        # microprice deviation
        deviations = []

        for row in rows:
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
                deviations.append(None)
            else:
                deviations.append(
                    microprice - mid_price
                )

        # Temporarily add the derived signal
        derived_rows = []

        for row, deviation in zip(
            rows,
            deviations,
        ):
            copied = dict(row)

            copied["microprice_deviation"] = (
                ""
                if deviation is None
                else str(deviation)
            )

            derived_rows.append(copied)

        analyze_signal(
            derived_rows,
            "microprice_deviation",
            horizon,
        )


if __name__ == "__main__":
    analyze_dataset(
        "data/market_states.csv"
    )

