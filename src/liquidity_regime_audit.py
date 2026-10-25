from src.market_data import OrderSide
from src.simulation import Simulation


def run_audit(num_events=10_000, seed=42):
    simulation = Simulation(seed=seed)

    regimes = {
        "both_present": [],
        "bid_empty": [],
        "ask_empty": [],
        "both_empty": [],
    }

    for _ in range(num_events):
        order = simulation.market.generate_order()

        book = simulation.book.snapshot()

        bids = book.bids
        asks = book.asks

        fair_value = simulation.market.fair_value

        bid_liquidity = sum(bids.values())
        ask_liquidity = sum(asks.values())

        best_bid = book.best_bid
        best_ask = book.best_ask

        if bids and asks:
            regime = "both_present"
        elif not bids and asks:
            regime = "bid_empty"
        elif bids and not asks:
            regime = "ask_empty"
        else:
            regime = "both_empty"

        spread = None

        if best_bid is not None and best_ask is not None:
            spread = best_ask - best_bid

        bid_distance = None
        ask_distance = None

        if best_bid is not None:
            bid_distance = abs(fair_value - best_bid)

        if best_ask is not None:
            ask_distance = abs(best_ask - fair_value)

        # Weighted average distance of all liquidity
        bid_weighted_distance = calculate_weighted_distance(
            bids,
            fair_value,
        )

        ask_weighted_distance = calculate_weighted_distance(
            asks,
            fair_value,
        )

        total_liquidity = bid_liquidity + ask_liquidity

        if total_liquidity > 0:
            obi = (
                bid_liquidity - ask_liquidity
            ) / total_liquidity
        else:
            obi = 0.0

        regimes[regime].append({
            "fair_value": fair_value,
            "bid_liquidity": bid_liquidity,
            "ask_liquidity": ask_liquidity,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "bid_distance": bid_distance,
            "ask_distance": ask_distance,
            "bid_weighted_distance": bid_weighted_distance,
            "ask_weighted_distance": ask_weighted_distance,
            "obi": obi,
        })

        simulation.engine.submit_order(order)

    print("=== LIQUIDITY REGIME AUDIT ===")

    for regime, records in regimes.items():
        print(f"\n--- {format_regime(regime)} ---")
        print_summary(records)


def calculate_weighted_distance(levels, fair_value):
    total_quantity = sum(levels.values())

    if total_quantity == 0:
        return None

    weighted_distance = sum(
        abs(price - fair_value) * quantity
        for price, quantity in levels.items()
    )

    return weighted_distance / total_quantity


def average(records, key):
    values = [
        r[key]
        for r in records
        if r[key] is not None
    ]

    if not values:
        return None

    return sum(values) / len(values)


def print_summary(records):
    print(f"events: {len(records)}")

    if not records:
        return

    metrics = [
        ("avg bid liquidity", "bid_liquidity"),
        ("avg ask liquidity", "ask_liquidity"),
        ("avg spread", "spread"),
        ("avg best bid distance", "bid_distance"),
        ("avg best ask distance", "ask_distance"),
        (
            "avg bid weighted distance",
            "bid_weighted_distance",
        ),
        (
            "avg ask weighted distance",
            "ask_weighted_distance",
        ),
        ("avg OBI", "obi"),
    ]

    for label, key in metrics:
        value = average(records, key)

        if value is None:
            print(f"{label}: N/A")
        else:
            print(f"{label}: {value:.6f}")


def format_regime(regime):
    names = {
        "both_present": "BOTH SIDES PRESENT",
        "bid_empty": "BID EMPTY",
        "ask_empty": "ASK EMPTY",
        "both_empty": "BOTH SIDES EMPTY",
    }

    return names[regime]


if __name__ == "__main__":
    run_audit()

    