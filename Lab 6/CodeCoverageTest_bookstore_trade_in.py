"""
Lab 6 - Code (line) coverage tests for bookstore_trade_in.py

Goal: execute every statement in the module at least once.
Each test below is aimed at the specific line(s) that the starter
test left unexecuted (lines 3, 10, 16, 18, 22-23, 33-34, 37-41, 43, 45,
50, 55, 57, 62-74).

Run:
    coverage run -m pytest CodeCoverageTest_bookstore_trade_in.py
    coverage report -m
"""
import pytest
from bookstore_trade_in import process_book_buybacks, inspect_scanner_calibration


def make_batch(books, format_type="paperback", approved=True, in_credit=False):
    """Helper to build a single batch dictionary."""
    return {
        "intake_approved": approved,
        "format": format_type,
        "payout_in_credit": in_credit,
        "books": books,
    }


def book(missing_pages=0, condition="good", counterfeit=False):
    """Helper to build a single book dictionary."""
    return {
        "missing_pages": missing_pages,
        "condition": condition,
        "counterfeit": counterfeit,
    }


# ---------------------------------------------------------------------------
# process_book_buybacks
# ---------------------------------------------------------------------------

def test_single_paperback_good():
    # Starter test: paperback, good condition, no store-credit bonus
    result = process_book_buybacks([make_batch([book()])], 5.0)
    assert result["total_payout"] == 8.0
    assert result["status"] == "COMPLETED"


def test_invalid_batches_raises_value_error():
    # Line 3: batches is not a list
    with pytest.raises(ValueError):
        process_book_buybacks({"not": "a list"}, 5.0)


def test_unapproved_batch_is_skipped():
    # Line 10: batch without intake approval is skipped
    # Line 57: nothing was paid out, so status is ZERO_CREDIT
    result = process_book_buybacks([make_batch([book()], approved=False)], 5.0)
    assert result == {"total_payout": 0.0, "status": "ZERO_CREDIT"}


def test_textbook_mint_with_store_credit_bonus():
    # Line 16: textbook base value 40.0
    # Line 43: mint condition pays 125% -> 50.0
    # Line 50: payout in credit adds the bonus -> 55.0
    batches = [make_batch([book(condition="mint")], "textbook", in_credit=True)]
    result = process_book_buybacks(batches, 5.0)
    assert result["total_payout"] == 55.0
    assert result["status"] == "COMPLETED"


def test_hardcover_poor_condition():
    # Line 18: hardcover base value 15.0
    # Line 45: poor condition pays 40% -> 6.0
    result = process_book_buybacks([make_batch([book(condition="poor")], "hardcover")], 0.0)
    assert result["total_payout"] == 6.0
    assert result["status"] == "COMPLETED"


def test_unknown_format_is_rejected():
    # Lines 22-23: unsupported format rejects the whole batch
    result = process_book_buybacks([make_batch([book()], "audiobook")], 5.0)
    assert result == {"total_payout": 0.0, "status": "ZERO_CREDIT"}


def test_book_with_missing_pages_is_rejected():
    # Lines 33-34: a book with missing pages earns nothing
    batches = [make_batch([book(missing_pages=3), book()], "paperback")]
    result = process_book_buybacks(batches, 0.0)
    assert result["total_payout"] == 8.0
    assert result["status"] == "COMPLETED"


def test_counterfeit_paperback_earns_nothing():
    # Line 37 and line 41: counterfeit non-textbook adds 0.0 and the loop continues
    batches = [make_batch([book(counterfeit=True), book()], "paperback")]
    result = process_book_buybacks(batches, 0.0)
    assert result["total_payout"] == 8.0
    assert result["status"] == "COMPLETED"


def test_counterfeit_textbook_voids_whole_batch():
    # Lines 38-40: a counterfeit textbook wipes the batch credit and stops the batch
    batches = [make_batch([book(condition="mint"), book(counterfeit=True), book()], "textbook")]
    result = process_book_buybacks(batches, 0.0)
    assert result == {"total_payout": 0.0, "status": "ZERO_CREDIT"}


def test_more_than_four_rejections_triggers_audit():
    # Line 55: rejected_items > 4 -> AUDIT_REJECTED (payout is still reported)
    books = [book(missing_pages=1) for _ in range(5)] + [book()]
    result = process_book_buybacks([make_batch(books, "paperback")], 0.0)
    assert result == {"total_payout": 8.0, "status": "AUDIT_REJECTED"}


# ---------------------------------------------------------------------------
# inspect_scanner_calibration
# ---------------------------------------------------------------------------

def test_scanner_no_data():
    # Lines 62-63: empty matrix
    assert inspect_scanner_calibration([]) == "NO_DATA"


def test_scanner_needs_recalibration():
    # Lines 65-71: two consecutive error rates above 5 on one device
    assert inspect_scanner_calibration([[1, 6, 7]]) == "RECALIBRATE"


def test_scanner_is_calibrated():
    # Lines 72-74: an isolated spike resets the streak, all devices pass
    assert inspect_scanner_calibration([[2, 9, 1], [3, 4]]) == "CALIBRATED"
