from statistics import mean, pstdev

from src.simulation import Simulation
from src.order_execution_analyzer import OrderExecutionAnalyzer


NUM_SUBMISSIONS = 10_000
SEEDS = [42, 123, 456, 789, 2026]
CANCELLATION_PROBABILITY = 0.10

SCENARIOS = [
    {"name": "NONE", "policy": "none"},
    {"name": "RANDOM", "policy": "random"},
    {"name": "DISTANCE", "policy": "distance"},
]


METRICS = [
    ("Resting orders", "total_resting_orders"),
    ("Completed orders", "completed_orders"),
    ("Active orders", "active_orders"),
    ("Fully filled", "fully_filled"),
    ("Partially filled", "partially_filled"),
    ("No-fill cancelled", "no_fill_cancelled"),
    ("Any filled", "any_filled"),
    ("Any-fill rate", "any_fill_rate"),
    ("Full-fill rate", "full_fill_rate"),
    ("Partial-fill rate", "partial_fill_rate"),
    ("No-fill cancellation rate", "no_fill_cancellation_rate"),
    ("Average fill ratio (completed)", "average_fill_ratio_completed"),
    ("Average fill ratio (all)", "average_fill_ratio_all"),
    ("Average first fill age", "average_first_fill_age"),
    ("Median first fill age", "median_first_fill_age"),
]


def audit(seed, policy):
    sim = Simulation(
        seed=seed,
        cancellation_probability=CANCELLATION_PROBABILITY,
        cancellation_policy=policy,
    )

    sim.run_until_submissions(NUM_SUBMISSIONS)

    analyzer = OrderExecutionAnalyzer(
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


def format_metric(value, is_rate=False):
    if value is None:
        return "N/A"

    if is_rate:
        return f"{value * 100:.2f}%"

    return f"{value:.2f}"


def print_summary(policy, results):
    print("\n" + "=" * 90)
    print(f"EXECUTION QUALITY | POLICY: {policy.upper()}")
    print("=" * 90)

    print(
        f"{'Metric':38s}"
        f"{'Mean':>16s}"
        f"{'Std dev':>16s}"
    )

    rate_metrics = {
        "any_fill_rate",
        "full_fill_rate",
        "partial_fill_rate",
        "no_fill_cancellation_rate",
    }

    for label, key in METRICS:
        values = [
            result[key]
            for result in results
            if result[key] is not None
        ]

        if not values:
            print(
                f"{label:38s}"
                f"{'N/A':>16s}"
                f"{'N/A':>16s}"
            )
            continue

        average_value = mean(values)
        std_value = pstdev(values)

        is_rate = key in rate_metrics

        print(
            f"{label:38s}"
            f"{format_metric(average_value, is_rate):>16s}"
            f"{format_metric(std_value, is_rate):>16s}"
        )


def main():
    all_results = {}

    for scenario in SCENARIOS:
        policy = scenario["policy"]

        results = [
            audit(seed=seed, policy=policy)
            for seed in SEEDS
        ]

        all_results[policy] = results

        print("\n" + "#" * 90)
        print(f"POLICY: {scenario['name']}")
        print("#" * 90)

        for result in results:
            print(
                f"Seed {result['seed']:4d} | "
                f"Resting: {result['total_resting_orders']:5d} | "
                f"Completed: {result['completed_orders']:5d} | "
                f"Filled: {result['fully_filled']:5d} | "
                f"Partial: {result['partially_filled']:5d} | "
                f"No-fill cancel: {result['no_fill_cancelled']:5d} | "
                f"Active: {result['active_orders']:5d}"
            )

        print_summary(policy, results)

    print("\n" + "#" * 90)
    print("PHASE 20.8 COMPLETE: ORDER EXECUTION QUALITY ANALYSIS")
    print("#" * 90)

    return all_results


if __name__ == "__main__":
    main()