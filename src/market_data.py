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