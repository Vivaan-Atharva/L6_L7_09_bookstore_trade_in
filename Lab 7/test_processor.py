"""
Lab 7 - Fuzz testing processor.py with Hypothesis

The first three tests are the starter "must not crash" fuzz tests, completed
with try/except. The tests after them use targeted strategies to drive each
function into edge cases that plain random text rarely hits (ISBN-shaped
strings, numeric age/lifespan pairs, real condition codes in odd casing).

Run:
    pytest test_processor.py
"""
from hypothesis import given, strategies as st
from processor import verify_isbn10_format, calculate_depreciation_factor, lookup_condition_multiplier

KNOWN_GRADES = {
    "MINT": 1.25,
    "LIKE_NEW": 1.00,
    "VERY_GOOD": 0.80,
    "GOOD": 0.60,
    "POOR": 0.30,
}


def call_without_crash(func, value):
    """Call func(value); turn any exception into a clear test failure."""
    try:
        return func(value)
    except Exception as e:
        assert False, f"{func.__name__}({value!r}) crashed with {type(e).__name__}: {e}"


def isbn10_check_char(first_nine):
    """Correct ISBN-10 check character for nine digits."""
    total = sum((10 - i) * int(d) for i, d in enumerate(first_nine))
    check = (11 - total % 11) % 11
    return "X" if check == 10 else str(check)


# ---------------------------------------------------------------------------
# Starter tests: random text or None must never crash any function
# ---------------------------------------------------------------------------

@given(st.text() | st.none())
def test_verify_isbn10_format_no_crash(s):
    try:
        verify_isbn10_format(s)
    except Exception as e:
        assert False, f"verify_isbn10_format crashed with: {type(e).__name__}: {e}"


@given(st.text() | st.none())
def test_calculate_depreciation_factor_safe(s):
    try:
        calculate_depreciation_factor(s)
    except Exception as e:
        assert False, f"calculate_depreciation_factor crashed with: {type(e).__name__}: {e}"


@given(st.text() | st.none())
def test_lookup_condition_multiplier_safe(s):
    try:
        lookup_condition_multiplier(s)
    except Exception as e:
        assert False, f"lookup_condition_multiplier crashed with: {type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# verify_isbn10_format: targeted edge cases
# ---------------------------------------------------------------------------

@given(st.text(alphabet="0123456789Xx- ", max_size=16))
def test_isbn_shaped_strings_never_crash(s):
    # Digits, X and separators in random lengths: empty, too short, too long,
    # X in the first position, only hyphens...
    call_without_crash(verify_isbn10_format, s)


@given(st.text(alphabet="0123456789", max_size=20).filter(lambda s: len(s) != 10))
def test_wrong_length_isbn_is_not_accepted(s):
    result = call_without_crash(verify_isbn10_format, s)
    assert not (isinstance(result, str) and result.startswith("Group")), \
        f"{s!r} has {len(s)} digits but was accepted as an ISBN-10: {result!r}"


@given(st.text(alphabet=st.characters(categories=("Nd",)), min_size=10, max_size=10))
def test_non_ascii_digits_are_not_accepted(s):
    # str.isdigit()/int() accept digits from other scripts (e.g. Arabic-Indic),
    # which are not valid in an ISBN.
    result = call_without_crash(verify_isbn10_format, s)
    if isinstance(result, str) and result.startswith("Group"):
        assert s.isascii(), f"non-ASCII digits {s!r} were accepted as an ISBN-10: {result!r}"


@given(st.text(alphabet="0123456789", min_size=9, max_size=9),
       st.sampled_from(["plain", "hyphenated", "padded"]))
def test_valid_isbn10_is_accepted(first_nine, style):
    isbn = first_nine + isbn10_check_char(first_nine)
    if style == "hyphenated":
        text = f"{isbn[0]}-{isbn[1:4]}-{isbn[4:9]}-{isbn[9]}"
    elif style == "padded":
        text = f"  {isbn}  "
    else:
        text = isbn
    result = call_without_crash(verify_isbn10_format, text)
    assert result == f"Group {isbn[1:4]}: Starts {isbn[0]}, Checksum {isbn[9]}"


# ---------------------------------------------------------------------------
# calculate_depreciation_factor: targeted edge cases
# ---------------------------------------------------------------------------

numbers = st.integers(-1000, 1000) | st.floats(allow_nan=True, allow_infinity=True)


@given(numbers, numbers)
def test_depreciation_factor_stays_between_0_1_and_1(age, life):
    # Covers lifespan 0 (division by zero), negative ages and lifespans,
    # nan and inf. A valid result must always be a factor in [0.1, 1.0].
    text = f"{age}/{life}"
    result = call_without_crash(calculate_depreciation_factor, text)
    if result is not None:
        assert 0.1 <= result <= 1.0, f"{text!r} gave factor {result} outside [0.1, 1.0]"


@given(st.lists(st.integers(0, 50).map(str), min_size=0, max_size=4).map("/".join))
def test_depreciation_wrong_number_of_parts_never_crash(text):
    # "", "3", "3/10/2", "1/2/3/4": anything but exactly one "/"
    call_without_crash(calculate_depreciation_factor, text)


@given(st.integers(0, 100), st.integers(0, 100), st.integers(1, 100))
def test_older_books_never_depreciate_less(age_a, age_b, life):
    younger, older = sorted((age_a, age_b))
    young_factor = call_without_crash(calculate_depreciation_factor, f"{younger}/{life}")
    old_factor = call_without_crash(calculate_depreciation_factor, f"{older}/{life}")
    assert young_factor >= old_factor


# ---------------------------------------------------------------------------
# lookup_condition_multiplier: targeted edge cases
# ---------------------------------------------------------------------------

@given(st.sampled_from(sorted(KNOWN_GRADES)),
       st.sampled_from([str.lower, str.upper, str.title]),
       st.text(alphabet=" \t", max_size=3),
       st.text(alphabet=" \t", max_size=3))
def test_known_grades_in_any_case_with_padding(grade, change_case, left, right):
    text = left + change_case(grade) + right
    assert call_without_crash(lookup_condition_multiplier, text) == KNOWN_GRADES[grade]


@given(st.text())
def test_unknown_grades_return_no_multiplier_or_a_known_one(s):
    result = call_without_crash(lookup_condition_multiplier, s)
    assert result is None or result in KNOWN_GRADES.values()
