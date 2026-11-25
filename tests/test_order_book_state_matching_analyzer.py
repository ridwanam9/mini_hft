
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
