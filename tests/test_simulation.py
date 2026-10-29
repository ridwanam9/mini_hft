from src.simulation import Simulation
from src.market_data import Order, OrderSide, OrderType

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

def test_cancellation_protects_last_order_on_each_side():
    sim = Simulation(seed=42)

    sim.engine.submit_order(
        Order(
            order_id=1001,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=10,
            price=99.0,
            timestamp=0.001,
        )
    )

    sim.engine.submit_order(
        Order(
            order_id=1002,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=10,
            price=101.0,
            timestamp=0.002,
        )
    )

    assert sim.get_cancellable_order_ids() == []

    sim.engine.submit_order(
        Order(
            order_id=1003,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=10,
            price=98.0,
            timestamp=0.003,
        )
    )

    eligible = sim.get_cancellable_order_ids()

    assert 1001 in eligible or 1003 in eligible
    assert 1002 not in eligible