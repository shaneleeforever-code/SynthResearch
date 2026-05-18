"""
SynthResearch - 焦点小组引擎
实现发言链模式 (Reaction Chain) + 冲突控制逻辑
"""

import random
import streamlit as st
from typing import List, Dict, Generator, Tuple
from app.i18n import t

FOCUS_CONTEXT_CHAR_LIMIT = 3000


class FocusGroupEngine:
    """焦点小组讨论引擎"""

    def __init__(self, engine, personas: List[Dict], research_concept: str):
        """
        Args:
            engine: SynthEngine 实例
            personas: Persona 列表
            research_concept: 研究主题
        """
        self.engine = engine
        self.personas = personas
        self.research_concept = research_concept
        self.global_history: List[Dict] = []
        self.round_count = 0

    def _get_disc_primary(self, persona: Dict) -> str:
        """提取 DISC 主导类型"""
        return persona.get("_disc_primary", "S")

    def _generate_behavioral_prompt(self, persona: Dict) -> str:
        """基于大五人格 + DISC 动态生成冲突控制指令"""
        psych = persona.get("psychographics", {})
        big5 = psych.get("big_five", {})
        disc = psych.get("disc_profile", "")

        agreeableness = big5.get("agreeableness", 3)
        openness = big5.get("openness", 3)
        extraversion = big5.get("extraversion", 3)

        # 激化冲突：D 型 / 低宜人性
        if agreeableness <= 2 or "D" in disc.upper().split(",")[0]:
            return t("你非常有主见且挑剔。如果前面的发言与你的痛点不符，请直接且尖锐地提出异议，不要迎合他人。只需用 1-2 句话反驳。")

        # 缓和/补充：S 型 / 高宜人性
        if agreeableness >= 4:
            behavior = t("你比较温和。请在前面发言的基础上，从你的实际生活场景出发进行补充。如果不同意，请委婉表达。")
            # S 型额外柔化
            if "S" in disc.upper():
                behavior += " " + t("你更倾向于维护团队和谐，避免直接冲突。")
            return behavior

        # 转移焦点：高开放性
        if openness >= 4:
            return t("你思维发散、富有想象力。不要纠结于别人讨论的死胡同，尝试引入一个全新的视角或疯狂的想法。")

        # 高外向性：主动
        if extraversion >= 4:
            return t("你健谈活跃。积极回应前面的发言，可以举具体例子来支持或反对，语气生动。")

        # 默认
        return t("基于你的价值观，客观评价前面的发言，提出你的独立见解。")

    def _build_agent_system_prompt(self, persona: Dict) -> str:
        """构建 Agent 的核心 System Prompt"""
        demo = persona.get("demographics", {})
        psych = persona.get("psychographics", {})
        traits = persona.get("behavioral_traits", {})
        behavior_rule = self._generate_behavioral_prompt(persona)

        return t("Focus Group Agent Prompt",
            name=persona.get('name', t('未知')),
            age=demo.get('age', '?'),
            occupation=demo.get('occupation', t('未知')),
            location=demo.get('location', t('未知')),
            household=demo.get('household_structure', ''),
            pains=', '.join(traits.get('frustrations', [])),
            values=', '.join(traits.get('values', [])),
            goals=', '.join(traits.get('goals', [])),
            behavior=behavior_rule,
            concept=self.research_concept
        )

    def _check_cooldown(self) -> bool:
        """检查是否需要主持人降温（连续3次含冲突词汇）"""
        if len(self.global_history) < 4:
            return False
        recent = self.global_history[-3:]
        conflict_keywords = [t("不同意"), t("但是"), t("反对"), t("不对"), t("错了"), t("胡说"), t("扯淡"), t("不可能")]
        conflict_count = sum(
            1 for msg in recent
            if msg["speaker"] != "Moderator" and any(kw in msg["content"] for kw in conflict_keywords)
        )
        return conflict_count >= 3

    def _build_context_text(self, question: str) -> str:
        context_lines = [t("【当前讨论上下文】"), f"{t('主持人')}: {question}"]
        for msg in self.global_history[-5:]:
            if msg["speaker"] != t("主持人") or msg["content"] != question:
                context_lines.append(f"{msg['speaker']}: {msg['content']}")
        context_text = "\n".join(context_lines)
        if len(context_text) > FOCUS_CONTEXT_CHAR_LIMIT:
            keep_head = f"{t('【当前讨论上下文】')}\n{t('主持人')}: {question}\n"
            remaining = max(0, FOCUS_CONTEXT_CHAR_LIMIT - len(keep_head))
            context_text = keep_head + "..." + context_text[-remaining:]
        return context_text

    def run_round(self, question: str) -> Generator[Dict, None, None]:
        """
        执行一轮焦点话题讨论（生成器模式，逐条输出）

        Args:
            question: 主持人提出的问题

        Yields:
            {"speaker": str, "content": str, "persona": dict|None, "type": "moderator"|"agent"}
        """
        self.round_count += 1

        # 主持人发问
        moderator_msg = {"speaker": t("主持人"), "content": question, "persona": None, "type": "moderator"}
        self.global_history.append({"speaker": t("主持人"), "content": question})
        yield moderator_msg

        # 打乱发言顺序
        round_personas = list(self.personas)
        random.shuffle(round_personas)

        for idx, persona in enumerate(round_personas):
            # 检查是否需要降温
            if self._check_cooldown():
                cooldown_content = t("好的，我们看到了不同观点的碰撞。让我们把焦点拉回来——关于这个话题，还有谁想从自己的实际经历出发补充一下？")
                cooldown_msg = {
                    "speaker": t("主持人"),
                    "content": cooldown_content,
                    "persona": None,
                    "type": "moderator",
                }
                self.global_history.append({"speaker": t("主持人"), "content": cooldown_content})
                yield cooldown_msg

            context_text = self._build_context_text(question)

            # Agent System Prompt
            system_prompt = self._build_agent_system_prompt(persona)

            # User Prompt
            length_rule = t("Length Rule Focus")
            if idx == 0:
                p_name = persona.get('name', t('未知'))
                user_prompt = f"{t('主持人刚刚提出了一个问题')}：{question}\n\n{t('作为 {name}，请根据你的痛点和经历给出你的看法。', name=p_name)}\n\n{length_rule}"
            else:
                user_prompt = f"{context_text}\n\n{t('作为 {name}，请根据上下文和你自己的立场给出你的看法。', name=persona.get('name', t('未知')))}\n\n{length_rule}"

            # 调用 API
            try:
                answer = self.engine.chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.85,
                    max_tokens=600,
                )
            except Exception as e:
                answer = f"({t('发言失败')}：{str(e)[:50]})"

            # 推入全局记录
            self.global_history.append({"speaker": persona.get("name", t("未知")), "content": answer})

            yield {
                "speaker": persona.get("name", t("未知")),
                "content": answer,
                "persona": persona,
                "type": "agent",
            }

    def run_round_stream(self, question: str) -> Generator[Tuple[str, str], None, None]:
        """
        流式执行一轮讨论（用于 Streamlit 实时展示）

        Yields:
            (speaker_name, content_chunk)
        """
        for msg in self.run_round(question):
            yield (msg["speaker"], msg["content"])

    def get_discussion_summary(self) -> str:
        """获取讨论摘要"""
        if not self.global_history:
            return t("暂无讨论记录")

        lines = []
        for msg in self.global_history:
            lines.append(f"{msg['speaker']}: {msg['content']}")
        return "\n".join(lines)

    def reset(self):
        """重置讨论状态"""
        self.global_history = []
        self.round_count = 0
