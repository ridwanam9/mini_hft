
from collections import deque

from src.market_data import Order, OrderSide
from dataclasses import dataclass


@dataclass
class OrderBookSnapshot:
    bids: dict
    asks: dict

    @property
    def best_bid(self):
        return max(self.bids, default=None)

    @property
    def best_ask(self):
        return min(self.asks, default=None)


class OrderBookL3:
    def __init__(self):
        self.bid_orders = {}
        self.ask_orders = {}

        # order_id -> (side, price, order)
        self.order_index = {}
        self.seen_order_ids = set()
        self.order_history = {}

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
        
        if order.order_id not in self.order_history:
            self.order_history[order.order_id] = {
                "order": order,
                "original_quantity": order.quantity,
                "remaining_quantity": order.quantity,
                "status": "active",
                "first_fill_time": None,
                "completion_time": None,
                "executed_quantity": 0,
            }
        else:
            self.order_history[order.order_id]["status"] = "active"
            self.order_history[order.order_id]["remaining_quantity"] = order.quantity

    def cancel_order(self, order_id: int, timestamp=None) -> bool:
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

        history = self.order_history.get(order_id)

        if history is not None:
            history["status"] = "cancelled"

            if timestamp is not None:
                history["completion_time"] = timestamp

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
    
    def snapshot(self):
        return OrderBookSnapshot(
            bids=dict(self.bids),
            asks=dict(self.asks),
        )
