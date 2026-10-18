from pathlib import Path

from src.simulation import Simulation
from src.csv_recorder import CSVMarketStateRecorder


def run_simulation(
    num_events=1_000,
    seed=42,
):
    simulation = Simulation(
        seed=seed,
        start_price=100.0,
        tick_size=0.01,
        time_step=0.001,
    )

    states = simulation.run(num_events)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "market_states.csv"

    recorder = CSVMarketStateRecorder(output_file)

    recorder.start()

    for state in states:
        recorder.record(state)

    recorder.close()

    return output_file


if __name__ == "__main__":
    output_file = run_simulation(
        num_events=1_000,
        seed=42,
    )

    print(f"Dataset created: {output_file}")