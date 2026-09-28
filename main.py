from src.order_book import OrderBook
from src.market_data import MarketEvent, EventType, Side

from src.features import (
    spread,
    mid_price,
    bid_volume,
    ask_volume,
    order_book_imbalance,
)


book = OrderBook()


events = [

    MarketEvent(
        timestamp=0.001,
        event_type=EventType.ADD,
        side=Side.BID,
        price=101.00,
        quantity=500,
    ),

    MarketEvent(
        timestamp=0.002,
        event_type=EventType.ADD,
        side=Side.BID,
        price=101.01,
        quantity=250,
    ),

    MarketEvent(
        timestamp=0.003,
        event_type=EventType.ADD,
        side=Side.ASK,
        price=101.02,
        quantity=300,
    ),

    MarketEvent(
        timestamp=0.004,
        event_type=EventType.ADD,
        side=Side.ASK,
        price=101.03,
        quantity=200,
    ),
]


for event in events:
    book.process_event(event)


print("Best Bid :", book.best_bid)
print("Best Ask :", book.best_ask)

print("Spread   :", spread(book))
print("Mid      :", mid_price(book))

print("Bid Vol  :", bid_volume(book))
print("Ask Vol  :", ask_volume(book))

print("OBI      :", order_book_imbalance(book))