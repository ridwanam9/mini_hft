
from collections import deque

from src.market_data import Order, OrderSide


class OrderBookL3:
    def __init__(self):
        self.bid_orders = {}
        self.ask_orders = {}

        # order_id -> (side, price, order)
        self.order_index = {}
        self.seen_order_ids = set()

    @property
    def bids(self):
        return {
            price: sum(order.quantity for order in queue)
            for price, queue in self.bid_orders.items()
        }

    @property
    def asks(self):
        return {
            price: sum(order.quantity for order in queue)
            for price, queue in self.ask_orders.items()
        }

    @property
    def best_bid(self):
        return max(self.bid_orders, default=None)

    @property
    def best_ask(self):
        return min(self.ask_orders, default=None)

    @property
    def spread(self):
        if self.best_bid is None or self.best_ask is None:
            return None

        return self.best_ask - self.best_bid

    def add_resting_order(self, order: Order):
        if order.quantity <= 0:
            raise ValueError("Quantity must be positive")

        if order.price is None:
            raise ValueError("Resting order requires a price")

        if order.order_id in self.order_index:
            raise ValueError("Duplicate active order ID")

        levels = (
            self.bid_orders
            if order.side == OrderSide.BUY
            else self.ask_orders
        )

        if order.price not in levels:
            levels[order.price] = deque()

        levels[order.price].append(order)

        self.order_index[order.order_id] = (
            order.side,
            order.price,
            order,
        )

    def cancel_order(self, order_id: int) -> bool:
        entry = self.order_index.get(order_id)

        if entry is None:
            return False

        side, price, order = entry

        levels = (
            self.bid_orders
            if side == OrderSide.BUY
            else self.ask_orders
        )

        queue = levels[price]
        queue.remove(order)

        if not queue:
            del levels[price]

        del self.order_index[order_id]
        return True

    def get_depth(self, levels=5):
        bids = sorted(
            self.bids.items(),
            reverse=True,
        )[:levels]

        asks = sorted(
            self.asks.items(),
        )[:levels]

        return bids, asks
