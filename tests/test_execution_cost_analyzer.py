
from src.order_book_l3 import OrderBookL3
from src.matching_engine_l3 import MatchingEngineL3
from src.market_data import Order, OrderSide, OrderType


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
