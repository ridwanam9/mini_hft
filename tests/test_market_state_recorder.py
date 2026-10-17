from src.market_state_recorder import MarketStateRecorder
from src.order_book_l3 import OrderBookL3
from src.matching_engine_l3 import MatchingEngineL3
from src.market_data import (
    Order,
    OrderSide,
    OrderType,
)


def test_market_state_recorder_records_trade():
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

    previous = book.snapshot()

    fills = engine.submit_order(
        Order(
            order_id=201,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=50,
            timestamp=0.002,
        )
    )

    current = book.snapshot()

    recorder = MarketStateRecorder()

    state = recorder.record(
        previous_book=previous,
        current_book=current,
        timestamp=0.002,
        trade=engine.trade_tape[-1],
    )

    assert state.timestamp == 0.002

    assert state.best_bid is None
    assert state.best_ask == 101.02

    assert state.spread is None
    assert state.mid_price is None

    assert state.ask_volume == 50

    assert state.last_trade_price == 101.02
    assert state.last_trade_quantity == 50
    assert state.last_trade_aggressor == "BUY"

    assert state.ofi == 50
    
    assert len(recorder.states) == 1