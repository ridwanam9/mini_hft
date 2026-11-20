
from statistics import mean, pstdev

from src.simulation import Simulation
from src.execution_cost_analyzer import ExecutionCostAnalyzer
from src.order_book_state_analyzer import OrderBookStateAnalyzer

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

    analyzer = ExecutionCostAnalyzer(
        simulation.engine.trade_tape
    )

    result = analyzer.analyze()

    state_analyzer = OrderBookStateAnalyzer(
        simulation.engine.trade_tape
    )

    state_result = state_analyzer.analyze()

    missing_buy = sum(
        trade.aggressor == "BUY"
        and trade.arrival_mid_price is None
        for trade in simulation.engine.trade_tape
    )

    missing_sell = sum(
        trade.aggressor == "SELL"
        and trade.arrival_mid_price is None
        for trade in simulation.engine.trade_tape
    )

    valid_buy = sum(
        trade.aggressor == "BUY"
        and trade.arrival_mid_price is not None
        for trade in simulation.engine.trade_tape
    )

    valid_sell = sum(
        trade.aggressor == "SELL"
        and trade.arrival_mid_price is not None
        for trade in simulation.engine.trade_tape
    )

    valid_quantity = sum(
        trade.quantity
        for trade in simulation.engine.trade_tape
        if trade.arrival_mid_price is not None
    )

    missing_quantity = sum(
        trade.quantity
        for trade in simulation.engine.trade_tape
        if trade.arrival_mid_price is None
    )

    total_trade_quantity = sum(
        trade.quantity
        for trade in simulation.engine.trade_tape
    )

    raw_trade_count = len(simulation.engine.trade_tape)
    analyzed_trade_count = result["total_trades"]

    if state_result["total_trades"] != raw_trade_count:
        raise AssertionError("Order book state trade count mismatch")

    if state_result["total_quantity"] != total_trade_quantity:
        raise AssertionError("Order book state quantity mismatch")

    return {
        "result": result,
        "state_result": state_result,
        "raw_trade_count": raw_trade_count,
        "analyzed_trade_count": analyzed_trade_count,
        "skipped_trade_count": (
            raw_trade_count - analyzed_trade_count
        ),
        "missing_buy": missing_buy,
        "missing_sell": missing_sell,
        "valid_buy": valid_buy,
        "valid_sell": valid_sell,
        "valid_quantity": valid_quantity,
        "missing_quantity": missing_quantity,
        "total_trade_quantity": total_trade_quantity,
    }


def summarize_results(results, metric_path):
    values = []

    for item in results:
        value = item["result"]

        for key in metric_path:
            value = value[key]

        if value is not None:
            values.append(value)

    if not values:
        return None, None

    return mean(values), pstdev(values)


def print_metric(label, results, metric_path):
    avg, std = summarize_results(results, metric_path)

    if avg is None:
        print(f"{label:<42} N/A")
        return

    print(
        f"{label:<42} "
        f"{avg:>10.4f} "
        f"{std:>10.4f}"
    )


def main():
    for policy in POLICIES:
        print("\n" + "#" * 95)
        print(f"EXECUTION COST EXPERIMENT: {policy.upper()}")
        print("#" * 95)

        policy_results = []

        for seed in SEEDS:
            experiment = run_experiment(policy, seed)
            policy_results.append(experiment)

            result = experiment["result"]

            state_result = experiment["state_result"]

            print("\n         ORDER BOOK STATE")

            for category in ["TWO_SIDED", "ASK_ONLY", "BID_ONLY", "EMPTY"]:
                state = state_result[category]

                print(
                    f"         {category:<12} | "
                    f"Trades: {state['trade_count']:>5} | "
                    f"Quantity: {state['total_quantity']:>8} | "
                    f"BUY: {state['buy_count']:>5} | "
                    f"SELL: {state['sell_count']:>5}"
                )

            print(
                f"Seed {seed:>4} | "
                f"Raw trades: {experiment['raw_trade_count']:>6} | "
                f"Analyzed: {experiment['analyzed_trade_count']:>6} | "
                f"Skipped: {experiment['skipped_trade_count']:>5} | "
                f"Valid Quantity: {result['total_quantity']:>8}"
            )
            print(
                f"         Valid BUY: {experiment['valid_buy']} | "
                f"Missing BUY: {experiment['missing_buy']}"
            )

            print(
                f"         Valid SELL: {experiment['valid_sell']} | "
                f"Missing SELL: {experiment['missing_sell']}"
            )

            missing_quantity_rate = (
                experiment["missing_quantity"]
                / experiment["total_trade_quantity"]
                if experiment["total_trade_quantity"] > 0
                else 0
            )

            print(
                f"         Valid qty: {experiment['valid_quantity']} | "
                f"Missing qty: {experiment['missing_quantity']} | "
                f"Missing rate: {missing_quantity_rate:.2%} | "
                f"Total qty: {experiment['total_trade_quantity']}"
            )

        print("\n" + "=" * 95)
        print(f"EXECUTION COST SUMMARY: {policy.upper()}")
        print("=" * 95)

        print(
            f"{'Metric':<42} "
            f"{'Mean':>10} "
            f"{'Std dev':>10}"
        )

        print_metric(
            "Analyzed trades",
            policy_results,
            ("total_trades",),
        )

        print_metric(
            "Total executed quantity",
            policy_results,
            ("total_quantity",),
        )

        print_metric(
            "Average execution cost",
            policy_results,
            ("average_execution_cost",),
        )

        print_metric(
            "Average execution cost (bps)",
            policy_results,
            ("average_execution_cost_bps",),
        )

        print_metric(
            "Quantity-weighted execution cost",
            policy_results,
            ("quantity_weighted_execution_cost",),
        )

        print_metric(
            "Quantity-weighted execution cost (bps)",
            policy_results,
            ("quantity_weighted_execution_cost_bps",),
        )

        print("\nBUY AGGRESSOR")
        print("-" * 65)

        print_metric(
            "BUY average cost (bps)",
            policy_results,
            ("buy", "average_execution_cost_bps"),
        )

        print_metric(
            "BUY quantity-weighted cost (bps)",
            policy_results,
            ("buy", "quantity_weighted_execution_cost_bps"),
        )

        print("\nSELL AGGRESSOR")
        print("-" * 65)

        print_metric(
            "SELL average cost (bps)",
            policy_results,
            ("sell", "average_execution_cost_bps"),
        )

        print_metric(
            "SELL quantity-weighted cost (bps)",
            policy_results,
            ("sell", "quantity_weighted_execution_cost_bps"),
        )

        total_raw = sum(
            item["raw_trade_count"]
            for item in policy_results
        )

        total_analyzed = sum(
            item["analyzed_trade_count"]
            for item in policy_results
        )

        total_skipped = sum(
            item["skipped_trade_count"]
            for item in policy_results
        )

        print("\nDATA COVERAGE")
        print("-" * 65)
        print(f"Raw trades:       {total_raw}")
        print(f"Analyzed trades:  {total_analyzed}")
        print(f"Skipped trades:   {total_skipped}")

    print("\n" + "#" * 95)
    print("PHASE 20.10: EXECUTION COST EXPERIMENT COMPLETE")
    print("#" * 95)


if __name__ == "__main__":
    main()
