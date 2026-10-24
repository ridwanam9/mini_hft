from src.market_data import Order, OrderSide, OrderType, Trade
from src.trade_tape import TradeRecord

class MatchingEngineL3:
    def __init__(self, book):
        self.book = book
        self.trades = []
        self.trade_tape = []

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

        # Register order in historical order tracking.
        self.book.order_history[order.order_id] = {
            "order": order,
            "original_quantity": order.quantity,
            "remaining_quantity": order.quantity,
            "status": "submitted",
            "first_fill_time": None,
            "completion_time": None,
            "executed_quantity": 0,
        }

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

            self.trade_tape.append(
                TradeRecord(
                    timestamp=order.timestamp,
                    price=best_price,
                    quantity=executed,
                    aggressor=(
                        "BUY"
                        if order.side == OrderSide.BUY
                        else "SELL"
                    ),
                    buy_order_id=buy_id,
                    sell_order_id=sell_id,
                )
            )

            # -------------------------------------------------
            # Update historical order tracking
            # -------------------------------------------------

            incoming_history = self.book.order_history[order.order_id]
            resting_history = self.book.order_history[resting.order_id]

            if incoming_history["first_fill_time"] is None:
                incoming_history["first_fill_time"] = order.timestamp

            if resting_history["first_fill_time"] is None:
                resting_history["first_fill_time"] = order.timestamp

            incoming_history["executed_quantity"] += executed
            incoming_history["remaining_quantity"] -= executed

            resting_history["executed_quantity"] += executed
            resting_history["remaining_quantity"] -= executed

            # Update actual order quantities.
            resting.quantity -= executed
            remaining -= executed

            # -------------------------------------------------
            # Resting order completely filled
            # -------------------------------------------------

            if resting.quantity == 0:
                resting_history["status"] = "filled"
                resting_history["completion_time"] = order.timestamp

                queue.popleft()
                del self.book.order_index[resting.order_id]

                if not queue:
                    del opposite[best_price]

        # -----------------------------------------------------
        # Incoming order completely filled
        # -----------------------------------------------------

        if remaining == 0:
            incoming_history = self.book.order_history[order.order_id]

            incoming_history["status"] = "filled"
            incoming_history["completion_time"] = order.timestamp

        # Market order could not consume all available liquidity.
        if remaining > 0 and order.order_type == OrderType.MARKET:
            incoming_history = self.book.order_history[order.order_id]

            incoming_history["status"] = "expired"
            incoming_history["remaining_quantity"] = remaining
            incoming_history["completion_time"] = order.timestamp

        # -----------------------------------------------------
        # Unfilled limit quantity rests in the book.
        # -----------------------------------------------------

        if remaining > 0 and order.order_type == OrderType.LIMIT:
            order.quantity = remaining

            incoming_history = self.book.order_history[order.order_id]

            incoming_history["remaining_quantity"] = remaining
            incoming_history["status"] = "active"

            self.book.add_resting_order(order)

        self.trades.extend(fills)

        return fills