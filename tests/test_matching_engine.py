
from src.order_book import OrderBook
from src.market_data import Order, OrderSide, OrderType
from src.matching_engine import MatchingEngine


def make_order(
    order_id,
    side,
    order_type,
    quantity,
    price=None,
):
    return Order(
        order_id=order_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
    )


def test_market_buy_consumes_multiple_ask_levels():
    book = OrderBook()
    engine = MatchingEngine(book)

    engine.submit_order(
        make_order(1, OrderSide.SELL, OrderType.LIMIT, 100, 101.02)
    )
    engine.submit_order(
        make_order(2, OrderSide.SELL, OrderType.LIMIT, 200, 101.03)
    )

    fills = engine.submit_order(
        make_order(3, OrderSide.BUY, OrderType.MARKET, 150)
    )

    assert [(t.price, t.quantity) for t in fills] == [
        (101.02, 100),
        (101.03, 50),
    ]

    assert book.asks == {101.03: 150}


def test_limit_buy_rests_unfilled_quantity():
    book = OrderBook()
    engine = MatchingEngine(book)

    engine.submit_order(
        make_order(1, OrderSide.SELL, OrderType.LIMIT, 100, 101.02)
    )

    fills = engine.submit_order(
        make_order(2, OrderSide.BUY, OrderType.LIMIT, 150, 101.03)
    )

    assert sum(t.quantity for t in fills) == 100
    assert book.asks == {}
    assert book.bids == {101.03: 50}


def test_market_buy_without_liquidity_does_not_create_bid():
    book = OrderBook()
    engine = MatchingEngine(book)

    fills = engine.submit_order(
        make_order(1, OrderSide.BUY, OrderType.MARKET, 100)
    )

    assert fills == []
    assert book.bids == {}
    assert book.asks == {}


def test_zero_quantity_is_rejected():
    book = OrderBook()
    engine = MatchingEngine(book)

    try:
        engine.submit_order(
            make_order(1, OrderSide.BUY, OrderType.MARKET, 0)
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")
