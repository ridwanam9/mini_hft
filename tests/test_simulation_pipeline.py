import csv

from src.simulation import Simulation
from src.csv_recorder import CSVMarketStateRecorder


def test_simulation_to_csv_pipeline(tmp_path):

    simulation = Simulation(
        seed=42,
        start_price=100.0,
        tick_size=0.01,
        time_step=0.001,
    )

    states = simulation.run(100)

    filepath = tmp_path / "market_states.csv"

    recorder = CSVMarketStateRecorder(filepath)

    recorder.start()

    for state in states:
        recorder.record(state)

    recorder.close()

    with open(filepath, newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 100

    assert rows[0]["timestamp"] == "0.001"

    assert rows[-1]["timestamp"] == "0.1"