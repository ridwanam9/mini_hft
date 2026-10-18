import csv

from src.csv_recorder import CSVMarketStateRecorder
from src.market_state import MarketState


def test_csv_recorder_writes_market_state(tmp_path):

    filepath = tmp_path / "market_states.csv"

    recorder = CSVMarketStateRecorder(filepath)

    recorder.start()

    state = MarketState(
        timestamp=0.001,

        best_bid=101.00,
        best_ask=101.02,

        spread=0.02,
        mid_price=101.01,

        bid_volume=100,
        ask_volume=150,

        obi=-0.20,
        microprice=101.008,

        ofi=50,

        last_trade_price=101.02,
        last_trade_quantity=50,
        last_trade_aggressor="BUY",
    )

    recorder.record(state)
    recorder.close()

    with open(filepath, newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1

    row = rows[0]

    assert float(row["timestamp"]) == 0.001
    assert float(row["best_bid"]) == 101.00
    assert float(row["best_ask"]) == 101.02

    assert float(row["spread"]) == 0.02
    assert float(row["mid_price"]) == 101.01

    assert int(row["bid_volume"]) == 100
    assert int(row["ask_volume"]) == 150

    assert float(row["obi"]) == -0.20
    assert float(row["ofi"]) == 50

    assert float(row["last_trade_price"]) == 101.02
    assert int(row["last_trade_quantity"]) == 50

    assert row["last_trade_aggressor"] == "BUY"



    