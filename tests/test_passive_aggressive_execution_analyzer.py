
import pytest

from src.passive_aggressive_execution_analyzer import (
    PassiveAggressiveExecutionAnalyzer,
)


def make_record(
    status="filled",
    original_quantity=10,
    executed_quantity=10,
    remaining_quantity=0,
    aggressive_quantity=0,
    passive_quantity=10,
    book_entry_time=0.001,
):
    return {
        "status": status,
        "original_quantity": original_quantity,
        "executed_quantity": executed_quantity,
        "remaining_quantity": remaining_quantity,
        "aggressive_executed_quantity": aggressive_quantity,
        "passive_executed_quantity": passive_quantity,
        "book_entry_time": book_entry_time,
    }


def make_analyzer(history):
    return PassiveAggressiveExecutionAnalyzer(history)


def test_aggressive_execution_metrics():
    history = {
        1: make_record(
            aggressive_quantity=10,
            passive_quantity=0,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["overall"]["aggressive_executed_quantity"] == 10
    assert result["overall"]["passive_executed_quantity"] == 0
    assert result["overall"]["aggressive_execution_share"] == 1.0


def test_passive_execution_metrics():
    history = {
        1: make_record(
            aggressive_quantity=0,
            passive_quantity=10,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["overall"]["aggressive_executed_quantity"] == 0
    assert result["overall"]["passive_executed_quantity"] == 10
    assert result["overall"]["passive_execution_share"] == 1.0


def test_mixed_execution_metrics():
    history = {
        1: make_record(
            original_quantity=10,
            executed_quantity=7,
            remaining_quantity=3,
            aggressive_quantity=4,
            passive_quantity=3,
        )
    }

    result = make_analyzer(history).analyze()

    overall = result["overall"]

    assert overall["aggressive_executed_quantity"] == 4
    assert overall["passive_executed_quantity"] == 3
    assert overall["total_executed_quantity"] == 7

    assert overall["aggressive_execution_share"] == pytest.approx(4 / 7)
    assert overall["passive_execution_share"] == pytest.approx(3 / 7)

    assert overall["quantity_consistency"] is True


def test_active_and_completed_orders_are_separated():
    history = {
        1: make_record(
            status="filled",
            aggressive_quantity=2,
            passive_quantity=8,
        ),
        2: make_record(
            status="active",
            original_quantity=10,
            executed_quantity=3,
            remaining_quantity=7,
            aggressive_quantity=1,
            passive_quantity=2,
        ),
    }

    result = make_analyzer(history).analyze()

    assert result["completed_orders"] == 1
    assert result["active_orders"] == 1

    assert result["completed"]["total_executed_quantity"] == 10
    assert result["active"]["total_executed_quantity"] == 3


def test_order_that_never_entered_book_is_included():
    history = {
        1: make_record(
            status="filled",
            aggressive_quantity=10,
            passive_quantity=0,
            book_entry_time=None,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["total_orders"] == 1
    assert result["overall"]["aggressive_executed_quantity"] == 10
    assert result["overall"]["passive_executed_quantity"] == 0
    assert result["overall"]["aggressive_execution_share"] == 1.0


def test_inconsistent_execution_quantity_is_detected():
    history = {
        1: make_record(
            executed_quantity=10,
            aggressive_quantity=4,
            passive_quantity=3,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["overall"]["quantity_consistency"] is False

def test_expired_order_without_fill_is_included():
    history = {
        1: make_record(
            status="expired",
            executed_quantity=0,
            remaining_quantity=10,
            aggressive_quantity=0,
            passive_quantity=0,
            book_entry_time=None,
        )
    }

    result = make_analyzer(history).analyze()

    assert result["total_orders"] == 1
    assert result["overall"]["total_executed_quantity"] == 0
    assert result["overall"]["aggressive_execution_share"] is None
    assert result["overall"]["passive_execution_share"] is None