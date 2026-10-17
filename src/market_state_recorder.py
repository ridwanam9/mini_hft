from src.market_state import MarketState
from src.features import (
    bid_volume,
    ask_volume,
    order_book_imbalance,
    microprice,
    spread,
    mid_price,
)
from src.ofi import calculate_ofi


class MarketStateRecorder:
    def __init__(self):
        self.states = []

    def record(
        self,
        previous_book,
        current_book,
        timestamp,
        trade=None,
    ):
        state = MarketState(
            timestamp=timestamp,

            best_bid=current_book.best_bid,
            best_ask=current_book.best_ask,

            spread=spread(current_book),
            mid_price=mid_price(current_book),

            bid_volume=bid_volume(current_book),
            ask_volume=ask_volume(current_book),

            obi=order_book_imbalance(current_book),

            microprice=microprice(current_book),

            ofi=calculate_ofi(
                previous_book,
                current_book,
            ),

            last_trade_price=(
                trade.price
                if trade is not None
                else None
            ),

            last_trade_quantity=(
                trade.quantity
                if trade is not None
                else 0
            ),

            last_trade_aggressor=(
                trade.aggressor
                if trade is not None
                else None
            ),
        )

        self.states.append(state)

        return state

