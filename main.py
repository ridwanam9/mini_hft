from src.order_book import OrderBook
from src.market_data import MarketEvent, EventType, Side


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

    print(
        event.timestamp,
        "best_bid =", book.best_bid,
        "best_ask =", book.best_ask,
        "spread =", book.spread,
    )

bids, asks = book.get_depth()

print("BIDS")
for price, quantity in bids:
    print(price, quantity)

print()

print("ASKS")
for price, quantity in asks:
    print(price, quantity)