import random

from src.market_data import(
    MarketEvent,
    EventType,
    Side,
)

class MarketSimulator:


    def __init__(self, start_price = 100.00):
        self.price = start_price

    def generate_event(self, timestamp):
        side = random.choice([
            Side.BID,
            Side.ASK
        ])

        event_type = random.choice([
            EventType.ADD,
            EventType.UPDATE,
            EventType.DELETE,
        ])

        price_offset = random.choice([
            -0.02,
            -0.01,
            0.01,
            0.02,
        ])

        price = round(
            self.price + price_offset,
            2
        )

        quantity = random.randint(
            10,
            500
        )

        return MarketEvent(
            timestamp = timestamp,
            event_type = event_type,
            side = side,
            price = price,
            quantity = quantity,
        )

    