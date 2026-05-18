"""
SynthResearch - Persona 生成引擎
基于大五人格 + DISC 模型生成高保真合成用户画像
"""

import json
import streamlit as st
import time
from typing import List, Dict, Optional
from app.i18n import t

PERSONA_BATCH_SIZE = 5

def get_persona_system_prompt() -> str:
    """获取 Persona 生成的 System Prompt"""
    return t("Persona System Prompt")

def _extract_personas(result) -> List[Dict]:
    if isinstance(result, dict):
        personas = result.get("personas", [])
    elif isinstance(result, list):
        personas = result
    else:
        personas = []
    return [p for p in personas if isinstance(p, dict)]

def _mark_disc_primary(personas: List[Dict]) -> None:
    # 为每个 persona 补充 DISC 主导类型标记（用于 UI 颜色映射）
    for p in personas:
        disc = p.get("psychographics", {}).get("disc_profile", "")
        if "D" in disc.upper().split(",")[0] or "DOMINANT" in disc.upper():
            p["_disc_primary"] = "D"
        elif "I" in disc.upper().split(",")[0] or "INFLUENCE" in disc.upper():
            p["_disc_primary"] = "I"
        elif "S" in disc.upper().split(",")[0] or "STEADINESS" in disc.upper():
            p["_disc_primary"] = "S"
        elif "C" in disc.upper().split(",")[0] or "CONSCIENTIOUS" in disc.upper():
            p["_disc_primary"] = "C"
        else:
            p["_disc_primary"] = "S"  # 默认

def _persona_signature(persona: Dict) -> str:
    demo = persona.get("demographics", {})
    psych = persona.get("psychographics", {})
    parts = [
        persona.get("name", ""),
        str(demo.get("age", "")),
        demo.get("occupation", ""),
        demo.get("location", ""),
        psych.get("disc_profile", ""),
    ]
    return "|".join(str(part).strip().lower() for part in parts if str(part).strip())

def _summarize_existing_personas(personas: List[Dict], limit: int = 12) -> str:
    summaries = []
    for persona in personas[-limit:]:
        demo = persona.get("demographics", {})
        psych = persona.get("psychographics", {})
        summaries.append(
            f"{persona.get('name', t('未知'))} / "
            f"{demo.get('age', '?')}{t('岁')} / "
            f"{demo.get('occupation', t('未知'))} / "
            f"{demo.get('location', t('未知'))} / "
            f"{psych.get('disc_profile', t('未知'))}"
        )
    return "\n".join(summaries)

def _build_persona_prompt(
    target_audience: str,
    research_concept: str,
    batch_count: int,
    total_count: int,
    batch_index: int,
    total_batches: int,
    challenges_text: str,
    existing_personas: List[Dict],
) -> str:
    user_prompt = f"{t('请生成 {n} 个不同的目标用户画像。', n=batch_count)}\n\n"
    user_prompt += f"{t('这些用户必须符合以下基础描述：')} \"{target_audience}\"\n"
    user_prompt += f"{t('当前的研究主题/概念是：')} \"{research_concept}\"{challenges_text}\n\n"
    user_prompt += t(
        "这是第 {batch}/{total_batches} 批，整体目标样本量为 {total}。请把本批视为总体样本的一部分，而不是孤立样本。",
        batch=batch_index,
        total_batches=total_batches,
        total=total_count,
    ) + "\n"
    user_prompt += t(
        "语言只决定输出文字，不决定用户画像的国家、地区、族裔或文化背景。必须优先遵循目标用户描述中的地域范围；如果描述包含“全球”“海外”“国际”“worldwide”“global”等含义，应生成跨国家、跨地区、跨文化背景的画像，不要默认生成中国用户。"
    ) + "\n"
    user_prompt += t(
        "本批多样性要求：优先覆盖尚未出现的人群段，确保年龄、职业、国家/地区、城市层级、收入、家庭结构、DISC、技术接受度分散；姓名、所在地、职业和生活方式应与该画像的真实文化背景一致。每个画像都应有不同动机、痛点和决策风格。"
    ) + "\n"
    if existing_personas:
        user_prompt += f"\n{t('已生成画像摘要（不要重复姓名、职业、年龄组合或人格组合）：')}\n"
        user_prompt += _summarize_existing_personas(existing_personas) + "\n"
    user_prompt += "\n" + t("Persona Generation Requirements")
    return user_prompt

def generate_personas(
    engine,
    target_audience: str,
    research_concept: str,
    count: int = 5,
    challenges: Optional[List[str]] = None,
    existing_personas: Optional[List[Dict]] = None,
    progress_callback=None,
    batch_size: int = PERSONA_BATCH_SIZE,
    batch_retries: int = 3,
    batch_pause: float = 0.8,
) -> List[Dict]:
    """
    生成合成用户画像
    """
    if count <= 0:
        return []

    challenges_text = ""
    if challenges:
        challenges_text = f"\n{t('当前研究主题相关的预设挑战/痛点包括：')}{'; '.join(challenges)}"

    batch_size = max(1, min(PERSONA_BATCH_SIZE, batch_size))
    total_batches = (count + batch_size - 1) // batch_size
    generated: List[Dict] = []
    context_personas = list(existing_personas or [])
    seen = {_persona_signature(p) for p in context_personas if _persona_signature(p)}

    batch_index = 0
    max_attempts = total_batches + 2
    while len(generated) < count and batch_index < max_attempts:
        batch_index += 1
        remaining = count - len(generated)
        batch_count = min(batch_size, remaining)
        visible_batch_index = min(batch_index, total_batches)
        user_prompt = _build_persona_prompt(
            target_audience=target_audience,
            research_concept=research_concept,
            batch_count=batch_count,
            total_count=count,
            batch_index=visible_batch_index,
            total_batches=total_batches,
            challenges_text=challenges_text,
            existing_personas=context_personas + generated,
        )

        last_error = None
        for attempt in range(1, batch_retries + 1):
            try:
                result = engine.chat_json(
                    system_prompt=get_persona_system_prompt(),
                    user_prompt=user_prompt,
                    temperature=0.8,
                    max_tokens=4000,
                )
                break
            except Exception as e:
                last_error = e
                if attempt >= batch_retries:
                    raise RuntimeError(
                        t(
                            "第 {batch}/{batches} 批画像生成失败，已完成 {done}/{total}。请稍后重试。",
                            batch=visible_batch_index,
                            batches=total_batches,
                            done=len(generated),
                            total=count,
                        )
                    ) from e
                time.sleep(2 * attempt)

        batch_personas = _extract_personas(result)
        accepted = []
        for persona in batch_personas:
            signature = _persona_signature(persona)
            if signature and signature in seen:
                continue
            if signature:
                seen.add(signature)
            accepted.append(persona)
            if len(generated) + len(accepted) >= count:
                break

        _mark_disc_primary(accepted)
        generated.extend(accepted)

        if progress_callback:
            progress_callback(len(generated), count, visible_batch_index, total_batches)

        if len(generated) < count and batch_pause > 0:
            time.sleep(batch_pause)

    return generated[:count]


def generate_ai_questions(
    engine,
    target_audience: str,
    research_concept: str,
    comparison_concepts: Optional[List[Dict]] = None,
    personas_summary: str = "",
    count: int = 5,
) -> List[str]:
    """
    AI 自动生成访谈问题
    """
    system_prompt = t("Questions Generation System Prompt")

    user_prompt = f"{t('目标受众')}：{target_audience}\n"
    user_prompt += f"{t('研究概念')}：{research_concept}\n"
    if comparison_concepts:
        user_prompt += f"{t('对照概念')}：\n"
        for idx, concept in enumerate(comparison_concepts, start=1):
            name = concept.get("name", "").strip()
            desc = concept.get("description", "").strip()
            user_prompt += f"{idx}. {name}: {desc}\n"
        user_prompt += t("Comparison Question Requirement") + "\n"
    if personas_summary:
        user_prompt += f"{t('已有画像特征摘要')}：{personas_summary}\n"
    
    user_prompt += f"\n{t('Please generate {n} high-quality interview questions. Output JSON.', n=count)}"

    result = engine.chat_json(system_prompt, user_prompt, temperature=0.3)
    if isinstance(result, dict):
        ai_questions = result.get("questions")
    elif isinstance(result, list):
        ai_questions = result
    else:
        ai_questions = []
    if not ai_questions:
        for val in result.values():
            if isinstance(val, list):
                ai_questions = val
                break
    if not ai_questions:
        ai_questions = []
        
    return [q for q in ai_questions if isinstance(q, str)]


def get_persona_summary(persona: Dict) -> str:
    """获取 Persona 的简短摘要文本"""
    name = persona.get("name", t("未知"))
    demo = persona.get("demographics", {})
    age = demo.get("age", "?")
    occ = demo.get("occupation", t("未知"))
    disc = persona.get("psychographics", {}).get("disc_profile", t("未知"))
    values = ", ".join(persona.get("behavioral_traits", {}).get("values", [])[:2])
    return f"{name}（{age}{t('岁')}，{occ}，{disc}，{t('核心价值观')}：{values}）"


def build_interview_system_prompt(persona: Dict, research_concept: str) -> str:
    """构建用于访谈的 Agent System Prompt"""
    demo = persona.get("demographics", {})
    psych = persona.get("psychographics", {})
    big5 = psych.get("big_five", {})
    traits = persona.get("behavioral_traits", {})

    return t("Interview System Prompt",
        name=persona.get('name', t('未知')),
        age=demo.get('age', '?'),
        location=demo.get('location', t('未知')),
        occupation=demo.get('occupation', t('未知')),
        income=demo.get('income', t('未知')),
        household=demo.get('household_structure', t('未知')),
        disc=psych.get('disc_profile', t('未知')),
        openness=big5.get('openness', 3),
        conscientiousness=big5.get('conscientiousness', 3),
        extraversion=big5.get('extraversion', 3),
        agreeableness=big5.get('agreeableness', 3),
        neuroticism=big5.get('neuroticism', 3),
        decision_style=psych.get('personality_summary', t('未知')),
        values=', '.join(traits.get('values', [])),
        frustrations=', '.join(traits.get('frustrations', [])),
        goals=', '.join(traits.get('goals', [])),
        challenges=', '.join(traits.get('challenges', [])),
        tech_adoption=traits.get('technology_adoption', t('未知')),
        concept=research_concept
    )
