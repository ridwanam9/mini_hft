from src.simulation import Simulation


def test_simulation_generates_market_states():
    simulation = Simulation(
        seed=42,
        start_price=100.0,
    )

    states = simulation.run(100)

    assert len(states) == 100


def test_simulation_produces_unique_timestamps():
    simulation = Simulation(
        seed=42,
    )

    states = simulation.run(100)

    timestamps = [
        state.timestamp
        for state in states
    ]

    assert len(timestamps) == len(set(timestamps))


def test_simulation_records_valid_market_state():
    simulation = Simulation(
        seed=42,
    )

    states = simulation.run(100)

    for state in states:
        assert state.timestamp > 0

        assert state.bid_volume >= 0
        assert state.ask_volume >= 0

        assert -1 <= state.obi <= 1

        assert state.last_trade_quantity >= 0