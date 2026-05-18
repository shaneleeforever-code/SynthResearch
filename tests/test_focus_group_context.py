import unittest
from unittest.mock import patch

from app.focus_group import FOCUS_CONTEXT_CHAR_LIMIT, FocusGroupEngine


def passthrough_t(text, **kwargs):
    return text.format(**kwargs) if kwargs else text


class FocusGroupContextTest(unittest.TestCase):
    def test_discussion_context_is_hard_capped(self):
        with patch("app.focus_group.t", passthrough_t):
            fg = FocusGroupEngine(engine=None, personas=[], research_concept="Concept")
            fg.global_history = [
                {"speaker": f"P{i}", "content": "A" * 2000}
                for i in range(10)
            ]

            context = fg._build_context_text("Question")

        self.assertLessEqual(len(context), FOCUS_CONTEXT_CHAR_LIMIT + 200)
        self.assertIn("Question", context)


if __name__ == "__main__":
    unittest.main()
