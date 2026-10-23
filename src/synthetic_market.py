import random

from src.market_data import Order, OrderSide, OrderType


class SyntheticMarket:
    def __init__(
        self,
        start_price=100.0,
        tick_size=0.01,
        time_step=0.001,
        seed=None,
    ):
        self.fair_value = start_price

        self.tick_size = tick_size
        self.timestamp = 0.0
        self.time_step = time_step
        self.event_count = 0
        self.order_id = 1

        self.random = random.Random(seed)

    def next_order_id(self):
        order_id = self.order_id
        self.order_id += 1
        return order_id

    def next_timestamp(self):
        self.event_count += 1
        self.timestamp = round(
            self.event_count * self.time_step,
            10,
        )
        return self.timestamp

    def update_fair_value(self):
        """
        Random walk sederhana.

        Fair value bergerak 0, +1 tick,
        atau -1 tick pada setiap event.
        """

        move = self.random.choice([-1, 0, 1])

        self.fair_value += move * self.tick_size

        self.fair_value = round(
            self.fair_value,
            10,
        )

    def generate_limit_buy(self):
        self.update_fair_value()

        price = (
            self.fair_value
            - self.tick_size
            * self.random.randint(1, 5)
        )

        quantity = self.random.randint(10, 100)

        return Order(
            order_id=self.next_order_id(),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=round(price, 10),
            timestamp=self.next_timestamp(),
        )

    def generate_limit_sell(self):
        self.update_fair_value()

        price = (
            self.fair_value
            + self.tick_size
            * self.random.randint(1, 5)
        )

        quantity = self.random.randint(10, 100)

        return Order(
            order_id=self.next_order_id(),
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=round(price, 10),
            timestamp=self.next_timestamp(),
        )

    def generate_market_buy(self):
        self.update_fair_value()

        quantity = self.random.randint(10, 100)

        return Order(
            order_id=self.next_order_id(),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=quantity,
            timestamp=self.next_timestamp(),
        )

    def generate_market_sell(self):
        self.update_fair_value()

        quantity = self.random.randint(10, 100)

        return Order(
            order_id=self.next_order_id(),
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=quantity,
            timestamp=self.next_timestamp(),
        )

    def generate_order(self):
        event = self.random.choice(
            [
                "limit_buy",
                "limit_sell",
                "market_buy",
                "market_sell",
            ]
        )

        if event == "limit_buy":
            return self.generate_limit_buy()

        if event == "limit_sell":
            return self.generate_limit_sell()

        if event == "market_buy":
            return self.generate_market_buy()

        return self.generate_market_sell()
    