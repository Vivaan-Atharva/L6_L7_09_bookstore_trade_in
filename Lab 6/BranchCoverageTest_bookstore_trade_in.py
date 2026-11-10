"""
Lab 6 - Branch coverage tests for bookstore_trade_in.py

Goal: make every decision in the module evaluate to BOTH True and False,
and make every loop run zero times, normally to completion, and (where the
code allows it) exit early. Tests are grouped by the decision they target,
with the line number from bookstore_trade_in.py in each heading.

Run:
    coverage run --branch -m pytest BranchCoverageTest_bookstore_trade_in.py
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


# ===========================================================================
# process_book_buybacks
# ===========================================================================

# --- Line 2: if not isinstance(batches, list) or store_credit_bonus < 0 -----

@pytest.mark.parametrize("bad_batches", [None, {}, (), "batches"])
def test_non_list_batches_raise(bad_batches):
    # True branch via the first operand
    with pytest.raises(ValueError):
        process_book_buybacks(bad_batches, 5.0)


def test_negative_bonus_raises():
    # True branch via the second operand (batches IS a list)
    with pytest.raises(ValueError):
        process_book_buybacks([make_batch([book()])], -0.01)


def test_zero_bonus_is_allowed():
    # False branch at the boundary: bonus of exactly 0 is valid
    result = process_book_buybacks([make_batch([book()], in_credit=True)], 0.0)
    assert result == {"total_payout": 8.0, "status": "COMPLETED"}


# --- Line 8: for batch in batches (zero iterations) ------------------------

def test_empty_batch_list_gives_zero_credit():
    # Loop body never runs; falls straight through to the status checks
    assert process_book_buybacks([], 5.0) == {"total_payout": 0.0, "status": "ZERO_CREDIT"}


# --- Line 9: if not batch.get("intake_approved", False) ----------------------

def test_unapproved_batch_skipped_but_approved_batch_counted():
    # True branch (skip) and False branch (process) in the same call
    batches = [
        make_batch([book(condition="mint")], "textbook", approved=False),
        make_batch([book()], "paperback", approved=True),
    ]
    assert process_book_buybacks(batches, 5.0) == {"total_payout": 8.0, "status": "COMPLETED"}


def test_missing_intake_flag_defaults_to_not_approved():
    batch = {"format": "hardcover", "books": [book()]}
    assert process_book_buybacks([batch], 5.0) == {"total_payout": 0.0, "status": "ZERO_CREDIT"}


# --- Lines 15/17/19: format_type == textbook / hardcover / paperback / else -

@pytest.mark.parametrize("format_type, expected", [
    ("textbook", 40.0),
    ("hardcover", 15.0),
    ("paperback", 8.0),
])
def test_each_supported_format_base_value(format_type, expected):
    result = process_book_buybacks([make_batch([book()], format_type)], 0.0)
    assert result == {"total_payout": expected, "status": "COMPLETED"}


def test_missing_format_defaults_to_paperback():
    batch = {"intake_approved": True, "books": [book()]}
    assert process_book_buybacks([batch], 0.0) == {"total_payout": 8.0, "status": "COMPLETED"}


def test_unknown_format_rejects_batch_once_without_reading_books():
    # else branch: one rejection for the batch, its books are never evaluated
    batches = [make_batch([book(missing_pages=2)] * 5, "magazine")]
    result = process_book_buybacks(batches, 5.0)
    assert result == {"total_payout": 0.0, "status": "ZERO_CREDIT"}  # 1 rejection, not 5


def test_format_is_case_sensitive():
    result = process_book_buybacks([make_batch([book()], "Textbook")], 0.0)
    assert result["status"] == "ZERO_CREDIT"


# --- Line 27: for book in books (zero iterations) --------------------------

def test_approved_batch_with_no_books_pays_only_bonus():
    result = process_book_buybacks([make_batch([], "textbook", in_credit=True)], 7.5)
    assert result == {"total_payout": 7.5, "status": "COMPLETED"}


def test_batch_without_books_key():
    batch = {"intake_approved": True, "format": "hardcover"}
    assert process_book_buybacks([batch], 0.0) == {"total_payout": 0.0, "status": "ZERO_CREDIT"}


# --- Line 32: if pages_missing > 0 ------------------------------------------

def test_missing_pages_boundary():
    # 0 missing pages -> False branch (accepted); 1 missing page -> True branch (rejected)
    batches = [make_batch([book(missing_pages=0), book(missing_pages=1)], "hardcover")]
    assert process_book_buybacks(batches, 0.0) == {"total_payout": 15.0, "status": "COMPLETED"}


def test_book_with_no_fields_uses_defaults():
    # missing_pages=0, condition="good", counterfeit=False
    assert process_book_buybacks([make_batch([{}], "hardcover")], 0.0)["total_payout"] == 15.0


def test_missing_pages_checked_before_counterfeit():
    # A counterfeit textbook with missing pages is rejected by the page check,
    # so it never reaches the counterfeit branch and does NOT void the batch.
    batches = [make_batch([book(condition="mint"), book(missing_pages=4, counterfeit=True)], "textbook")]
    assert process_book_buybacks(batches, 0.0) == {"total_payout": 50.0, "status": "COMPLETED"}


# --- Line 36 / 38: if is_counterfeit -> if format_type == "textbook" --------

def test_counterfeit_textbook_breaks_and_wipes_earlier_credit():
    # True/True: earlier mint credit is reset, later good book is never reached
    batches = [make_batch([book(condition="mint"), book(counterfeit=True), book()], "textbook")]
    assert process_book_buybacks(batches, 0.0) == {"total_payout": 0.0, "status": "ZERO_CREDIT"}


def test_counterfeit_textbook_still_gets_credit_bonus():
    # After the break, the payout_in_credit check still runs
    batches = [make_batch([book(), book(counterfeit=True)], "textbook", in_credit=True)]
    assert process_book_buybacks(batches, 4.0) == {"total_payout": 4.0, "status": "COMPLETED"}


def test_counterfeit_textbook_only_voids_its_own_batch():
    batches = [
        make_batch([book(counterfeit=True)], "textbook"),
        make_batch([book()], "textbook"),
    ]
    assert process_book_buybacks(batches, 0.0) == {"total_payout": 40.0, "status": "COMPLETED"}


@pytest.mark.parametrize("format_type, expected", [("hardcover", 15.0), ("paperback", 8.0)])
def test_counterfeit_non_textbook_continues_loop(format_type, expected):
    # True/False: counterfeit earns 0.0 but the next book is still paid
    batches = [make_batch([book(counterfeit=True), book()], format_type)]
    assert process_book_buybacks(batches, 0.0) == {"total_payout": expected, "status": "COMPLETED"}


def test_counterfeit_overrides_mint_condition():
    batches = [make_batch([book(condition="mint", counterfeit=True)], "hardcover")]
    assert process_book_buybacks(batches, 0.0)["status"] == "ZERO_CREDIT"


# --- Lines 42/44: condition == "mint" / "poor" / else -----------------------

@pytest.mark.parametrize("format_type, condition, expected", [
    ("textbook", "mint", 50.0),
    ("textbook", "poor", 16.0),
    ("textbook", "good", 40.0),
    ("hardcover", "mint", 18.75),
    ("hardcover", "poor", 6.0),
    ("hardcover", "good", 15.0),
    ("paperback", "mint", 10.0),
    ("paperback", "poor", 3.2),
    ("paperback", "good", 8.0),
    ("paperback", "fair", 8.0),   # unknown condition falls into the else branch
])
def test_condition_multipliers(format_type, condition, expected):
    result = process_book_buybacks([make_batch([book(condition=condition)], format_type)], 0.0)
    assert result == {"total_payout": expected, "status": "COMPLETED"}


def test_float_total_is_rounded_to_two_decimals():
    # 3 x 3.2 = 9.600000000000001 in floating point
    batches = [make_batch([book(condition="poor")] * 3, "paperback")]
    assert process_book_buybacks(batches, 0.0)["total_payout"] == 9.6


# --- Line 49: if batch.get("payout_in_credit", False) -----------------------

def test_credit_bonus_added_per_batch_in_credit():
    batches = [
        make_batch([book()], "paperback", in_credit=True),
        make_batch([book()], "paperback", in_credit=True),
        make_batch([book()], "paperback", in_credit=False),
    ]
    assert process_book_buybacks(batches, 2.5)["total_payout"] == 29.0  # 3*8 + 2*2.5


def test_missing_payout_flag_means_no_bonus():
    batch = {"intake_approved": True, "format": "paperback", "books": [book()]}
    assert process_book_buybacks([batch], 100.0)["total_payout"] == 8.0


# --- Lines 54/56: final status ----------------------------------------------

def test_exactly_four_rejections_is_not_audited():
    books = [book(missing_pages=1)] * 4 + [book()]
    result = process_book_buybacks([make_batch(books)], 0.0)
    assert result == {"total_payout": 8.0, "status": "COMPLETED"}


def test_five_rejections_across_batches_is_audited():
    # rejections accumulate across batches: 2 + 1 (unknown format) + 2 = 5
    batches = [
        make_batch([book(missing_pages=1), book(counterfeit=True), book()], "hardcover"),
        make_batch([book()], "comic"),
        make_batch([book(missing_pages=2), book(counterfeit=True)], "paperback"),
    ]
    assert process_book_buybacks(batches, 0.0) == {"total_payout": 15.0, "status": "AUDIT_REJECTED"}


def test_audit_takes_priority_over_zero_credit():
    batches = [make_batch([book(missing_pages=1)] * 5)]
    assert process_book_buybacks(batches, 0.0) == {"total_payout": 0.0, "status": "AUDIT_REJECTED"}


def test_zero_credit_when_nothing_paid():
    batches = [make_batch([book(counterfeit=True)], "paperback")]
    assert process_book_buybacks(batches, 0.0) == {"total_payout": 0.0, "status": "ZERO_CREDIT"}


def test_completed_when_paid_and_few_rejections():
    batches = [make_batch([book(condition="mint")], "hardcover", in_credit=True)]
    assert process_book_buybacks(batches, 1.25) == {"total_payout": 20.0, "status": "COMPLETED"}


# ===========================================================================
# inspect_scanner_calibration
# ===========================================================================

# --- Line 62: if not scanner_matrix ------------------------------------------

@pytest.mark.parametrize("empty", [[], None])
def test_scanner_no_data(empty):
    assert inspect_scanner_calibration(empty) == "NO_DATA"


def test_matrix_with_empty_device_is_not_no_data():
    # matrix is truthy, inner loop runs zero times
    assert inspect_scanner_calibration([[]]) == "CALIBRATED"


# --- Line 68: if error_rate > 5 ----------------------------------------------

def test_error_rate_of_exactly_five_is_ok():
    assert inspect_scanner_calibration([[5, 5, 5, 5]]) == "CALIBRATED"


def test_error_rate_just_above_five_counts():
    assert inspect_scanner_calibration([[5.1, 5.1]]) == "RECALIBRATE"


# --- Line 70: if misread_streak >= 2 -----------------------------------------

def test_single_high_reading_at_end_does_not_trigger():
    # streak reaches 1 (False branch) and the loop then ends
    assert inspect_scanner_calibration([[1, 2, 9]]) == "CALIBRATED"


def test_alternating_spikes_reset_streak():
    assert inspect_scanner_calibration([[9, 1, 9, 1, 9]]) == "CALIBRATED"


def test_two_consecutive_high_readings_trigger():
    assert inspect_scanner_calibration([[1, 6, 7, 1]]) == "RECALIBRATE"


# --- Line 65/66: streak resets for each device -------------------------------

def test_streak_does_not_carry_over_between_devices():
    # device 1 ends on a spike, device 2 starts with one: still not consecutive
    assert inspect_scanner_calibration([[1, 9], [9, 1]]) == "CALIBRATED"


def test_later_device_triggers_recalibration():
    assert inspect_scanner_calibration([[1, 2], [], [3, 8, 9]]) == "RECALIBRATE"


def test_all_devices_calibrated():
    assert inspect_scanner_calibration([[0, 1, 2], [3, 4, 5], [6, 0, 6]]) == "CALIBRATED"
