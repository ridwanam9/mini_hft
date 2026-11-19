from src.order_book_l3 import OrderBookL3
from src.matching_engine_l3 import MatchingEngineL3
from src.market_data import Order, OrderSide, OrderType
import pytest
from src.trade_tape import TradeRecord
from src.execution_cost_analyzer import ExecutionCostAnalyzer

def test_trade_records_arrival_mid_price():
    book = OrderBookL3()
    engine = MatchingEngineL3(book)

    # Existing resting ask at 100.05
    ask = Order(
        order_id=1,
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        quantity=10,
        price=100.05,
        timestamp=1.0,
    )
    engine.submit_order(ask)

    # Existing resting bid at 99.95
    bid = Order(
        order_id=2,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=10,
        price=99.95,
        timestamp=2.0,
    )
    engine.submit_order(bid)

    # Arrival mid-price = (99.95 + 100.05) / 2 = 100.00
    market_buy = Order(
        order_id=3,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=5,
        timestamp=3.0,
    )
    engine.submit_order(market_buy)

    trade = engine.trade_tape[-1]

    assert trade.price == 100.05
    assert trade.arrival_mid_price == 100.00
    assert trade.aggressor == "BUY"
    assert trade.quantity == 5


def test_aggressive_buy_execution_cost():
    trades = [
        TradeRecord(
            timestamp=1.0,
            price=100.05,
            quantity=10,
            aggressor="BUY",
            buy_order_id=1,
            sell_order_id=2,
            arrival_mid_price=100.00,
        )
    ]

    result = ExecutionCostAnalyzer(trades).analyze()

    assert result["total_trades"] == 1
    assert result["buy"]["average_execution_cost"] == pytest.approx(0.05)
    assert result["buy"]["average_execution_cost_bps"] == pytest.approx(5.0)


def test_aggressive_sell_execution_cost():
    trades = [
        TradeRecord(
            timestamp=1.0,
            price=99.95,
            quantity=10,
            aggressor="SELL",
            buy_order_id=1,
            sell_order_id=2,
            arrival_mid_price=100.00,
        )
    ]

    result = ExecutionCostAnalyzer(trades).analyze()

    assert result["sell"]["average_execution_cost"] == pytest.approx(0.05)
    assert result["sell"]["average_execution_cost_bps"] == pytest.approx(5.0)


def test_quantity_weighted_execution_cost():
    trades = [
        TradeRecord(
            timestamp=1.0,
            price=100.01,
            quantity=10,
            aggressor="BUY",
            buy_order_id=1,
            sell_order_id=2,
            arrival_mid_price=100.00,
        ),
        TradeRecord(
            timestamp=2.0,
            price=100.05,
            quantity=100,
            aggressor="BUY",
            buy_order_id=3,
            sell_order_id=4,
            arrival_mid_price=100.00,
        ),
    ]

    result = ExecutionCostAnalyzer(trades).analyze()

    expected = ((0.01 * 10) + (0.05 * 100)) / 110

    assert result["buy"]["quantity_weighted_execution_cost"] == pytest.approx(
        expected
    )


def test_trade_without_arrival_mid_price_is_skipped():
    trades = [
        TradeRecord(
            timestamp=1.0,
            price=100.05,
            quantity=10,
            aggressor="BUY",
            buy_order_id=1,
            sell_order_id=2,
            arrival_mid_price=None,
        )
    ]

    result = ExecutionCostAnalyzer(trades).analyze()

    assert result["total_trades"] == 0
    assert result["total_quantity"] == 0


def test_invalid_arrival_mid_price_is_rejected():
    trades = [
        TradeRecord(
            timestamp=1.0,
            price=100.05,
            quantity=10,
            aggressor="BUY",
            buy_order_id=1,
            sell_order_id=2,
            arrival_mid_price=0,
        )
    ]

    with pytest.raises(ValueError):
        ExecutionCostAnalyzer(trades).analyze()