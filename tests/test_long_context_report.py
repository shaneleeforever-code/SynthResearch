import unittest
from unittest.mock import patch

from app.report import _chunk_text_blocks, generate_qualitative_report


def passthrough_t(text, **kwargs):
    return text.format(**kwargs) if kwargs else text


class FakeReportEngine:
    def __init__(self):
        self.calls = []

    def chat_json(self, system_prompt, user_prompt, temperature=0.3, max_tokens=1000):
        self.calls.append(user_prompt)
        if "Chunk" in user_prompt:
            return {
                "summary": "chunk summary",
                "resonance_points": ["liked speed"],
                "opposition_points": ["worried about trust"],
                "improvement_suggestions": ["add proof"],
                "key_quotes": [{"speaker": "P1", "quote": "I need evidence"}],
            }
        return {
            "executive_summary": "final summary",
            "resonance_points": ["liked speed"],
            "opposition_points": ["worried about trust"],
            "improvement_suggestions": ["add proof"],
            "key_insights": [{"title": "Trust", "description": "Trust gates adoption"}],
            "product_evaluation": {"strengths": ["speed"], "weaknesses": ["trust"], "opportunities": ["proof"]},
            "strategic_recommendations": [{"priority": "High", "suggestion": "Add evidence", "impact": "Improve conversion"}],
            "key_quotes": [{"speaker": "P1", "quote": "I need evidence"}],
        }


class LongContextReportTest(unittest.TestCase):
    def test_chunk_text_blocks_keeps_each_chunk_under_limit(self):
        chunks = _chunk_text_blocks(["A" * 60, "B" * 60, "C" * 60], limit=130)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(all(len(chunk) <= 130 for chunk in chunks))

    def test_large_qualitative_report_uses_chunk_summaries_before_final_report(self):
        transcripts = {}
        for p_idx in range(100):
            transcript = []
            for q_idx in range(15):
                transcript.append({"type": "question", "content": f"Question {q_idx} " + "Q" * 80})
                transcript.append({"type": "answer", "content": f"Answer {p_idx}-{q_idx} " + "A" * 400})
            transcripts[f"P{p_idx}"] = transcript

        engine = FakeReportEngine()
        with patch("app.report.t", passthrough_t):
            report = generate_qualitative_report(engine, "Concept", transcripts, None)

        self.assertEqual(report["executive_summary"], "final summary")
        self.assertGreater(len(engine.calls), 1)
        self.assertTrue(all(len(prompt) < 16000 for prompt in engine.calls))


if __name__ == "__main__":
    unittest.main()
