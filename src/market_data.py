from dataclasses import dataclass
from enum import Enum


class Side(Enum):
    BID = "bid"
    ASK = "ask"


class EventType(Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    TRADE = "trade"


@dataclass
class MarketEvent:
    timestamp: float
    event_type: EventType
    side: Side
    price: float
    quantity: float


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"


@dataclass
class Order:
    order_id: int
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: float | None = None

@dataclass
class Trade:
    buy_order_id: int
    sell_order_id: int
    price: float
    quantity: int

