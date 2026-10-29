from collections import Counter

from src.simulation import Simulation


NUM_EVENTS = 10_000
SEED = 42


def audit(probability):
    sim = Simulation(
        seed=SEED,
        cancellation_probability=probability,
    )
    states = sim.run(NUM_EVENTS)

    conditions = Counter()
    longest_empty_run = 0
    current_empty_run = 0

    for state in states:
        bid_exists = state.best_bid is not None
        ask_exists = state.best_ask is not None

        if bid_exists and ask_exists:
            condition = "BOTH_PRESENT"
            current_empty_run = 0
        elif bid_exists:
            condition = "ASK_EMPTY"
            current_empty_run += 1
        elif ask_exists:
            condition = "BID_EMPTY"
            current_empty_run += 1
        else:
            condition = "BOTH_EMPTY"
            current_empty_run += 1

        conditions[condition] += 1
        longest_empty_run = max(
            longest_empty_run,
            current_empty_run,
        )

    statuses = Counter(
        record["status"]
        for record in sim.book.order_history.values()
    )

    return {
        "probability": probability,
        "states": len(states),
        "submitted": len(sim.book.order_history),
        "trades": len(sim.engine.trade_tape),
        "statuses": statuses,
        "conditions": conditions,
        "longest_empty_run": longest_empty_run,
        "active_final": len(sim.book.order_index),
        "best_bid": sim.book.best_bid,
        "best_ask": sim.book.best_ask,
        "spread": sim.book.spread,
    }


results = [
    audit(0.0),
    audit(0.10),
]

for result in results:
    print("\n" + "=" * 55)
    print(
        "CANCELLATION PROBABILITY:",
        result["probability"],
    )
    print("=" * 55)

    print(f"Recorded states: {result['states']}")
    print(f"Submitted orders: {result['submitted']}")
    print(f"Trade records: {result['trades']}")
    print(f"Final active orders: {result['active_final']}")

    print("\nOrder lifecycle:")
    for status in ("filled", "active", "cancelled", "expired"):
        print(
            f"{status:10s}: "
            f"{result['statuses'][status]}"
        )

    print("\nBook conditions:")
    for condition in (
        "BOTH_PRESENT",
        "BID_EMPTY",
        "ASK_EMPTY",
        "BOTH_EMPTY",
    ):
        count = result["conditions"][condition]
        print(
            f"{condition:15s}: "
            f"{count:5d} ({count / result['states']:.2%})"
        )

    print(
        "\nLongest consecutive non-two-sided run:",
        result["longest_empty_run"],
    )
    print("Final best bid:", result["best_bid"])
    print("Final best ask:", result["best_ask"])
    print("Final spread:", result["spread"])
