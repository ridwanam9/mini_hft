import pytest

from src.order_execution_analyzer import OrderExecutionAnalyzer


def make_record(
    status,
    original_quantity=10,
    executed_quantity=0,
    remaining_quantity=10,
    book_entry_time=0.001,
    completion_time=None,
    first_fill_time=None,
    first_resting_fill_time=None,
):
    return {
        "status": status,
        "original_quantity": original_quantity,
        "executed_quantity": executed_quantity,
        "remaining_quantity": remaining_quantity,
        "book_entry_time": book_entry_time,
        "completion_time": completion_time,
        "first_fill_time": first_fill_time,
        "first_resting_fill_time": first_resting_fill_time,
    }


def make_analyzer(order_history, end_time=0.020):
    return OrderExecutionAnalyzer(
        order_history=order_history,
        end_time=end_time,
        time_step=0.001,
    )


def test_full_fill_classification():
    history = {
        1: make_record(
            status="filled",
            executed_quantity=10,
            remaining_quantity=0,
            completion_time=0.011,
            first_fill_time=0.005,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["fully_filled"] == 1
    assert result["any_filled"] == 1
    assert result["full_fill_rate"] == 1.0
    assert result["average_fill_ratio_completed"] == 1.0


def test_partial_fill_classification():
    history = {
        1: make_record(
            status="cancelled",
            executed_quantity=4,
            remaining_quantity=6,
            completion_time=0.011,
            first_fill_time=0.005,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["partially_filled"] == 1
    assert result["any_filled"] == 1
    assert result["partial_fill_rate"] == 1.0
    assert result["average_fill_ratio_completed"] == 0.4


def test_no_fill_cancellation():
    history = {
        1: make_record(
            status="cancelled",
            executed_quantity=0,
            remaining_quantity=10,
            completion_time=0.011,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["no_fill_cancelled"] == 1
    assert result["any_filled"] == 0
    assert result["any_fill_rate"] == 0.0


def test_active_order_is_not_counted_as_completed():
    history = {
        1: make_record(
            status="active",
            executed_quantity=0,
            remaining_quantity=10,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["active_orders"] == 1
    assert result["completed_orders"] == 0
    assert result["any_fill_rate"] is None


def test_active_partial_fill_is_included_in_current_fill_ratio():
    history = {
        1: make_record(
            status="active",
            executed_quantity=4,
            remaining_quantity=6,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["active_orders"] == 1
    assert result["average_fill_ratio_all"] == 0.4
    assert result["average_fill_ratio_completed"] is None


def test_first_fill_age():
    history = {
        1: make_record(
            status="filled",
            executed_quantity=10,
            remaining_quantity=0,
            completion_time=0.015,
            first_fill_time=0.004,
            first_resting_fill_time=0.006,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["average_first_fill_age"] == 5
    assert result["median_first_fill_age"] == 5
    

def test_order_that_never_entered_book_is_ignored():
    history = {
        1: make_record(
            status="filled",
            book_entry_time=None,
            executed_quantity=10,
            remaining_quantity=0,
            completion_time=0.010,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["total_resting_orders"] == 0


def test_empty_completed_orders_have_no_rates():
    history = {}

    result = make_analyzer(history).analyze()

    assert result["completed_orders"] == 0
    assert result["any_fill_rate"] is None
    assert result["full_fill_rate"] is None


def test_invalid_time_step_is_rejected():
    with pytest.raises(ValueError):
        OrderExecutionAnalyzer(
            order_history={},
            end_time=0.010,
            time_step=0,
        )

def test_time_to_first_fill_uses_resting_fill_time():
    record = make_record(
        status="filled",
        executed_quantity=10,
        remaining_quantity=0,
        book_entry_time=0.001,
        completion_time=0.012,
        first_fill_time=0.002,
    )

    # Fill pertama terjadi sebelum order masuk ke order book.
    record["first_resting_fill_time"] = 0.007

    history = {1: record}

    result = make_analyzer(history).analyze()

    # Menghitung dari 0.007 - 0.001 = 6 event.
    assert result["average_first_fill_age"] == 6