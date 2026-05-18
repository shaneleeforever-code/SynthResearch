import unittest
from unittest.mock import patch

from app.interview import INTERVIEW_CONTEXT_CHAR_LIMIT, InterviewEngine
from app.quantitative import build_quant_scoring_prompts
from app.report import generate_quantitative_report


def passthrough_t(text, **kwargs):
    return text.format(**kwargs) if kwargs else text


class FakeTextEngine:
    def __init__(self):
        self.calls = []

    def chat(self, system_prompt, user_prompt, temperature=0.7, max_tokens=2000, json_mode=False):
        self.calls.append((system_prompt, user_prompt, max_tokens))
        return "report"


class LargeSampleGuardsTest(unittest.TestCase):
    def test_1v1_interview_prompt_is_hard_capped(self):
        engine = InterviewEngine(engine=None, personas=[], research_concept="Concept")
        conversation = []
        for _ in range(12):
            conversation.append({"type": "question", "content": "Q" * 1000})
            conversation.append({"type": "answer", "content": "A" * 3000})

        with patch("app.interview.t", passthrough_t):
            prompt = engine._build_user_prompt("Final question", conversation)

        self.assertLessEqual(len(prompt), INTERVIEW_CONTEXT_CHAR_LIMIT + 500)
        self.assertIn("Final question", prompt)

    def test_quant_scoring_prompt_is_bounded_for_verbose_persona(self):
        persona = {
            "name": "A",
            "demographics": {"age": 32, "occupation": "Designer"},
            "psychographics": {"disc_profile": "D" * 1000},
            "behavioral_traits": {
                "frustrations": ["pain" * 500],
                "values": ["value" * 500],
            },
        }
        with patch("app.quantitative.t", passthrough_t):
            system_prompt, user_prompt = build_quant_scoring_prompts(
                persona, "Concept" * 500, ["Purchase Intent", "Trust"]
            )

        self.assertLess(len(system_prompt), 6000)
        self.assertLess(len(user_prompt), 2500)

    def test_quant_report_uses_aggregate_summary_not_all_rows(self):
        import pandas as pd

        df = pd.DataFrame([{"姓名": f"P{i}", "职业": "Role", "DISC": "D", "score": i % 5 + 1} for i in range(100)])
        analysis = {
            "overall_scores": {"score": 3.0},
            "top_supporters": [{"姓名": "P1", "职业": "Role", "DISC": "D", "_avg_score": 5}],
            "top_critics": [{"姓名": "P2", "职业": "Role", "DISC": "S", "_avg_score": 1}],
        }
        engine = FakeTextEngine()

        with patch("app.report.t", passthrough_t):
            report = generate_quantitative_report(engine, "Concept", df, analysis)

        self.assertEqual(report, "report")
        self.assertLess(len(engine.calls[0][1]), 5000)


if __name__ == "__main__":
    unittest.main()
