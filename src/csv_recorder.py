import csv

from src.market_state import MarketState


class CSVMarketStateRecorder:
    def __init__(self, filepath):
        self.filepath = filepath

        self.fieldnames = [
            "timestamp",
            "best_bid",
            "best_ask",
            "spread",
            "mid_price",
            "bid_volume",
            "ask_volume",
            "obi",
            "microprice",
            "ofi",
            "last_trade_price",
            "last_trade_quantity",
            "last_trade_aggressor",
        ]

        self.file = None
        self.writer = None

    def start(self):
        self.file = open(
            self.filepath,
            "w",
            newline="",
        )

        self.writer = csv.DictWriter(
            self.file,
            fieldnames=self.fieldnames,
        )

        self.writer.writeheader()

    def record(self, state: MarketState):
        if self.writer is None:
            raise RuntimeError(
                "Recorder has not been started"
            )

        self.writer.writerow({
            "timestamp": state.timestamp,
            "best_bid": state.best_bid,
            "best_ask": state.best_ask,
            "spread": state.spread,
            "mid_price": state.mid_price,
            "bid_volume": state.bid_volume,
            "ask_volume": state.ask_volume,
            "obi": state.obi,
            "microprice": state.microprice,
            "ofi": state.ofi,
            "last_trade_price": state.last_trade_price,
            "last_trade_quantity": state.last_trade_quantity,
            "last_trade_aggressor": state.last_trade_aggressor,
        })

    def close(self):
        if self.file is not None:
            self.file.close()
            self.file = None
            self.writer = None