from src.market_data import(
    Order,
    OrderSide,
    OrderType,
)

from src.order_book_l3 import OrderBookL3
from src.matching_engine_l3 import MatchingEngineL3
import pytest

def test_trade_tape_records_aggressor():
    book = OrderBookL3()
    engine = MatchingEngineL3(book)

    engine.submit_order(
        Order(
            order_id=101,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=101.02,
            timestamp=0.001,
        )
    )

    engine.submit_order(
        Order(
            order_id=201,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=50,
            timestamp=0.002,
        )
    )

    assert len(engine.trade_tape) == 1

    trade = engine.trade_tape[0]

    assert trade.timestamp == 0.002
    assert trade.price == 101.02
    assert trade.quantity == 50
    assert trade.aggressor == "BUY"
    assert trade.buy_order_id == 201
    assert trade.sell_order_id == 101


def test_trade_tape_records_sell_aggressor():
    book = OrderBookL3()
    engine = MatchingEngineL3(book)

    engine.submit_order(
        Order(
            order_id=101,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=101.00,
            timestamp=0.001,
        )
    )

    engine.submit_order(
        Order(
            order_id=201,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=40,
            timestamp=0.002,
        )
    )

    assert len(engine.trade_tape) == 1

    trade = engine.trade_tape[0]

    assert trade.timestamp == 0.002
    assert trade.price == 101.00
    assert trade.quantity == 40
    assert trade.aggressor == "SELL"
    assert trade.buy_order_id == 101
    assert trade.sell_order_id == 201



def test_trade_tape_records_arrival_depth_and_obi():
    book = OrderBookL3()
    engine = MatchingEngineL3(book)

    # Create 5 bid levels.
    bid_levels = [
        (101, 100),
        (100, 90),
        (99, 80),
        (98, 70),
        (97, 60),
    ]

    for i, (price, quantity) in enumerate(bid_levels):
        engine.submit_order(
            Order(
                order_id=100 + i,
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=quantity,
                price=price,
            )
        )

    # Create 5 ask levels.
    ask_levels = [
        (102, 80),
        (103, 70),
        (104, 60),
        (105, 50),
        (106, 40),
    ]

    for i, (price, quantity) in enumerate(ask_levels):
        engine.submit_order(
            Order(
                order_id=200 + i,
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=quantity,
                price=price,
            )
        )

    # Aggressive BUY.
    engine.submit_order(
        Order(
            order_id=300,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10,
        )
    )

    trade = engine.trade_tape[0]

    expected_bid_depth = 100 + 90 + 80 + 70 + 60
    expected_ask_depth = 80 + 70 + 60 + 50 + 40

    expected_obi = (
        expected_bid_depth - expected_ask_depth
    ) / (
        expected_bid_depth + expected_ask_depth
    )

    assert trade.arrival_bid_depth == expected_bid_depth
    assert trade.arrival_ask_depth == expected_ask_depth
    assert trade.arrival_obi == pytest.approx(expected_obi)




def test_multiple_fills_share_same_arrival_snapshot():
    book = OrderBookL3()
    engine = MatchingEngineL3(book)

    # Bid depth.
    engine.submit_order(
        Order(
            order_id=101,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=100,
        )
    )

    # Two ask orders at different price levels.
    engine.submit_order(
        Order(
            order_id=102,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=40,
            price=101,
        )
    )

    engine.submit_order(
        Order(
            order_id=103,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=60,
            price=102,
        )
    )

    # Aggressive BUY consumes both ask orders.
    engine.submit_order(
        Order(
            order_id=201,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
        )
    )

    assert len(engine.trade_tape) == 2

    first = engine.trade_tape[0]
    second = engine.trade_tape[1]

    assert first.arrival_bid_depth == second.arrival_bid_depth
    assert first.arrival_ask_depth == second.arrival_ask_depth
    assert first.arrival_obi == pytest.approx(second.arrival_obi)

    assert first.arrival_bid_depth == 100
    assert first.arrival_ask_depth == 100
