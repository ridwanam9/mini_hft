
from src.order_book_state_matching_analyzer import (
    OrderBookStateMatchingAnalyzer,
)


def test_classify_spread():
    assert (
        OrderBookStateMatchingAnalyzer.classify_spread(0.02)
        == "LOW"
    )
    assert (
        OrderBookStateMatchingAnalyzer.classify_spread(0.05)
        == "MEDIUM"
    )
    assert (
        OrderBookStateMatchingAnalyzer.classify_spread(0.10)
        == "HIGH"
    )
    assert (
        OrderBookStateMatchingAnalyzer.classify_spread(0.20)
        is None
    )


def test_classify_depth():
    classify = OrderBookStateMatchingAnalyzer.classify_depth

    assert classify(50) == "LOW"
    assert classify(250) == "MEDIUM"
    assert classify(500) == "HIGH"


def test_classify_obi():
    classify = OrderBookStateMatchingAnalyzer.classify_obi

    assert classify(-0.6) == "NEGATIVE"
    assert classify(0.0) == "BALANCED"
    assert classify(0.6) == "POSITIVE"


def test_classify_observation():
    observation = {
        "spread": 0.05,
        "bid_depth": 250,
        "ask_depth": 500,
        "obi": -0.6,
        "aggressor": "BUY",
    }

    result = (
        OrderBookStateMatchingAnalyzer.classify_observation(
            observation
        )
    )

    assert result == (
        "MEDIUM",
        "MEDIUM",
        "HIGH",
        "NEGATIVE",
        "BUY",
    )


def test_observation_outside_spread_support():
    observation = {
        "spread": 0.20,
        "bid_depth": 250,
        "ask_depth": 500,
        "obi": 0.0,
        "aggressor": "BUY",
    }

    result = (
        OrderBookStateMatchingAnalyzer.classify_observation(
            observation
        )
    )

    assert result is None


def test_invalid_aggressor_is_rejected():
    observation = {
        "spread": 0.05,
        "bid_depth": 250,
        "ask_depth": 500,
        "obi": 0.0,
        "aggressor": "INVALID",
    }

    try:
        OrderBookStateMatchingAnalyzer.classify_observation(
            observation
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")



def test_analyze_groups_observations_by_policy():
    observations = [
        {
            "policy": "none",
            "spread": 0.05,
            "bid_depth": 250,
            "ask_depth": 500,
            "obi": -0.6,
            "aggressor": "BUY",
            "execution_cost_bps": 4.0,
            "quantity": 100,
        },
        {
            "policy": "random",
            "spread": 0.05,
            "bid_depth": 250,
            "ask_depth": 500,
            "obi": -0.6,
            "aggressor": "BUY",
            "execution_cost_bps": 3.0,
            "quantity": 200,
        },
        {
            "policy": "distance",
            "spread": 0.05,
            "bid_depth": 250,
            "ask_depth": 500,
            "obi": -0.6,
            "aggressor": "BUY",
            "execution_cost_bps": 2.0,
            "quantity": 300,
        },
    ]

    result = OrderBookStateMatchingAnalyzer.analyze(
        observations
    )

    state = (
        "MEDIUM",
        "MEDIUM",
        "HIGH",
        "NEGATIVE",
        "BUY",
    )

    group = result["groups"][state]

    assert group["none"]["trade_count"] == 1
    assert group["random"]["trade_count"] == 1
    assert group["distance"]["trade_count"] == 1

    assert group["none"]["average_cost_bps"] == 4.0
    assert group["random"]["average_cost_bps"] == 3.0
    assert group["distance"]["average_cost_bps"] == 2.0

    assert group["none"]["total_quantity"] == 100
    assert group["random"]["total_quantity"] == 200
    assert group["distance"]["total_quantity"] == 300

    assert result["excluded_count"] == 0
    assert result["total_observations"] == 3


def test_analyze_excludes_out_of_support_observations():
    observations = [
        {
            "policy": "none",
            "spread": 0.20,
            "bid_depth": 250,
            "ask_depth": 500,
            "obi": 0.0,
            "aggressor": "BUY",
            "execution_cost_bps": 3.0,
            "quantity": 100,
        }
    ]

    result = OrderBookStateMatchingAnalyzer.analyze(
        observations
    )

    assert result["groups"] == {}
    assert result["excluded_count"] == 1
    assert result["total_observations"] == 1


def test_find_common_states():
    observations = []

    policies = ["none", "random", "distance"]

    # State A: all policies have observations.
    for policy in policies:
        observations.append({
            "policy": policy,
            "spread": 0.05,
            "bid_depth": 250,
            "ask_depth": 500,
            "obi": -0.6,
            "aggressor": "BUY",
            "execution_cost_bps": 3.0,
            "quantity": 100,
        })

    # State B: only NONE and RANDOM have observations.
    for policy in ["none", "random"]:
        observations.append({
            "policy": policy,
            "spread": 0.02,
            "bid_depth": 50,
            "ask_depth": 80,
            "obi": 0.0,
            "aggressor": "SELL",
            "execution_cost_bps": 2.0,
            "quantity": 100,
        })

    result = OrderBookStateMatchingAnalyzer.analyze(
        observations
    )

    common_states = (
        OrderBookStateMatchingAnalyzer.find_common_states(
            result
        )
    )

    expected_state = (
        "MEDIUM",
        "MEDIUM",
        "HIGH",
        "NEGATIVE",
        "BUY",
    )

    assert common_states == [expected_state]



def test_compare_common_states():
    observations = []

    for policy, cost in [
        ("none", 3.5),
        ("random", 3.0),
        ("distance", 2.5),
    ]:
        observations.append({
            "policy": policy,
            "spread": 0.05,
            "bid_depth": 250,
            "ask_depth": 500,
            "obi": -0.6,
            "aggressor": "BUY",
            "execution_cost_bps": cost,
            "quantity": 100,
        })

    result = OrderBookStateMatchingAnalyzer.analyze(observations)

    comparisons = (
        OrderBookStateMatchingAnalyzer.compare_common_states(result)
    )

    assert len(comparisons) == 1

    comparison = comparisons[0]

    assert comparison["policies"]["none"]["average_cost_bps"] == 3.5
    assert comparison["policies"]["random"]["average_cost_bps"] == 3.0
    assert comparison["policies"]["distance"]["average_cost_bps"] == 2.5