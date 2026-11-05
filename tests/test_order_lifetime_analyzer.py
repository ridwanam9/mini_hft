import pytest

from src.order_lifetime_analyzer import OrderLifetimeAnalyzer


TIME_STEP = 0.001


def make_order_record(
    status,
    book_entry_time=0.0,
    completion_time=None,
    first_resting_fill_time=None,
    executed_quantity=0,
    remaining_quantity=0,
):
    return {
        "status": status,
        "book_entry_time": book_entry_time,
        "completion_time": completion_time,
        "first_resting_fill_time": first_resting_fill_time,
        "executed_quantity": executed_quantity,
        "remaining_quantity": remaining_quantity,
    }


def make_analyzer(order_history, end_time=0.010):
    return OrderLifetimeAnalyzer(
        order_history=order_history,
        end_time=end_time,
        time_step=TIME_STEP,
    )


def test_filled_order_lifetime():
    order_history = {
        1: make_order_record(
            status="filled",
            book_entry_time=0.001,
            completion_time=0.011,
            first_resting_fill_time=0.005,
            executed_quantity=5,
            remaining_quantity=0,
        )
    }

    analyzer = make_analyzer(order_history)
    observations = analyzer.collect_observations()

    assert len(observations) == 1
    assert observations[0]["order_id"] == 1
    assert observations[0]["status"] == "filled"
    assert observations[0]["lifetime"] == 10
    assert observations[0]["first_fill_age"] == 4
    assert observations[0]["censored"] is False


def test_cancelled_order_lifetime():
    order_history = {
        2: make_order_record(
            status="cancelled",
            book_entry_time=0.002,
            completion_time=0.009,
            executed_quantity=0,
            remaining_quantity=5,
        )
    }

    analyzer = make_analyzer(order_history)
    observations = analyzer.collect_observations()

    assert len(observations) == 1
    assert observations[0]["status"] == "cancelled"
    assert observations[0]["lifetime"] == 7
    assert observations[0]["censored"] is False


def test_ignore_order_that_never_entered_book():
    order_history = {
        3: make_order_record(
            status="submitted",
            book_entry_time=None,
            completion_time=0.005,
        )
    }

    analyzer = make_analyzer(order_history)
    observations = analyzer.collect_observations()

    assert observations == []


def test_active_order_is_treated_as_censored():
    order_history = {
        4: make_order_record(
            status="active",
            book_entry_time=0.002,
            completion_time=None,
            executed_quantity=2,
            remaining_quantity=3,
        )
    }

    analyzer = make_analyzer(order_history, end_time=0.012)
    observations = analyzer.collect_observations()

    assert len(observations) == 1
    assert observations[0]["status"] == "active"
    assert observations[0]["lifetime"] == 10
    assert observations[0]["censored"] is True


def test_kaplan_meier_survival_rate():
    observations = [
        {"lifetime": 2, "censored": False},
        {"lifetime": 4, "censored": False},
        {"lifetime": 4, "censored": True},
    ]

    survival = OrderLifetimeAnalyzer.kaplan_meier(
        observations,
        horizons=[2, 4],
    )

    # Pada event ke-2: 1 dari 3 order selesai.
    assert survival[2] == pytest.approx(2 / 3)

    # Pada event ke-4: 1 dari 2 order yang masih berisiko selesai.
    # Satu order lainnya mengalami censoring pada waktu yang sama.
    assert survival[4] == pytest.approx(1 / 3)


def test_kaplan_meier_handles_tied_event_and_censoring_times():
    observations = [
        {"lifetime": 5, "censored": False},
        {"lifetime": 5, "censored": True},
    ]

    survival = OrderLifetimeAnalyzer.kaplan_meier(
        observations,
        horizons=[5],
    )

    # Event diproses sebelum censoring pada waktu yang sama.
    assert survival[5] == pytest.approx(0.5)


def test_partial_fill_then_cancellation():
    order_history = {
        7: make_order_record(
            status="cancelled",
            book_entry_time=0.001,
            completion_time=0.006,
            first_resting_fill_time=0.003,
            executed_quantity=3,
            remaining_quantity=2,
        )
    }

    analyzer = make_analyzer(order_history)
    observations = analyzer.collect_observations()

    assert len(observations) == 1

    observation = observations[0]

    assert observation["status"] == "cancelled"
    assert observation["lifetime"] == 5
    assert observation["first_fill_age"] == 2
    assert observation["executed_quantity"] == 3
    assert observation["remaining_quantity"] == 2
    assert observation["censored"] is False