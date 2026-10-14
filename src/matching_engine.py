
from src.market_data import Order, OrderSide, OrderType, Trade


class MatchingEngine:
    def __init__(self, book):
        self.book = book
        self.trades = []

    def submit_order(self, order: Order) -> list[Trade]:
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

        fills = []
        remaining = order.quantity

        # BUY consumes ASK; SELL consumes BID.
        opposite_book = (
            self.book.asks
            if order.side == OrderSide.BUY
            else self.book.bids
        )

        while remaining > 0 and opposite_book:
            best_price = (
                min(opposite_book)
                if order.side == OrderSide.BUY
                else max(opposite_book)
            )

            # A limit order cannot execute beyond its limit price.
            if order.order_type == OrderType.LIMIT:
                if order.side == OrderSide.BUY and best_price > order.price:
                    break

                if order.side == OrderSide.SELL and best_price < order.price:
                    break

            available = opposite_book[best_price]
            executed = min(remaining, available)

            if order.side == OrderSide.BUY:
                trade = Trade(
                    buy_order_id=order.order_id,
                    sell_order_id=0,
                    price=best_price,
                    quantity=executed,
                )
            else:
                trade = Trade(
                    buy_order_id=0,
                    sell_order_id=order.order_id,
                    price=best_price,
                    quantity=executed,
                )

            opposite_book[best_price] -= executed

            if opposite_book[best_price] == 0:
                del opposite_book[best_price]

            fills.append(trade)
            remaining -= executed

        # Unfilled market quantity is cancelled.
        # Unfilled limit quantity rests on the book.
        if remaining > 0 and order.order_type == OrderType.LIMIT:
            own_book = (
                self.book.bids
                if order.side == OrderSide.BUY
                else self.book.asks
            )

            own_book[order.price] = (
                own_book.get(order.price, 0) + remaining
            )

        self.trades.extend(fills)
        return fills
