import csv
from statistics import mean, stdev


def load_dataset(filepath):
    with open(filepath, newline="") as file:
        return list(csv.DictReader(file))


def to_float(value):
    if value == "":
        return None

    return float(value)


def analyze_dataset(filepath):
    rows = load_dataset(filepath)

    print("=== DATASET SUMMARY ===")

    print("Number of events:", len(rows))

    # -------------------------
    # Mid price
    # -------------------------

    mid_prices = [
        to_float(row["mid_price"])
        for row in rows
        if row["mid_price"] != ""
    ]

    if mid_prices:
        print("\n=== PRICE ===")

        print("First mid price:", mid_prices[0])
        print("Last mid price:", mid_prices[-1])
        print("Min mid price:", min(mid_prices))
        print("Max mid price:", max(mid_prices))
        print(
            "Unique mid prices:",
            len(set(mid_prices)),
        )

    # -------------------------
    # Spread
    # -------------------------

    spreads = [
        to_float(row["spread"])
        for row in rows
        if row["spread"] != ""
    ]

    if spreads:
        print("\n=== SPREAD ===")

        print("Average spread:", mean(spreads))
        print("Min spread:", min(spreads))
        print("Max spread:", max(spreads))

    # -------------------------
    # OBI
    # -------------------------

    obi = [
        float(row["obi"])
        for row in rows
    ]

    print("\n=== ORDER BOOK IMBALANCE ===")

    print("Mean OBI:", mean(obi))

    if len(obi) > 1:
        print("Std OBI:", stdev(obi))

    print("Min OBI:", min(obi))
    print("Max OBI:", max(obi))

    # -------------------------
    # OFI
    # -------------------------

    ofi = [
        float(row["ofi"])
        for row in rows
    ]

    print("\n=== ORDER FLOW IMBALANCE ===")

    print("Mean OFI:", mean(ofi))

    if len(ofi) > 1:
        print("Std OFI:", stdev(ofi))

    print("Min OFI:", min(ofi))
    print("Max OFI:", max(ofi))

    # -------------------------
    # Trades
    # -------------------------

    trades = [
        row
        for row in rows
        if row["last_trade_price"] != ""
    ]

    print("\n=== TRADES ===")

    print("Events with trades:", len(trades))

    buy_trades = sum(
        row["last_trade_aggressor"] == "BUY"
        for row in trades
    )

    sell_trades = sum(
        row["last_trade_aggressor"] == "SELL"
        for row in trades
    )

    print("BUY aggressor events:", buy_trades)
    print("SELL aggressor events:", sell_trades)

    # -------------------------
    # Mid-price changes
    # -------------------------

    price_changes = sum(
        current != previous
        for previous, current
        in zip(mid_prices, mid_prices[1:])
    )

    print("\n=== PRICE MOVEMENT ===")

    print(
        "Mid-price changes:",
        price_changes,
    )


if __name__ == "__main__":
    analyze_dataset(
        "data/market_states.csv"
    )


