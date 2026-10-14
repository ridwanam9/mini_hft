
import pytest

from src.market_data import Order, OrderSide, OrderType
from src.order_book_l3 import OrderBookL3
from src.matching_engine_l3 import MatchingEngineL3


def make_order(order_id, side, order_type, quantity, price=None):
    return Order(
        order_id=order_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
    )


def test_fifo_priority_and_trade_ids():
    book = OrderBookL3()
    engine = MatchingEngineL3(book)

    engine.submit_order(
        make_order(101, OrderSide.SELL, OrderType.LIMIT, 100, 101.02)
    )
    engine.submit_order(
        make_order(102, OrderSide.SELL, OrderType.LIMIT, 150, 101.02)
    )

    fills = engine.submit_order(
        make_order(201, OrderSide.BUY, OrderType.MARKET, 120)
    )

    assert [
        (t.buy_order_id, t.sell_order_id, t.quantity)
        for t in fills
    ] == [
        (201, 101, 100),
        (201, 102, 20),
    ]

    assert book.asks == {101.02: 130}


def test_cancel_order():
    book = OrderBookL3()
    engine = MatchingEngineL3(book)

    engine.submit_order(
        make_order(101, OrderSide.SELL, OrderType.LIMIT, 100, 101.02)
    )
    engine.submit_order(
        make_order(102, OrderSide.SELL, OrderType.LIMIT, 200, 101.02)
    )

    assert book.cancel_order(101) is True
    assert book.asks == {101.02: 200}

    fills = engine.submit_order(
        make_order(201, OrderSide.BUY, OrderType.MARKET, 50)
    )

    assert len(fills) == 1
    assert fills[0].sell_order_id == 102
    assert fills[0].quantity == 50


def test_limit_order_rests_with_remaining_quantity():
    book = OrderBookL3()
    engine = MatchingEngineL3(book)

    engine.submit_order(
        make_order(101, OrderSide.SELL, OrderType.LIMIT, 100, 101.02)
    )

    engine.submit_order(
        make_order(102, OrderSide.SELL, OrderType.LIMIT, 100, 101.03)
    )

    fills = engine.submit_order(
        make_order(201, OrderSide.BUY, OrderType.LIMIT, 250, 101.03)
    )

    assert [t.quantity for t in fills] == [100, 100]
    assert book.asks == {}
    assert book.bids == {101.03: 50}


def test_duplicate_order_id_is_rejected():
    book = OrderBookL3()
    engine = MatchingEngineL3(book)

    order = make_order(
        101, OrderSide.SELL, OrderType.LIMIT, 100, 101.02
    )

    engine.submit_order(order)

    with pytest.raises(ValueError, match="Duplicate order ID"):
        engine.submit_order(
            make_order(101, OrderSide.BUY, OrderType.MARKET, 10)
        )
