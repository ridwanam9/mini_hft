from statistics import mean, pstdev

from src.simulation import Simulation
from src.execution_cost_analyzer import ExecutionCostAnalyzer
from src.order_book_state_analyzer import OrderBookStateAnalyzer
from src.spread_cost_analyzer import SpreadCostAnalyzer


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

    trade_tape = simulation.engine.trade_tape

    # Execution cost analysis
    analyzer = ExecutionCostAnalyzer(trade_tape)
    result = analyzer.analyze()

    # Order book state analysis
    state_analyzer = OrderBookStateAnalyzer(trade_tape)
    state_result = state_analyzer.analyze()

    # Spread cost decomposition
    spread_analyzer = SpreadCostAnalyzer(trade_tape)
    spread_result = spread_analyzer.analyze()

    # Trade coverage
    missing_buy = sum(
        trade.aggressor == "BUY"
        and trade.arrival_mid_price is None
        for trade in trade_tape
    )

    missing_sell = sum(
        trade.aggressor == "SELL"
        and trade.arrival_mid_price is None
        for trade in trade_tape
    )

    valid_buy = sum(
        trade.aggressor == "BUY"
        and trade.arrival_mid_price is not None
        for trade in trade_tape
    )

    valid_sell = sum(
        trade.aggressor == "SELL"
        and trade.arrival_mid_price is not None
        for trade in trade_tape
    )

    valid_quantity = sum(
        trade.quantity
        for trade in trade_tape
        if trade.arrival_mid_price is not None
    )

    missing_quantity = sum(
        trade.quantity
        for trade in trade_tape
        if trade.arrival_mid_price is None
    )

    total_trade_quantity = sum(
        trade.quantity
        for trade in trade_tape
    )

    raw_trade_count = len(trade_tape)
    analyzed_trade_count = result["total_trades"]

    # Coverage rates
    valid_trade_rate = (
        analyzed_trade_count / raw_trade_count
        if raw_trade_count > 0
        else 0
    )

    missing_trade_rate = (
        1 - valid_trade_rate
    )

    valid_quantity_rate = (
        valid_quantity / total_trade_quantity
        if total_trade_quantity > 0
        else 0
    )

    missing_quantity_rate = (
        missing_quantity / total_trade_quantity
        if total_trade_quantity > 0
        else 0
    )

    total_buy_trades = valid_buy + missing_buy
    total_sell_trades = valid_sell + missing_sell

    valid_buy_rate = (
        valid_buy / total_buy_trades
        if total_buy_trades > 0
        else 0
    )

    valid_sell_rate = (
        valid_sell / total_sell_trades
        if total_sell_trades > 0
        else 0
    )

    # Consistency checks
    if state_result["total_trades"] != raw_trade_count:
        raise AssertionError(
            "Order book state trade count mismatch"
        )

    if state_result["total_quantity"] != total_trade_quantity:
        raise AssertionError(
            "Order book state quantity mismatch"
        )

    if spread_result["overall"]["trade_count"] != analyzed_trade_count:
        raise AssertionError(
            "Spread cost and execution cost trade count mismatch"
        )

    if spread_result["skipped_count"] != (
        raw_trade_count - analyzed_trade_count
    ):
        raise AssertionError(
            "Spread cost skipped trade count mismatch"
        )

    if (
        state_result["TWO_SIDED"]["trade_count"]
        != analyzed_trade_count
    ):
        raise AssertionError(
            "Two-sided trade count does not match analyzed trades"
        )

    if (
        state_result["TWO_SIDED"]["total_quantity"]
        != valid_quantity
    ):
        raise AssertionError(
            "Two-sided quantity does not match valid quantity"
        )

    return {
        "result": result,
        "state_result": state_result,
        "spread_result": spread_result,
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
        "valid_trade_rate": valid_trade_rate,
        "missing_trade_rate": missing_trade_rate,
        "valid_quantity_rate": valid_quantity_rate,
        "missing_quantity_rate": missing_quantity_rate,
        "valid_buy_rate": valid_buy_rate,
        "valid_sell_rate": valid_sell_rate,
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


def summarize_spread_results(results, metric_path, aggressor=None):
    values = []

    for item in results:
        spread_result = item["spread_result"]

        if aggressor is None:
            value = spread_result["overall"]
        else:
            value = spread_result["by_aggressor"].get(aggressor)

        if value is None:
            continue

        for key in metric_path:
            value = value.get(key)

            if value is None:
                break

        if value is not None:
            values.append(value)

    if not values:
        return None, None

    return mean(values), pstdev(values)


def print_metric(label, results, metric_path):
    avg, std = summarize_results(results, metric_path)

    if avg is None:
        print(f"{label:<48} N/A")
        return

    print(
        f"{label:<48} "
        f"{avg:>12.4f} "
        f"{std:>12.4f}"
    )


def print_spread_metric(
    label,
    results,
    metric_path,
    aggressor=None,
):
    avg, std = summarize_spread_results(
        results,
        metric_path,
        aggressor,
    )

    if avg is None:
        print(f"{label:<48} N/A")
        return

    print(
        f"{label:<48} "
        f"{avg:>12.4f} "
        f"{std:>12.4f}"
    )


def print_spread_decomposition(results):
    print("\nSPREAD COST DECOMPOSITION")
    print("-" * 75)

    print(
        f"{'Metric':<48} "
        f"{'Mean':>12} "
        f"{'Std dev':>12}"
    )

    print("\nOVERALL COST")
    print("-" * 75)

    print_spread_metric(
        "Average half-spread cost",
        results,
        ("average_total_half_spread_cost",),
    )

    print_spread_metric(
        "Average beyond-touch cost",
        results,
        ("average_total_beyond_touch_cost",),
    )

    print_spread_metric(
        "Average total execution cost",
        results,
        ("average_total_cost",),
    )

    print("\nOVERALL COST (BPS)")
    print("-" * 75)

    print_spread_metric(
        "Average half-spread cost (bps)",
        results,
        ("average_total_half_spread_bps",),
    )

    print_spread_metric(
        "Average beyond-touch cost (bps)",
        results,
        ("average_total_beyond_touch_bps",),
    )

    print_spread_metric(
        "Average total execution cost (bps)",
        results,
        ("average_total_cost_bps",),
    )

    print("\nQUANTITY-WEIGHTED COST")
    print("-" * 75)

    print_spread_metric(
        "Quantity-weighted half-spread cost",
        results,
        ("quantity_weighted_half_spread_cost",),
    )

    print_spread_metric(
        "Quantity-weighted beyond-touch cost",
        results,
        ("quantity_weighted_beyond_touch_cost",),
    )

    print_spread_metric(
        "Quantity-weighted total execution cost",
        results,
        ("quantity_weighted_cost",),
    )

    print("\nQUANTITY-WEIGHTED COST (BPS)")
    print("-" * 75)

    print_spread_metric(
        "Quantity-weighted half-spread cost (bps)",
        results,
        ("quantity_weighted_half_spread_bps",),
    )

    print_spread_metric(
        "Quantity-weighted beyond-touch cost (bps)",
        results,
        ("quantity_weighted_beyond_touch_bps",),
    )

    print_spread_metric(
        "Quantity-weighted total execution cost (bps)",
        results,
        ("quantity_weighted_cost_bps",),
    )

    for aggressor in ["BUY", "SELL"]:
        print(f"\n{aggressor} AGGRESSOR DECOMPOSITION")
        print("-" * 75)

        print_spread_metric(
            f"{aggressor} half-spread cost (bps)",
            results,
            ("average_total_half_spread_bps",),
            aggressor,
        )

        print_spread_metric(
            f"{aggressor} beyond-touch cost (bps)",
            results,
            ("average_total_beyond_touch_bps",),
            aggressor,
        )

        print_spread_metric(
            f"{aggressor} total execution cost (bps)",
            results,
            ("average_total_cost_bps",),
            aggressor,
        )

        print_spread_metric(
            f"{aggressor} quantity-weighted total cost (bps)",
            results,
            ("quantity_weighted_cost_bps",),
            aggressor,
        )

def print_coverage_summary(results):
    print("\nEXECUTION COST DATA COVERAGE ANALYSIS")
    print("-" * 85)

    print(
        f"{'Coverage metric':<42} "
        f"{'Mean':>12} "
        f"{'Std dev':>12}"
    )

    metrics = [
        ("Valid trade coverage", "valid_trade_rate"),
        ("Missing trade coverage", "missing_trade_rate"),
        ("Valid quantity coverage", "valid_quantity_rate"),
        ("Missing quantity coverage", "missing_quantity_rate"),
        ("BUY valid coverage", "valid_buy_rate"),
        ("SELL valid coverage", "valid_sell_rate"),
    ]

    for label, key in metrics:
        values = [item[key] for item in results]

        avg = mean(values)
        std = pstdev(values)

        print(
            f"{label:<42} "
            f"{avg:>11.2%} "
            f"{std:>11.2%}"
        )

    print("\nORDER BOOK STATE DISTRIBUTION")
    print("-" * 85)

    print(
        f"{'State':<20} "
        f"{'Trade share':>15} "
        f"{'Quantity share':>20}"
    )

    categories = ["TWO_SIDED", "ASK_ONLY", "BID_ONLY", "EMPTY",]

    for category in categories:
        trade_shares = []
        quantity_shares = []

        for item in results:
            state = item["state_result"][category]

            raw_count = item["raw_trade_count"]
            total_quantity = item["total_trade_quantity"]

            trade_share = (
                state["trade_count"] / raw_count
                if raw_count > 0
                else 0
            )

            quantity_share = (
                state["total_quantity"] / total_quantity
                if total_quantity > 0
                else 0
            )

            trade_shares.append(trade_share)
            quantity_shares.append(quantity_share)

        print(
            f"{category:<20} "
            f"{mean(trade_shares):>14.2%} "
            f"{mean(quantity_shares):>19.2%}"
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

            for category in [
                "TWO_SIDED",
                "ASK_ONLY",
                "BID_ONLY",
                "EMPTY",
            ]:
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
            f"{'Metric':<48} "
            f"{'Mean':>12} "
            f"{'Std dev':>12}"
        )

        print_metric(
            "Analyzed trades",
            policy_results,
            ("total_trades",),
        )

        print_metric(
            "Analyzed executed quantity",
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
        print("-" * 75)

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
        print("-" * 75)

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

        # New: spread cost decomposition
        print_spread_decomposition(policy_results)
        print_coverage_summary(policy_results)

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
        print("-" * 75)
        print(f"Raw trades:       {total_raw}")
        print(f"Analyzed trades:  {total_analyzed}")
        print(f"Skipped trades:   {total_skipped}")

    print("\n" + "#" * 95)
    print("PHASE 20.10: EXECUTION COST EXPERIMENT COMPLETE")
    print("#" * 95)


if __name__ == "__main__":
    main()
