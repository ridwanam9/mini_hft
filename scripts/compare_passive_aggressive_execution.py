
from statistics import mean, pstdev

from src.simulation import Simulation
from src.passive_aggressive_execution_analyzer import (
    PassiveAggressiveExecutionAnalyzer,
)


NUM_SUBMISSIONS = 10_000
SEEDS = [42, 123, 456, 789, 2026]
CANCELLATION_PROBABILITY = 0.10

POLICIES = ["none", "random", "distance"]


def run_experiment(policy, seed):
    simulation = Simulation(
        seed=seed,
        cancellation_probability=CANCELLATION_PROBABILITY,
        cancellation_policy=policy,
    )

    simulation.run_until_submissions(NUM_SUBMISSIONS)

    # Audit status order
    from collections import Counter

    status_counts = Counter(
        record.get("status")
        for record in simulation.book.order_history.values()
    )

    print("Status distribution:", status_counts)
    print(
        "Total history records:",
        len(simulation.book.order_history),
    )

    analyzer = PassiveAggressiveExecutionAnalyzer(
        simulation.book.order_history
    )

    return analyzer.analyze()


def summarize_results(results, metric):
    values = [
        result["overall"][metric]
        for result in results
        if result["overall"][metric] is not None
    ]

    if not values:
        return None, None

    return mean(values), pstdev(values)


def print_metric(label, results, metric, percentage=False):
    avg, std = summarize_results(results, metric)

    if avg is None:
        print(f"{label:<38} N/A")
        return

    if percentage:
        print(
            f"{label:<38} "
            f"{avg * 100:>8.2f}% "
            f"{std * 100:>8.2f}%"
        )
    else:
        print(
            f"{label:<38} "
            f"{avg:>8.2f} "
            f"{std:>8.2f}"
        )


def main():
    all_results = {}

    for policy in POLICIES:
        print("\n" + "#" * 90)
        print(f"POLICY: {policy.upper()}")
        print("#" * 90)

        policy_results = []

        for seed in SEEDS:
            result = run_experiment(policy, seed)
            policy_results.append(result)

            overall = result["overall"]

            print(
                f"Seed {seed:>4} | "
                f"Orders: {result['total_orders']:>6} | "
                f"Completed: {result['completed_orders']:>6} | "
                f"Active: {result['active_orders']:>4} | "
                f"Aggressive: "
                f"{overall['aggressive_orders']:>5} | "
                f"Passive: "
                f"{overall['passive_orders']:>5} | "
                f"Consistent: "
                f"{overall['quantity_consistency']}"
            )

        all_results[policy] = policy_results

        print("\n" + "=" * 90)
        print(f"EXECUTION ANALYSIS | POLICY: {policy.upper()}")
        print("=" * 90)

        print(f"{'Metric':<38} {'Mean':>10} {'Std dev':>10}")

        print_metric(
            "Total orders",
            policy_results,
            "total_orders",
        )

        print_metric(
            "Aggressive orders",
            policy_results,
            "aggressive_orders",
        )

        print_metric(
            "Passive orders",
            policy_results,
            "passive_orders",
        )

        print_metric(
            "Aggressive order rate",
            policy_results,
            "aggressive_order_rate",
            percentage=True,
        )

        print_metric(
            "Passive order rate",
            policy_results,
            "passive_order_rate",
            percentage=True,
        )

        print_metric(
            "Aggressive executed quantity",
            policy_results,
            "aggressive_executed_quantity",
        )

        print_metric(
            "Passive executed quantity",
            policy_results,
            "passive_executed_quantity",
        )

        print_metric(
            "Average aggressive fill ratio",
            policy_results,
            "average_aggressive_fill_ratio",
            percentage=True,
        )

        print_metric(
            "Average passive fill ratio",
            policy_results,
            "average_passive_fill_ratio",
            percentage=True,
        )

        consistency = all(
            result["overall"]["quantity_consistency"]
            for result in policy_results
        )

        print(f"\nQuantity consistency across seeds: {consistency}")

    print("\n" + "#" * 90)
    print("PHASE 20.9: PASSIVE VS AGGRESSIVE EXECUTION COMPLETE")
    print("#" * 90)


if __name__ == "__main__":
    main()
