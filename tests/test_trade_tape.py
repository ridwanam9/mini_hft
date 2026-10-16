from src.market_data import(
    Order,
    OrderSide,
    OrderType,
)

from src.order_book_l3 import OrderBookL3
from src.matching_engine_l3 import MatchingEngineL3

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