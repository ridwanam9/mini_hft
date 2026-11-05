
from statistics import mean, median, pstdev

from src.simulation import Simulation
from src.order_lifetime_analyzer import OrderLifetimeAnalyzer


NUM_SUBMISSIONS = 10_000
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

    sim.run_until_submissions(NUM_SUBMISSIONS)

    analyzer = OrderLifetimeAnalyzer(
        order_history=sim.book.order_history,
        end_time=sim.market.timestamp,
        time_step=sim.market.time_step,
    )

    result = analyzer.analyze()

    return {
        "seed": seed,
        "policy": policy,
        **{
            key: value
            for key, value in result.items()
            if key != "observations"
        },
    }


def print_summary(policy, results):
    print("\n" + "=" * 80)
    print(f"POLICY: {policy.upper()} | {len(results)} SEEDS")
    print("=" * 80)

    metrics = [
        ("Resting orders", "total_resting_orders"),
        ("Filled orders", "filled"),
        ("Cancelled orders", "cancelled"),
        ("Active at end", "active"),
        ("Average lifetime", "average_lifetime"),
        ("Median lifetime", "median_lifetime"),
        ("Average filled lifetime", "average_filled_lifetime"),
        ("Median filled lifetime", "median_filled_lifetime"),
        ("Average cancellation age", "average_cancellation_age"),
        ("Median cancellation age", "median_cancellation_age"),
        ("Average first fill age", "average_first_fill_age"),
        ("Median first fill age", "median_first_fill_age"),
    ]

    print(f"{'Metric':32s} {'Mean':>12s} {'Std dev':>12s}")

    for label, key in metrics:
        values = [
            result[key]
            for result in results
            if result[key] is not None
        ]

        if not values:
            print(f"{label:32s} {'N/A':>12s} {'N/A':>12s}")
            continue

        print(
            f"{label:32s} "
            f"{mean(values):12.2f} "
            f"{pstdev(values):12.2f}"
        )

    print("\nKaplan-Meier Survival Rate")

    for horizon in [10, 50, 100, 500]:
        values = [
            result["survival"][horizon]
            for result in results
            if result["survival"][horizon] is not None
        ]

        if values:
            print(
                f"After {horizon:3d} events: "
                f"{mean(values) * 100:.2f}% "
                f"(std: {pstdev(values) * 100:.2f}%)"
            )
        else:
            print(f"After {horizon:3d} events: N/A")


def main():
    all_results = {}

    for scenario in SCENARIOS:
        policy = scenario["policy"]

        results = [
            audit(seed=seed, policy=policy)
            for seed in SEEDS
        ]

        all_results[policy] = results

        print("\n" + "#" * 80)
        print(f"POLICY: {scenario['name']}")
        print("#" * 80)

        for result in results:
            print(
                f"Seed {result['seed']:4d} | "
                f"Resting: {result['total_resting_orders']:5d} | "
                f"Filled: {result['filled']:5d} | "
                f"Cancelled: {result['cancelled']:5d} | "
                f"Active: {result['active']:5d}"
            )

        print_summary(policy, results)

    print("\n" + "#" * 80)
    print("PHASE 20.7 COMPLETE: ORDER LIFETIME ANALYSIS")
    print("#" * 80)

    return all_results


if __name__ == "__main__":
    main()
