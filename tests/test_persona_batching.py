import re
import unittest
from unittest.mock import patch

from app.persona import generate_personas, get_persona_system_prompt


def passthrough_t(text, **kwargs):
    return text.format(**kwargs) if kwargs else text


class FakeEngine:
    def __init__(self):
        self.calls = []

    def chat_json(self, system_prompt, user_prompt, temperature=0.3, max_tokens=1000):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        match = re.search(r"请生成\s+(\d+)\s+个", user_prompt)
        count = int(match.group(1)) if match else 1
        start = sum(len(call.get("personas", [])) for call in self.calls)
        personas = []
        for idx in range(count):
            personas.append(
                {
                    "name": f"Persona {start + idx + 1}",
                    "demographics": {
                        "age": 25 + idx,
                        "occupation": f"Role {start + idx + 1}",
                        "income": "medium",
                        "location": "City",
                    },
                    "psychographics": {
                        "personality_summary": "pragmatic",
                        "disc_profile": "D",
                        "big_five": {
                            "openness": 3,
                            "conscientiousness": 3,
                            "extraversion": 3,
                            "agreeableness": 3,
                            "neuroticism": 3,
                        },
                    },
                    "behavioral_traits": {
                        "values": ["value"],
                        "goals": ["goal"],
                        "frustrations": ["pain"],
                        "technology_adoption": "mainstream",
                    },
                }
            )
        self.calls[-1]["personas"] = personas
        return {"personas": personas}


class PersonaBatchingTest(unittest.TestCase):
    def test_persona_system_prompt_separates_language_from_geography(self):
        prompt = get_persona_system_prompt()

        self.assertIn("Output language is only a presentation choice", prompt)
        self.assertIn("must NOT imply China", prompt)
        self.assertIn("global, international, worldwide", prompt)

    def test_generates_personas_in_batches_of_five_and_reports_progress(self):
        engine = FakeEngine()
        progress = []

        with patch("app.persona.t", passthrough_t):
            personas = generate_personas(
                engine,
                "目标用户",
                "主概念",
                count=12,
                batch_pause=0,
                progress_callback=lambda done, total, batch, batches: progress.append(
                    (done, total, batch, batches)
                ),
            )

        self.assertEqual(len(personas), 12)
        self.assertEqual(len(engine.calls), 3)
        self.assertIn("请生成 5 个", engine.calls[0]["user_prompt"])
        self.assertIn("请生成 5 个", engine.calls[1]["user_prompt"])
        self.assertIn("请生成 2 个", engine.calls[2]["user_prompt"])
        self.assertIn("语言只决定输出文字", engine.calls[0]["user_prompt"])
        self.assertIn("不要默认生成中国用户", engine.calls[0]["user_prompt"])
        self.assertIn("国家/地区", engine.calls[0]["user_prompt"])
        self.assertEqual(progress, [(5, 12, 1, 3), (10, 12, 2, 3), (12, 12, 3, 3)])

    def test_skips_existing_duplicates_and_generates_top_up_personas(self):
        class DuplicateEngine:
            def __init__(self):
                self.calls = 0

            def chat_json(self, system_prompt, user_prompt, temperature=0.3, max_tokens=1000):
                self.calls += 1
                if self.calls == 1:
                    names = ["Persona 1", "Persona 2"]
                else:
                    names = ["Persona 3"]
                return {
                    "personas": [
                        {
                            "name": name,
                            "demographics": {
                                "age": 30,
                                "occupation": name,
                                "income": "medium",
                                "location": "City",
                            },
                            "psychographics": {
                                "personality_summary": "pragmatic",
                                "disc_profile": "S",
                                "big_five": {},
                            },
                            "behavioral_traits": {},
                        }
                        for name in names
                    ]
                }

        with patch("app.persona.t", passthrough_t):
            personas = generate_personas(
                DuplicateEngine(),
                "目标用户",
                "主概念",
                count=2,
                batch_pause=0,
                existing_personas=[
                    {
                        "name": "Persona 1",
                        "demographics": {"age": 30, "occupation": "Persona 1", "location": "City"},
                        "psychographics": {"disc_profile": "S"},
                    }
                ],
            )

        self.assertEqual([p["name"] for p in personas], ["Persona 2", "Persona 3"])

    def test_retries_a_failed_batch_without_losing_previous_batches(self):
        class FlakyEngine(FakeEngine):
            def __init__(self):
                super().__init__()
                self.failures = 0

            def chat_json(self, system_prompt, user_prompt, temperature=0.3, max_tokens=1000):
                if len(self.calls) == 1 and self.failures == 0:
                    self.failures += 1
                    raise RuntimeError("temporary connection error")
                return super().chat_json(system_prompt, user_prompt, temperature, max_tokens)

        engine = FlakyEngine()
        progress = []

        with patch("app.persona.t", passthrough_t), patch("app.persona.time.sleep"):
            personas = generate_personas(
                engine,
                "目标用户",
                "主概念",
                count=8,
                batch_pause=0,
                progress_callback=lambda done, total, batch, batches: progress.append(
                    (done, total, batch, batches)
                ),
            )

        self.assertEqual(len(personas), 8)
        self.assertEqual(engine.failures, 1)
        self.assertEqual(len(engine.calls), 2)
        self.assertEqual(progress, [(5, 8, 1, 2), (8, 8, 2, 2)])


if __name__ == "__main__":
    unittest.main()
