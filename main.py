
from src.order_book import OrderBook
from src.market_data import Order, OrderSide, OrderType
from src.matching_engine import MatchingEngine


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
