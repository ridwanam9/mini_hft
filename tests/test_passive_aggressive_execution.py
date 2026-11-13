
from src.market_data import Order, OrderSide, OrderType
from src.order_book_l3 import OrderBookL3
from src.matching_engine_l3 import MatchingEngineL3


def make_order(
    order_id,
    side,
    quantity,
    price,
    timestamp,
):
    return Order(
        order_id=order_id,
        side=side,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
        timestamp=timestamp,
    )


def make_engine():
    book = OrderBookL3()
    engine = MatchingEngineL3(book)
    return book, engine


def test_aggressive_buy_execution():
    book, engine = make_engine()

    sell = make_order(
        1, OrderSide.SELL, 10, 100.0, 1.0
    )
    engine.submit_order(sell)

    buy = make_order(
        2, OrderSide.BUY, 6, 100.0, 2.0
    )
    engine.submit_order(buy)

    resting = book.order_history[1]
    incoming = book.order_history[2]

    assert incoming["aggressive_executed_quantity"] == 6
    assert incoming["passive_executed_quantity"] == 0

    assert resting["aggressive_executed_quantity"] == 0
    assert resting["passive_executed_quantity"] == 6


def test_aggressive_sell_execution():
    book, engine = make_engine()

    buy = make_order(
        1, OrderSide.BUY, 10, 100.0, 1.0
    )
    engine.submit_order(buy)

    sell = make_order(
        2, OrderSide.SELL, 6, 100.0, 2.0
    )
    engine.submit_order(sell)

    resting = book.order_history[1]
    incoming = book.order_history[2]

    assert incoming["aggressive_executed_quantity"] == 6
    assert incoming["passive_executed_quantity"] == 0

    assert resting["aggressive_executed_quantity"] == 0
    assert resting["passive_executed_quantity"] == 6


def test_partial_aggressive_execution():
    book, engine = make_engine()

    sell = make_order(
        1, OrderSide.SELL, 4, 100.0, 1.0
    )
    engine.submit_order(sell)

    buy = make_order(
        2, OrderSide.BUY, 10, 100.0, 2.0
    )
    engine.submit_order(buy)

    incoming = book.order_history[2]
    resting = book.order_history[1]

    assert incoming["aggressive_executed_quantity"] == 4
    assert incoming["passive_executed_quantity"] == 0
    assert incoming["executed_quantity"] == 4
    assert incoming["remaining_quantity"] == 6

    assert resting["passive_executed_quantity"] == 4


def test_mixed_aggressive_and_passive_execution():
    book, engine = make_engine()

    # Step 1: Add resting SELL quantity 4.
    sell = make_order(
        1, OrderSide.SELL, 4, 100.0, 1.0
    )
    engine.submit_order(sell)

    # Step 2: BUY 10 executes 4 immediately.
    # Remaining 6 becomes a resting BUY.
    buy = make_order(
        2, OrderSide.BUY, 10, 100.0, 2.0
    )
    engine.submit_order(buy)

    # Step 3: Incoming SELL executes 3 against resting BUY.
    incoming_sell = make_order(
        3, OrderSide.SELL, 3, 100.0, 3.0
    )
    engine.submit_order(incoming_sell)

    history = book.order_history[2]

    assert history["aggressive_executed_quantity"] == 4
    assert history["passive_executed_quantity"] == 3
    assert history["executed_quantity"] == 7
    assert history["remaining_quantity"] == 3
    assert history["status"] == "active"


def test_execution_quantity_consistency():
    book, engine = make_engine()

    sell = make_order(
        1, OrderSide.SELL, 10, 100.0, 1.0
    )
    engine.submit_order(sell)

    buy = make_order(
        2, OrderSide.BUY, 6, 100.0, 2.0
    )
    engine.submit_order(buy)

    for record in book.order_history.values():
        assert record["executed_quantity"] == (
            record["aggressive_executed_quantity"]
            + record["passive_executed_quantity"]
        )
