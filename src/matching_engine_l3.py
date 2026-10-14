
from src.market_data import Order, OrderSide, OrderType, Trade


class MatchingEngineL3:
    def __init__(self, book):
        self.book = book
        self.trades = []

    def submit_order(self, order: Order) -> list[Trade]:
        if order.order_id in self.book.seen_order_ids:
            raise ValueError("Duplicate order ID")

        if order.quantity <= 0:
            raise ValueError("Quantity must be positive")

        if order.order_type == OrderType.LIMIT:
            if order.price is None or order.price <= 0:
                raise ValueError("Limit order needs a positive price")

        elif order.order_type == OrderType.MARKET:
            if order.price is not None:
                raise ValueError("Market order must not specify a price")

        else:
            raise ValueError("Unsupported order type")

        self.book.seen_order_ids.add(order.order_id)

        fills = []
        remaining = order.quantity

        opposite = (
            self.book.ask_orders
            if order.side == OrderSide.BUY
            else self.book.bid_orders
        )

        while remaining > 0 and opposite:
            best_price = (
                min(opposite)
                if order.side == OrderSide.BUY
                else max(opposite)
            )

            # Stop if the best price exceeds the limit.
            if order.order_type == OrderType.LIMIT:
                if (
                    order.side == OrderSide.BUY
                    and best_price > order.price
                ):
                    break

                if (
                    order.side == OrderSide.SELL
                    and best_price < order.price
                ):
                    break

            queue = opposite[best_price]
            resting = queue[0]

            executed = min(remaining, resting.quantity)

            if order.side == OrderSide.BUY:
                buy_id = order.order_id
                sell_id = resting.order_id
            else:
                buy_id = resting.order_id
                sell_id = order.order_id

            fills.append(
                Trade(
                    buy_order_id=buy_id,
                    sell_order_id=sell_id,
                    price=best_price,
                    quantity=executed,
                )
            )

            resting.quantity -= executed
            remaining -= executed

            if resting.quantity == 0:
                queue.popleft()
                del self.book.order_index[resting.order_id]

                if not queue:
                    del opposite[best_price]

        # Unfilled limit quantity rests in the book.
        if remaining > 0 and order.order_type == OrderType.LIMIT:
            order.quantity = remaining
            self.book.add_resting_order(order)

        self.trades.extend(fills)
        return fills
