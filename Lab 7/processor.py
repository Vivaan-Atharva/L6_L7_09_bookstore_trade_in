import math

ISBN_DIGITS = "0123456789"

CONDITION_MULTIPLIERS = {
    "MINT": 1.25,
    "LIKE_NEW": 1.00,
    "VERY_GOOD": 0.80,
    "GOOD": 0.60,
    "POOR": 0.30,
}


def verify_isbn10_format(isbn_str):
    """Summarise a valid ISBN-10, or return None if the input is not one.

    Fixes: None/non-string input, too short or too long values (IndexError),
    a non-digit first character (ValueError), non-ASCII digits, and a
    check character that is not a digit or X or does not match the checksum.
    """
    if not isinstance(isbn_str, str):
        return None

    cleaned = isbn_str.strip().replace('-', '').replace(' ', '')
    if len(cleaned) != 10:
        return None

    body = cleaned[:9]
    check_char = cleaned[9].upper()
    if any(ch not in ISBN_DIGITS for ch in body):
        return None
    if check_char not in ISBN_DIGITS and check_char != "X":
        return None

    total = sum((10 - i) * int(d) for i, d in enumerate(body))
    total += 10 if check_char == "X" else int(check_char)
    if total % 11 != 0:
        return None

    first_digit = int(cleaned[0])
    group_code = cleaned[1:4]
    return f"Group {group_code}: Starts {first_digit}, Checksum {check_char}"


def calculate_depreciation_factor(book_age_str):
    """Return the depreciation factor (0.1 to 1.0) for "age/lifespan", or None if invalid.

    Fixes: None/non-string input, missing or extra "/" (unpack ValueError),
    non-numeric parts (ValueError), a lifespan of 0 (ZeroDivisionError),
    nan/inf values, and negative ages or lifespans that produced factors above 1.0.
    """
    if not isinstance(book_age_str, str):
        return None

    parts = book_age_str.split('/')
    if len(parts) != 2:
        return None

    try:
        age = float(parts[0])
        life = float(parts[1])
    except ValueError:
        return None

    if not (math.isfinite(age) and math.isfinite(life)):
        return None
    if age < 0 or life <= 0:
        return None

    depreciation = 1.0 - (age / life)
    return round(min(1.0, max(0.1, depreciation)), 2)


def lookup_condition_multiplier(condition_code):
    """Return the price multiplier for a condition grade, or None if the grade is unknown.

    Fixes: None/non-string input and unknown grades (KeyError). Spaces and
    hyphens are read as underscores, so "like new" and "very-good" also work.
    """
    if not isinstance(condition_code, str):
        return None

    grade = condition_code.strip().upper().replace(' ', '_').replace('-', '_')
    return CONDITION_MULTIPLIERS.get(grade)


def read_input(prompt):
    """input() that returns an empty string instead of crashing when input ends."""
    try:
        return input(prompt)
    except EOFError:
        return ""


def main():
    print("==== Running verify_isbn10_format ====")
    isbn_in = read_input("Enter ISBN-10 (e.g. 0-306-40615-2): ")
    isbn_result = verify_isbn10_format(isbn_in)
    if isbn_result is None:
        print("Invalid ISBN-10: expected 9 digits plus a check digit or X, with a valid checksum.")
    else:
        print(isbn_result)

    print("\n==== Running calculate_depreciation_factor ====")
    age_in = read_input("Enter age/lifespan in years (e.g. 3/10): ")
    factor = calculate_depreciation_factor(age_in)
    if factor is None:
        print("Invalid input: use age/lifespan with numbers, age >= 0 and lifespan > 0 (e.g. 3/10).")
    else:
        print("Depreciation Factor:", factor)

    print("\n==== Running lookup_condition_multiplier ====")
    cond_in = read_input("Enter condition (e.g. MINT, GOOD, POOR): ")
    multiplier = lookup_condition_multiplier(cond_in)
    if multiplier is None:
        print("Unknown condition. Choose one of: " + ", ".join(CONDITION_MULTIPLIERS) + ".")
    else:
        print("Multiplier:", multiplier)


if __name__ == "__main__":
    main()
