
from types import SimpleNamespace

from src.spread_cost_analyzer import SpreadCostAnalyzer


def make_trade(
    price,
    quantity,
    aggressor,
    bid=99.0,
    ask=101.0,
    mid=100.0,
):
    return SimpleNamespace(
        price=price,
        quantity=quantity,
        aggressor=aggressor,
        arrival_best_bid=bid,
        arrival_best_ask=ask,
        arrival_mid_price=mid,
    )


def test_aggressive_buy_at_best_ask_has_zero_beyond_touch_cost():
    trade = make_trade(price=101.0, quantity=2, aggressor="BUY")

    result = SpreadCostAnalyzer([trade]).analyze()
    metrics = result["overall"]

    assert metrics["average_total_cost"] == 1.0
    assert metrics["average_total_half_spread_cost"] == 1.0
    assert metrics["average_total_beyond_touch_cost"] == 0.0


def test_aggressive_buy_beyond_best_ask_has_positive_impact():
    trade = make_trade(price=102.0, quantity=2, aggressor="BUY")

    result = SpreadCostAnalyzer([trade]).analyze()
    metrics = result["overall"]

    assert metrics["average_total_cost"] == 2.0
    assert metrics["average_total_half_spread_cost"] == 1.0
    assert metrics["average_total_beyond_touch_cost"] == 1.0


def test_aggressive_sell_at_best_bid_has_zero_beyond_touch_cost():
    trade = make_trade(price=99.0, quantity=2, aggressor="SELL")

    result = SpreadCostAnalyzer([trade]).analyze()
    metrics = result["overall"]

    assert metrics["average_total_cost"] == 1.0
    assert metrics["average_total_half_spread_cost"] == 1.0
    assert metrics["average_total_beyond_touch_cost"] == 0.0


def test_decomposition_is_consistent_for_both_sides():
    trades = [
        make_trade(price=102.0, quantity=2, aggressor="BUY"),
        make_trade(price=98.0, quantity=3, aggressor="SELL"),
    ]

    result = SpreadCostAnalyzer(trades).analyze()
    metrics = result["overall"]

    assert metrics["average_total_cost"] == 2.0
    assert metrics["average_total_half_spread_cost"] == 1.0
    assert metrics["average_total_beyond_touch_cost"] == 1.0


def test_missing_arrival_data_is_skipped():
    trade = make_trade(
        price=101.0,
        quantity=2,
        aggressor="BUY",
        bid=None,
        ask=101.0,
        mid=None,
    )

    result = SpreadCostAnalyzer([trade]).analyze()

    assert result["overall"]["trade_count"] == 0
    assert result["skipped_count"] == 1


def test_buy_and_sell_metrics_are_separated():
    trades = [
        make_trade(price=101.0, quantity=2, aggressor="BUY"),
        make_trade(price=99.0, quantity=3, aggressor="SELL"),
    ]

    result = SpreadCostAnalyzer(trades).analyze()

    assert result["by_aggressor"]["BUY"]["trade_count"] == 1
    assert result["by_aggressor"]["SELL"]["trade_count"] == 1
    assert result["by_aggressor"]["BUY"]["total_quantity"] == 2
    assert result["by_aggressor"]["SELL"]["total_quantity"] == 3
