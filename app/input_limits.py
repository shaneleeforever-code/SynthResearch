SAMPLE_MIN = 3
SAMPLE_MAX = 100
SAMPLE_DEFAULT = 10

TARGET_AUDIENCE_MAX_CHARS = 500
CONCEPT_NAME_MAX_CHARS = 50
CONCEPT_DESC_MAX_CHARS = 1500
CHALLENGE_MAX_ITEMS = 10
CHALLENGE_MAX_CHARS = 100
QUESTION_MAX_ITEMS = 15
QUESTION_MAX_CHARS = 200


def clamp_int(value, min_value: int, max_value: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = min_value
    return max(min_value, min(max_value, number))


def _char_units(char: str) -> float:
    return 0.25 if char.isascii() else 1.0


def weighted_text_units(value) -> float:
    return sum(_char_units(char) for char in str(value or "").strip())


def trim_text(value, max_chars: int) -> str:
    text = str(value or "").strip()
    total = 0.0
    result = []
    for char in text:
        total += _char_units(char)
        if total > max_chars:
            break
        result.append(char)
    return "".join(result).strip()


def append_limited_unique(items, value, max_items: int, max_chars: int):
    cleaned = trim_text(value, max_chars)
    if not cleaned or cleaned in items or len(items) >= max_items:
        return False
    items.append(cleaned)
    return True


def normalize_limited_list(items, max_items: int, max_chars: int):
    normalized = []
    for item in items or []:
        append_limited_unique(normalized, item, max_items, max_chars)
    return normalized
