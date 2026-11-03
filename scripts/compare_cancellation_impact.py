
from collections import Counter
from statistics import mean, pstdev

from src.simulation import Simulation


NUM_EVENTS = 10_000
SEEDS = [42, 123, 456, 789, 2026]
CANCELLATION_PROBABILITY = 0.10

SCENARIOS = [
    {"name": "NONE", "policy": "none"},
    {"name": "RANDOM", "policy": "random"},
    {"name": "DISTANCE", "policy": "distance"},
]


def audit(seed, policy):
    sim = Simulation(
        seed=seed,
        cancellation_probability=CANCELLATION_PROBABILITY,
        cancellation_policy=policy,
    )
    states = sim.run_until_submissions(NUM_EVENTS)

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

    total_states = len(states)

    total_events = total_states

    trades_per_event = (
        len(sim.engine.trade_tape) / total_events
        if total_events else 0.0
    )

    filled_per_event = (
        statuses["filled"] / total_events
        if total_events else 0.0
    )

    cancellations_per_event = (
        statuses["cancelled"] / total_events
        if total_events else 0.0
    )

    return {
        "seed": seed,
        "policy": policy,
        "states": total_states,
        "submitted": len(sim.book.order_history),
        "trades": len(sim.engine.trade_tape),
        "filled": statuses["filled"],
        "active": statuses["active"],
        "cancelled": statuses["cancelled"],
        "expired": statuses["expired"],
        "both_present_pct": (
            100 * conditions["BOTH_PRESENT"] / total_states
            if total_states else 0.0
        ),
        "bid_empty_pct": (
            100 * conditions["BID_EMPTY"] / total_states
            if total_states else 0.0
        ),
        "ask_empty_pct": (
            100 * conditions["ASK_EMPTY"] / total_states
            if total_states else 0.0
        ),
        "both_empty_pct": (
            100 * conditions["BOTH_EMPTY"] / total_states
            if total_states else 0.0
        ),
        "longest_empty_run": longest_empty_run,
        "final_no_bid": sim.book.best_bid is None,
        "final_no_ask": sim.book.best_ask is None,
        "final_spread": sim.book.spread,
        "total_events": total_events,
        "trades_per_event": trades_per_event,
        "filled_per_event": filled_per_event,
        "cancellations_per_event": cancellations_per_event,
    }


def print_summary(policy, results):
    print("\n" + "=" * 76)
    print(f"POLICY: {policy.upper()} | {len(results)} SEEDS")
    print("=" * 76)

    metrics = [
        ("Total events", "total_events"),
        ("Submitted orders", "submitted"),
        ("Trade records", "trades"),
        ("Filled orders", "filled"),
        ("Cancelled orders", "cancelled"),
        ("Expired orders", "expired"),
        ("Trades per event", "trades_per_event"),
        ("Filled per event", "filled_per_event"),
        ("Cancellations per event", "cancellations_per_event"),
        ("BOTH_PRESENT (%)", "both_present_pct"),
        ("BID_EMPTY (%)", "bid_empty_pct"),
        ("ASK_EMPTY (%)", "ask_empty_pct"),
        ("BOTH_EMPTY (%)", "both_empty_pct"),
        ("Longest non-two-sided run", "longest_empty_run"),
    ]

    print(f"{'Metric':30s} {'Mean':>12s} {'Std dev':>12s}")

    for label, key in metrics:
        values = [result[key] for result in results]
        print(
            f"{label:30s} "
            f"{mean(values):12.2f} "
            f"{pstdev(values):12.2f}"
        )

    no_bid_count = sum(r["final_no_bid"] for r in results)
    no_ask_count = sum(r["final_no_ask"] for r in results)

    print(
        f"\nFinal state without bid: "
        f"{no_bid_count}/{len(results)} seeds"
    )
    print(
        f"Final state without ask: "
        f"{no_ask_count}/{len(results)} seeds"
    )

    spreads = [
        result["final_spread"]
        for result in results
        if result["final_spread"] is not None
    ]

    if spreads:
        print(
            f"Mean final spread (available cases): "
            f"{mean(spreads):.5f}"
        )
    else:
        print("Mean final spread: unavailable in all seeds")


all_results = {}

for scenario in SCENARIOS:
    policy = scenario["policy"]
    results = [
        audit(seed=seed, policy=policy)
        for seed in SEEDS
    ]
    all_results[policy] = results

    print("\n" + "#" * 76)
    print(f"POLICY: {scenario['name']}")
    print("#" * 76)

    print(
        f"{'Seed':>6s} "
        f"{'Events':>10s} "
        f"{'Submitted':>10s} "
        f"{'Trades':>9s} "
        f"{'Cancelled':>10s} "
        f"{'Trades/Event':>12s} "
        f"{'Both (%)':>10s} "
        f"{'Empty (%)':>10s} "
        f"{'Longest':>9s} "
        f"{'No bid?':>8s} "
        f"{'No ask?':>8s}"
    )

    for result in results:
        print(
            f"{result['seed']:6d} "
            f"{result['total_events']:10d} "
            f"{result['submitted']:10d} "
            f"{result['trades']:9d} "
            f"{result['cancelled']:10d} "
            f"{result['trades_per_event']:12.4f} "
            f"{result['both_present_pct']:10.2f} "
            f"{result['both_empty_pct']:10.2f} "
            f"{result['longest_empty_run']:9d} "
            f"{str(result['final_no_bid']):>8s} "
            f"{str(result['final_no_ask']):>8s}"
        )

    print_summary(policy, results)


print("\n" + "#" * 76)
print("PHASE 20.5.8 COMPLETE: MULTI-SEED COMPARISON")
print("#" * 76)
