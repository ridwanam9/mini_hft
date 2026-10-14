
from src.order_book import OrderBook
from src.market_data import Order, OrderSide, OrderType
from src.matching_engine import MatchingEngine
from src.order_book_l3 import OrderBookL3
from src.matching_engine_l3 import MatchingEngineL3


book = OrderBook()
engine = MatchingEngine(book)

# Populate the ask side with resting limit orders.
engine.submit_order(
    Order(
        order_id=1,
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        price=101.02,
        quantity=100,
    )
)

engine.submit_order(
    Order(
        order_id=2,
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        price=101.03,
        quantity=200,
    )
)

print("Before market buy:", book.asks)

# A market buy consumes 100 at 101.02
# and another 50 at 101.03.
fills = engine.submit_order(
    Order(
        order_id=3,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=150,
    )
)

print("\nTrades:")
for trade in fills:
    print(
        f"Price={trade.price:.2f}, "
        f"Quantity={trade.quantity}"
    )

print("\nAfter market buy:", book.asks)
print("Best ask:", book.best_ask)
print("Best bid:", book.best_bid)




book = OrderBook()
engine = MatchingEngine(book)

engine.submit_order(
    Order(
        order_id=10,
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        price=101.02,
        quantity=100,
    )
)

fills = engine.submit_order(
    Order(
        order_id=11,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        price=101.03,
        quantity=150,
    )
)

for trade in fills:
    print(trade)

print("Remaining asks:", book.asks)
print("Remaining bids:", book.bids)


book = OrderBookL3()
engine = MatchingEngineL3(book)

# Two separate sell orders at the same price.
engine.submit_order(
    Order(101, OrderSide.SELL, OrderType.LIMIT, 100, 101.02)
)
engine.submit_order(
    Order(102, OrderSide.SELL, OrderType.LIMIT, 150, 101.02)
)

print("Ask depth before:", book.get_depth())

fills = engine.submit_order(
    Order(201, OrderSide.BUY, OrderType.MARKET, 120)
)

print("\nTrades:")
for trade in fills:
    print(trade)

print("\nAsk depth after:", book.get_depth())
print("Active order IDs:", list(book.order_index))

