from .market_data import MarketEvent, EventType, Side


class OrderBook:

    def __init__(self):
        self.bids = {}
        self.asks = {}

    def process_event(self, event: MarketEvent):

        if event.event_type == EventType.TRADE:
            return

        book = self.bids if event.side == Side.BID else self.asks

        if event.event_type == EventType.ADD:
            book[event.price] = event.quantity

        elif event.event_type == EventType.UPDATE:
            book[event.price] = event.quantity

        elif event.event_type == EventType.DELETE:
            book.pop(event.price, None)
    

    @property
    def best_bid(self):
        if not self.bids:
            return None

        return max(self.bids.keys())

    @property
    def best_ask(self):
        if not self.asks:
            return None

        return min(self.asks.keys())

    @property
    def spread(self):

        if self.best_bid is None or self.best_ask is None:
            return None

        return self.best_ask - self.best_bid