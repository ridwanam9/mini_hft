
from src.trade_tape import TradeRecord
from src.order_book_state_analyzer import OrderBookStateAnalyzer


def test_classify_two_sided():
    trade = TradeRecord(
        timestamp=1,
        price=101,
        quantity=5,
        aggressor="BUY",
        buy_order_id=1,
        sell_order_id=2,
        arrival_best_bid=99,
        arrival_best_ask=101,
        arrival_mid_price=100,
        arrival_spread=2,
    )

    assert OrderBookStateAnalyzer.classify(trade) == "TWO_SIDED"


def test_classify_ask_only():
    trade = TradeRecord(
        timestamp=1,
        price=101,
        quantity=5,
        aggressor="BUY",
        buy_order_id=1,
        sell_order_id=2,
        arrival_best_ask=101,
    )

    assert OrderBookStateAnalyzer.classify(trade) == "ASK_ONLY"


def test_classify_bid_only():
    trade = TradeRecord(
        timestamp=1,
        price=99,
        quantity=5,
        aggressor="SELL",
        buy_order_id=1,
        sell_order_id=2,
        arrival_best_bid=99,
    )

    assert OrderBookStateAnalyzer.classify(trade) == "BID_ONLY"


def test_analyze_trade_counts_and_quantity():
    trades = [
        TradeRecord(
            timestamp=1,
            price=101,
            quantity=5,
            aggressor="BUY",
            buy_order_id=1,
            sell_order_id=2,
            arrival_best_bid=99,
            arrival_best_ask=101,
        ),
        TradeRecord(
            timestamp=2,
            price=102,
            quantity=3,
            aggressor="BUY",
            buy_order_id=3,
            sell_order_id=4,
            arrival_best_ask=102,
        ),
        TradeRecord(
            timestamp=3,
            price=99,
            quantity=4,
            aggressor="SELL",
            buy_order_id=5,
            sell_order_id=6,
            arrival_best_bid=99,
        ),
    ]

    result = OrderBookStateAnalyzer(trades).analyze()

    assert result["TWO_SIDED"]["trade_count"] == 1
    assert result["ASK_ONLY"]["trade_count"] == 1
    assert result["BID_ONLY"]["trade_count"] == 1

    assert result["TWO_SIDED"]["total_quantity"] == 5
    assert result["ASK_ONLY"]["total_quantity"] == 3
    assert result["BID_ONLY"]["total_quantity"] == 4

    assert result["total_trades"] == 3
    assert result["total_quantity"] == 12
