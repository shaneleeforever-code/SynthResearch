import unittest

from app.input_limits import (
    CHALLENGE_MAX_CHARS,
    CHALLENGE_MAX_ITEMS,
    CONCEPT_DESC_MAX_CHARS,
    CONCEPT_NAME_MAX_CHARS,
    QUESTION_MAX_CHARS,
    QUESTION_MAX_ITEMS,
    SAMPLE_DEFAULT,
    SAMPLE_MAX,
    SAMPLE_MIN,
    append_limited_unique,
    clamp_int,
    normalize_limited_list,
    trim_text,
    weighted_text_units,
)


class InputLimitsTest(unittest.TestCase):
    def test_sample_limits_are_consistent(self):
        self.assertEqual((SAMPLE_MIN, SAMPLE_MAX, SAMPLE_DEFAULT), (3, 100, 10))
        self.assertEqual(clamp_int(1, SAMPLE_MIN, SAMPLE_MAX), 3)
        self.assertEqual(clamp_int(101, SAMPLE_MIN, SAMPLE_MAX), 100)

    def test_text_and_list_limits(self):
        self.assertEqual(CONCEPT_NAME_MAX_CHARS, 50)
        self.assertEqual(CONCEPT_DESC_MAX_CHARS, 1500)

        self.assertLessEqual(weighted_text_units(trim_text("中" * 80, 50)), 50)
        self.assertEqual(len(trim_text("a" * 220, 50)), 200)

        challenges = []
        for idx in range(CHALLENGE_MAX_ITEMS + 2):
            append_limited_unique(challenges, f"挑战{idx}" * 30, CHALLENGE_MAX_ITEMS, CHALLENGE_MAX_CHARS)
        self.assertEqual(len(challenges), 10)
        self.assertTrue(all(weighted_text_units(item) <= 100 for item in challenges))

        questions = normalize_limited_list(
            [f"问题{idx}" * 100 for idx in range(QUESTION_MAX_ITEMS + 1)],
            QUESTION_MAX_ITEMS,
            QUESTION_MAX_CHARS,
        )
        self.assertEqual(len(questions), 15)
        self.assertTrue(all(weighted_text_units(item) <= 200 for item in questions))


if __name__ == "__main__":
    unittest.main()
