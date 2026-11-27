from statistics import mean, pstdev

from src.simulation import Simulation
from src.execution_cost_analyzer import ExecutionCostAnalyzer
from src.order_book_state_analyzer import OrderBookStateAnalyzer
from src.spread_cost_analyzer import SpreadCostAnalyzer
from collections import defaultdict
from src.order_book_state_matching_analyzer import (
    OrderBookStateMatchingAnalyzer,
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

    trade_tape = simulation.engine.trade_tape

    spread_distribution = defaultdict(
        lambda: {
            "trade_count": 0,
            "total_quantity": 0,
            "total_cost_bps": 0.0,
            "quantity_weighted_cost_bps": 0.0,
        }
    )

    arrival_state_samples = {
        "spread": [],
        "bid_depth": [],
        "ask_depth": [],
        "obi": [],
    }

    arrival_state_observations = []

    for trade in trade_tape:
        if (
            trade.arrival_spread is not None
            and trade.arrival_bid_depth is not None
            and trade.arrival_ask_depth is not None
            and trade.arrival_obi is not None
        ):
            arrival_state_samples["spread"].append(
                trade.arrival_spread
            )
            arrival_state_samples["bid_depth"].append(
                trade.arrival_bid_depth
            )
            arrival_state_samples["ask_depth"].append(
                trade.arrival_ask_depth
            )
            arrival_state_samples["obi"].append(
                trade.arrival_obi
            )

        if (
            trade.arrival_best_bid is None
            or trade.arrival_best_ask is None
            or trade.arrival_mid_price is None
            or trade.arrival_spread is None
        ):
            continue

        mid_price = trade.arrival_mid_price

        if mid_price <= 0:
            continue

        if trade.aggressor == "BUY":
            execution_cost = trade.price - mid_price
        elif trade.aggressor == "SELL":
            execution_cost = mid_price - trade.price
        else:
            continue

        execution_cost_bps = (
            execution_cost / mid_price
        ) * 10_000

        if (
            trade.arrival_bid_depth is not None
            and trade.arrival_ask_depth is not None
            and trade.arrival_obi is not None
        ):
            arrival_state_observations.append({
                "policy": policy,
                "seed": seed,
                "spread": trade.arrival_spread,
                "bid_depth": trade.arrival_bid_depth,
                "ask_depth": trade.arrival_ask_depth,
                "obi": trade.arrival_obi,
                "aggressor": trade.aggressor,
                "execution_cost_bps": execution_cost_bps,
                "quantity": trade.quantity,
            })

        key = (
            round(trade.arrival_spread, 8),
            trade.aggressor,
        )

        spread_distribution[key]["trade_count"] += 1
        spread_distribution[key]["total_quantity"] += trade.quantity

        spread_distribution[key]["total_cost_bps"] += (
            execution_cost_bps
        )

        spread_distribution[key]["quantity_weighted_cost_bps"] += (
            execution_cost_bps * trade.quantity
        )


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
        "arrival_state_samples": arrival_state_samples,
        "valid_quantity": valid_quantity,
        "missing_quantity": missing_quantity,
        "total_trade_quantity": total_trade_quantity,
        "valid_trade_rate": valid_trade_rate,
        "missing_trade_rate": missing_trade_rate,
        "valid_quantity_rate": valid_quantity_rate,
        "missing_quantity_rate": missing_quantity_rate,
        "valid_buy_rate": valid_buy_rate,
        "valid_sell_rate": valid_sell_rate,
        "spread_distribution": dict(spread_distribution),
        "arrival_state_observations": arrival_state_observations,
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




def print_spread_distribution(all_results):
    print("\n" + "=" * 130)
    print("SPREAD-CONDITIONED EXECUTION COST")
    print("=" * 130)

    for policy, results in all_results.items():
        combined = defaultdict(
            lambda: {
                "trade_count": 0,
                "total_quantity": 0,
                "total_cost_bps": 0.0,
                "quantity_weighted_cost_bps": 0.0,
            }
        )

        # Combine results across all seeds
        for result in results:
            for (spread, aggressor), metrics in result[
                "spread_distribution"
            ].items():
                target = combined[(spread, aggressor)]

                target["trade_count"] += metrics["trade_count"]
                target["total_quantity"] += metrics["total_quantity"]

                target["total_cost_bps"] += metrics["total_cost_bps"]

                target["quantity_weighted_cost_bps"] += (
                    metrics["quantity_weighted_cost_bps"]
                )

        print(f"\nPOLICY: {policy.upper()}")
        print("-" * 130)

        print(
            f"{'Spread':>12} "
            f"{'Aggressor':>12} "
            f"{'Trades':>10} "
            f"{'Quantity':>12} "
            f"{'Avg Cost (bps)':>18} "
            f"{'Qty-Weighted (bps)':>22}"
        )

        for (spread, aggressor), metrics in sorted(combined.items()):
            trade_count = metrics["trade_count"]
            total_quantity = metrics["total_quantity"]

            avg_cost_bps = (
                metrics["total_cost_bps"] / trade_count
                if trade_count > 0
                else 0.0
            )

            qty_weighted_cost_bps = (
                metrics["quantity_weighted_cost_bps"] / total_quantity
                if total_quantity > 0
                else 0.0
            )

            print(
                f"{spread:>12.4f} "
                f"{aggressor:>12} "
                f"{trade_count:>10} "
                f"{total_quantity:>12} "
                f"{avg_cost_bps:>18.4f} "
                f"{qty_weighted_cost_bps:>22.4f}"
            )


def print_standardized_spread_cost(all_results):
    min_spread = 0.01
    max_spread = 0.18

    # Aggregate spread-conditioned metrics across seeds
    combined = {}

    for policy, results in all_results.items():
        policy_data = defaultdict(
            lambda: {
                "trade_count": 0,
                "total_quantity": 0,
                "total_cost_bps": 0.0,
                "quantity_weighted_cost_bps": 0.0,
            }
        )

        for result in results:
            for (spread, aggressor), metrics in result[
                "spread_distribution"
            ].items():
                if not min_spread <= spread <= max_spread:
                    continue

                target = policy_data[(spread, aggressor)]

                target["trade_count"] += metrics["trade_count"]
                target["total_quantity"] += metrics["total_quantity"]
                target["total_cost_bps"] += metrics["total_cost_bps"]
                target["quantity_weighted_cost_bps"] += (
                    metrics["quantity_weighted_cost_bps"]
                )

        combined[policy] = dict(policy_data)

    # Identify keys available in every policy
    common_keys = set.intersection(
        *[set(data.keys()) for data in combined.values()]
    )

    if not common_keys:
        raise ValueError("No common spread support found.")

    # Build common weights from pooled observations
    pooled_trades = {
        key: sum(
            combined[policy][key]["trade_count"]
            for policy in combined
        )
        for key in common_keys
    }

    pooled_quantity = {
        key: sum(
            combined[policy][key]["total_quantity"]
            for policy in combined
        )
        for key in common_keys
    }

    total_pooled_trades = sum(pooled_trades.values())
    total_pooled_quantity = sum(pooled_quantity.values())

    trade_weights = {
        key: count / total_pooled_trades
        for key, count in pooled_trades.items()
    }

    quantity_weights = {
        key: quantity / total_pooled_quantity
        for key, quantity in pooled_quantity.items()
    }

    print("\n" + "=" * 110)
    print("STANDARDIZED EXECUTION COST")
    print("=" * 110)

    print(f"Common support: {min_spread:.2f} - {max_spread:.2f}")
    print(f"Common spread/aggressor cells: {len(common_keys)}")
    print(f"Pooled trades: {total_pooled_trades}")
    print(f"Pooled quantity: {total_pooled_quantity}")

    print("\n")
    print(
        f"{'Policy':<12}"
        f"{'Avg Cost (bps)':>20}"
        f"{'Qty-Weighted (bps)':>25}"
    )
    print("-" * 60)

    standardized_results = {}

    for policy, data in combined.items():
        standardized_avg = 0.0
        standardized_qty = 0.0

        for key in common_keys:
            metrics = data[key]

            trade_count = metrics["trade_count"]
            total_quantity = metrics["total_quantity"]

            if trade_count <= 0 or total_quantity <= 0:
                raise ValueError(
                    f"Invalid observations for {policy}, {key}"
                )

            cell_avg_cost = (
                metrics["total_cost_bps"] / trade_count
            )

            cell_qty_cost = (
                metrics["quantity_weighted_cost_bps"]
                / total_quantity
            )

            standardized_avg += (
                trade_weights[key] * cell_avg_cost
            )

            standardized_qty += (
                quantity_weights[key] * cell_qty_cost
            )

        standardized_results[policy] = {
            "average_cost_bps": standardized_avg,
            "quantity_weighted_cost_bps": standardized_qty,
        }

        print(
            f"{policy:<12}"
            f"{standardized_avg:>20.4f}"
            f"{standardized_qty:>25.4f}"
        )

    # Compare against NONE
    baseline = standardized_results["none"]

    print("\nREDUCTION COMPARED WITH NONE")
    print("-" * 60)

    for policy, metrics in standardized_results.items():
        if policy == "none":
            continue

        avg_reduction = (
            (baseline["average_cost_bps"] - metrics["average_cost_bps"])
            / baseline["average_cost_bps"]
        ) * 100

        qty_reduction = (
            (
                baseline["quantity_weighted_cost_bps"]
                - metrics["quantity_weighted_cost_bps"]
            )
            / baseline["quantity_weighted_cost_bps"]
        ) * 100

        print(
            f"{policy.upper():<12}"
            f"Average: {avg_reduction:>8.2f}%"
            f" | Quantity-weighted: {qty_reduction:>8.2f}%"
        )

    return standardized_results


def print_arrival_state_distribution(samples):
    print("\n" + "=" * 95)
    print("POOLED ARRIVAL STATE DISTRIBUTION")
    print("=" * 95)

    for name, values in samples.items():
        if not values:
            print(f"\n{name.upper()}: No data")
            continue

        sorted_values = sorted(values)

        def percentile(data, p):
            index = round((len(data) - 1) * p)
            return data[index]

        print(f"\n{name.upper()}")
        print("-" * 75)
        print(f"Samples : {len(sorted_values)}")
        print(f"Min     : {min(sorted_values):.4f}")
        print(f"P10     : {percentile(sorted_values, 0.10):.4f}")
        print(f"P25     : {percentile(sorted_values, 0.25):.4f}")
        print(f"Median  : {percentile(sorted_values, 0.50):.4f}")
        print(f"P75     : {percentile(sorted_values, 0.75):.4f}")
        print(f"P90     : {percentile(sorted_values, 0.90):.4f}")
        print(f"Max     : {max(sorted_values):.4f}")


def print_paired_comparison(comparison, metric_name):
    result = comparison[metric_name]

    print(f"\n{metric_name}")
    print("-" * 60)
    print(f"Total states     : {result['total_states']}")
    print(f"NONE wins        : {result['baseline_wins']}")
    print(f"DISTANCE wins    : {result['competitor_wins']}")
    print(f"Ties             : {result['ties']}")
    print(f"NONE win rate    : {result['baseline_win_rate']:.2%}")
    print(f"DISTANCE win rate: {result['competitor_win_rate']:.2%}")


def analyze_paired_comparison_by_seed(
    arrival_observations_by_seed,
    min_samples=30,
):
    results = {}

    for seed, observations in arrival_observations_by_seed.items():

        analysis_result = (
            OrderBookStateMatchingAnalyzer.analyze(
                observations
            )
        )

        selected_states = (
            OrderBookStateMatchingAnalyzer
            .filter_common_states_by_minimum_samples(
                analysis_result,
                min_samples=min_samples,
            )
        )

        comparison = (
            OrderBookStateMatchingAnalyzer.compare_policies_by_state(
                analysis_result,
                selected_states=selected_states,
                baseline="none",
                competitor="distance",
            )
        )

        results[seed] = {
            "selected_state_count": len(selected_states),
            "comparison": comparison,
        }

    return results


def main():

    all_results = {}

    pooled_arrival_observations = []

    arrival_observations_by_seed = {
        seed: []
        for seed in SEEDS
    }

    pooled_arrival_samples = {
        "spread": [],
        "bid_depth": [],
        "ask_depth": [],
        "obi": [],
    }

    for policy in POLICIES:
        print("\n" + "#" * 95)
        print(f"EXECUTION COST EXPERIMENT: {policy.upper()}")
        print("#" * 95)

        policy_results = []

        for seed in SEEDS:
            experiment = run_experiment(policy, seed)
            policy_results.append(experiment)

            seed_observations = experiment[
                "arrival_state_observations"
            ]

            pooled_arrival_observations.extend(
                seed_observations
            )

            arrival_observations_by_seed[seed].extend(
                seed_observations
            )

            samples = experiment["arrival_state_samples"]

            for key in pooled_arrival_samples:
                pooled_arrival_samples[key].extend(
                    samples[key]
                )

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

        all_results[policy] = policy_results

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

    print_spread_distribution(all_results)
    print_standardized_spread_cost(all_results)

    total_observations = len(pooled_arrival_observations)

    total_analyzed = sum(
        experiment["analyzed_trade_count"]
        for policy_results in all_results.values()
        for experiment in policy_results
    )

    print("\nARRIVAL STATE OBSERVATION VALIDATION")
    print("-" * 75)
    print(f"Collected observations: {total_observations}")
    print(f"Expected observations:  {total_analyzed}")

    if total_observations != total_analyzed:
        raise AssertionError(
            "Arrival state observation count mismatch"
        )

    print("Validation: PASSED")

    print_arrival_state_distribution(
        pooled_arrival_samples
    )

    state_matching_result = (
        OrderBookStateMatchingAnalyzer.analyze(
            pooled_arrival_observations
        )
    )

    standardized_result = (
        OrderBookStateMatchingAnalyzer.calculate_standardized_cost(
            state_matching_result
        )
    )

    print("\n" + "=" * 95)
    print("PHASE 20.13: MINIMUM SAMPLE THRESHOLD ANALYSIS")
    print("=" * 95)


    # Paired comparison: NONE vs DISTANCE
    selected_states_30 = (
        OrderBookStateMatchingAnalyzer
        .filter_common_states_by_minimum_samples(
            state_matching_result,
            min_samples=30,
        )
    )

    paired_comparison = (
        OrderBookStateMatchingAnalyzer.compare_policies_by_state(
            state_matching_result,
            selected_states=selected_states_30,
            baseline="none",
            competitor="distance",
        )
    )

    print("\n" + "=" * 95)
    print("PHASE 20.13: PAIRED POLICY COMPARISON")
    print("=" * 95)

    print(f"Selected states: {len(selected_states_30)}")

    print_paired_comparison(
        paired_comparison,
        "average_cost_bps",
    )

    print_paired_comparison(
        paired_comparison,
        "quantity_weighted_cost_bps",
    )

    # Phase 20.14: Per-seed robustness analysis
    per_seed_results = analyze_paired_comparison_by_seed(
        arrival_observations_by_seed,
        min_samples=30,
    )

    print("\n" + "=" * 95)
    print("PHASE 20.14: PER-SEED PAIRED COMPARISON")
    print("=" * 95)

    for seed, result in per_seed_results.items():
        comparison = result["comparison"]

        print(f"\nSEED: {seed}")
        print("-" * 75)
        print(
            f"Selected states: "
            f"{result['selected_state_count']}"
        )

        print_paired_comparison(
            comparison,
            "average_cost_bps",
        )

        print_paired_comparison(
            comparison,
            "quantity_weighted_cost_bps",
        )

    thresholds = [10, 30, 50]

    for threshold in thresholds:
        selected_states = (
            OrderBookStateMatchingAnalyzer
            .filter_common_states_by_minimum_samples(
                state_matching_result,
                min_samples=threshold,
            )
        )

        result = (
            OrderBookStateMatchingAnalyzer.calculate_standardized_cost(
                state_matching_result,
                selected_states=selected_states,
            )
        )

        print(f"\nMINIMUM SAMPLE THRESHOLD: {threshold}")
        print("-" * 75)

        print(f"Selected states: {len(selected_states)}")

        if result["policies"] is None:
            print("Insufficient data for comparison.")
            continue

        for policy, metrics in result["policies"].items():
            print(
                f"{policy.upper():<12} | "
                f"Trades: {metrics['trade_count']:>7} | "
                f"Quantity: {metrics['total_quantity']:>9} | "
                f"Avg Cost: {metrics['average_cost_bps']:>8.4f} bps | "
                f"Qty-Weighted: "
                f"{metrics['quantity_weighted_cost_bps']:>8.4f} bps"
            )

    print("\n" + "=" * 95)
    print("PHASE 20.13: ORDER BOOK STATE MATCHING")
    print("=" * 95)

    print(
        f"Common states: "
        f"{standardized_result['common_state_count']}"
    )

    print(
        f"{'Policy':<15}"
        f"{'Trades':>12}"
        f"{'Quantity':>15}"
        f"{'Avg Cost (bps)':>20}"
        f"{'Qty-Weighted (bps)':>22}"
    )


    sample_summary = (
        OrderBookStateMatchingAnalyzer.summarize_common_state_samples(
            state_matching_result
        )
    )

    print("\nCOMMON STATE SAMPLE DISTRIBUTION")
    print("-" * 75)

    for policy, metrics in sample_summary.items():
        print(
            f"{policy.upper():<12} | "
            f"States: {metrics['state_count']:>4} | "
            f"Min: {metrics['minimum']:>5} | "
            f"Median: {metrics['median']:>5} | "
            f"Max: {metrics['maximum']:>5}"
        )

    print("-" * 84)

    for policy, metrics in standardized_result["policies"].items():
        print(
            f"{policy.upper():<15}"
            f"{metrics['trade_count']:>12}"
            f"{metrics['total_quantity']:>15}"
            f"{metrics['average_cost_bps']:>20.4f}"
            f"{metrics['quantity_weighted_cost_bps']:>22.4f}"
        )

    print("\n" + "#" * 95)
    print("PHASE 20.13: ORDER BOOK STATE MATCHING ANALYSIS COMPLETE")
    print("#" * 95)


if __name__ == "__main__":
    main()
