"""
SynthResearch - 1v1 深度访谈引擎
多 Agent 独立并行访谈执行
"""

from typing import List, Dict, Generator
from app.persona import build_interview_system_prompt
from app.i18n import t

INTERVIEW_CONTEXT_CHAR_LIMIT = 3500


class InterviewEngine:
    """1v1 深度访谈引擎"""

    def __init__(self, engine, personas: List[Dict], research_concept: str):
        self.engine = engine
        self.personas = personas
        self.research_concept = research_concept
        self.interviews: Dict[str, List[Dict]] = {}  # persona_id -> 对话列表

    def _build_user_prompt(self, question: str, conversation: list) -> str:
        length_rule = t("Length Rule")
        if conversation:
            history_text = "\n".join([
                f"{t('调研员') if msg['type'] == 'question' else t('你')}: {msg['content']}"
                for msg in conversation[-6:]
            ])
            if len(history_text) > INTERVIEW_CONTEXT_CHAR_LIMIT:
                history_text = "..." + history_text[-INTERVIEW_CONTEXT_CHAR_LIMIT:]
            return f"{t('之前的对话')}：\n{history_text}\n\n{t('调研员现在问你')}：{question}\n\n{length_rule}"
        else:
            return f"{t('调研员问你')}：{question}\n\n{t('请基于你的经历和感受自然地回答。')}\n\n{length_rule}"

    def run_interview(
        self,
        persona: Dict,
        questions: List[str],
    ) -> Generator[Dict, None, None]:
        """
        对单个 Persona 执行完整访谈
        """
        persona_id = persona.get("id", persona.get("name", "unknown"))
        self.interviews[persona_id] = []

        system_prompt = build_interview_system_prompt(persona, self.research_concept)
        conversation = []

        for q_idx, question in enumerate(questions):
            yield {"speaker": t("调研员"), "content": question, "type": "question"}

            user_prompt = self._build_user_prompt(question, conversation)

            try:
                answer = self.engine.chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.75,
                    max_tokens=800,
                )
            except Exception as e:
                answer = f"（{t('回答失败')}：{str(e)[:50]}）"

            conversation.append({"type": "question", "content": question})
            conversation.append({"type": "answer", "content": answer})
            self.interviews[persona_id] = conversation.copy()

            yield {"speaker": persona.get("name", t("未知")), "content": answer, "type": "answer"}

    def run_interview_stream(
        self,
        persona: Dict,
        questions: List[str],
    ) -> Generator[Dict, None, None]:
        """
        流式访谈执行
        """
        persona_id = persona.get("id", persona.get("name", "unknown"))
        self.interviews[persona_id] = []

        system_prompt = build_interview_system_prompt(persona, self.research_concept)
        conversation = []

        for q_idx, question in enumerate(questions):
            yield {"speaker": t("调研员"), "content": question, "type": "question", "stream": False}

            user_prompt = self._build_user_prompt(question, conversation)

            full_answer = ""
            try:
                for chunk in self.engine.chat_stream(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.75,
                    max_tokens=800,
                ):
                    full_answer += chunk
                    yield {
                        "speaker": persona.get("name", t("未知")),
                        "content": chunk,
                        "type": "answer_chunk",
                        "stream": True,
                    }
            except Exception as e:
                full_answer = f"（{t('回答失败')}：{str(e)[:50]}）"
                yield {
                    "speaker": persona.get("name", t("未知")),
                    "content": full_answer,
                    "type": "answer",
                    "stream": False,
                }

            conversation.append({"type": "question", "content": question})
            conversation.append({"type": "answer", "content": full_answer})
            self.interviews[persona_id] = conversation.copy()

            yield {
                "speaker": persona.get("name", t("未知")),
                "content": full_answer,
                "type": "answer_complete",
                "stream": False,
            }

    def get_all_transcripts(self) -> Dict[str, List[Dict]]:
        return self.interviews
