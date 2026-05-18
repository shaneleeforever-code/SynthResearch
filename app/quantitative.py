"""
SynthResearch - 定量概念验证引擎
批量 Persona 生成 + 打分题 + 统计分析
"""

import json
import pandas as pd
from typing import List, Dict, Optional
from app.i18n import t


QUANT_SCORING_SYSTEM_CHAR_LIMIT = 5000
QUANT_SCORING_USER_CHAR_LIMIT = 2000


def _clip_text(value, limit: int) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else "..." + text[-limit:]


def build_quant_scoring_prompts(persona: Dict, concept: str, scoring_dimensions: List) -> tuple[str, str]:
    demo = persona.get("demographics", {})
    psych = persona.get("psychographics", {})
    traits = persona.get("behavioral_traits", {})
    extras = persona.get("extra_constraints", [])
    extra_text = f"\n{t('额外约束：')}{', '.join(extras)}" if extras else ""

    dim_names = [d["name"] if isinstance(d, dict) else d for d in scoring_dimensions]
    dims_text = "\n".join([f"- {name}" for name in dim_names])
    dim_schema = {name: t("1-5整数") for name in dim_names}

    system_prompt = t(
        "Scoring System Prompt",
        concept=_clip_text(concept, 1800),
        dims=_clip_text(dims_text, 1200),
        schema=json.dumps(dim_schema, ensure_ascii=False, indent=2),
    )
    user_prompt = t(
        "Scoring User Prompt",
        name=persona.get("name", t("未知")),
        age=demo.get("age", "?"),
        occupation=demo.get("occupation", t("未知")),
        disc=_clip_text(psych.get("disc_profile", t("未知")), 500),
        pains=_clip_text(", ".join([str(p) for p in traits.get("frustrations", [])]), 500),
        values=_clip_text(", ".join([str(v) for v in traits.get("values", [])]), 500),
        extras=_clip_text(extra_text, 300),
    )
    return (
        _clip_text(system_prompt, QUANT_SCORING_SYSTEM_CHAR_LIMIT),
        _clip_text(user_prompt, QUANT_SCORING_USER_CHAR_LIMIT),
    )


def generate_quant_personas(engine, target_audience: str, count: int = 50) -> List[Dict]:
    """
    批量生成广泛分布的随机画像（定量模式）
    分批生成，每批最多 10 个
    """
    all_personas = []
    batch_size = min(10, count)
    batches = (count + batch_size - 1) // batch_size

    system_prompt = """你是一位社会学家。请生成多样化的用户画像。
要求：年龄、性别、职业、性格必须高度分散，避免集中在某一类人群。
返回 JSON 格式：{"personas": [...]}
每个 persona 结构：
{
  "id": "Q001",
  "name": "中文全名",
  "demographics": {"age": 数字, "gender": "性别", "occupation": "职业", "location": "城市"},
  "psychographics": {
    "big_five": {"openness": 1-5, "conscientiousness": 1-5, "extraversion": 1-5, "agreeableness": 1-5, "neuroticism": 1-5},
    "disc_profile": "类型描述"
  },
  "behavioral_traits": {"values": ["价值观"], "frustrations": ["痛点"]}
}"""

    for batch_idx in range(batches):
        remaining = count - len(all_personas)
        current_batch = min(batch_size, remaining)
        if current_batch <= 0:
            break

        user_prompt = f"""请生成 {current_batch} 个符合"{target_audience}"的随机用户画像。
这是第 {batch_idx + 1} 批（共 {batches} 批），请确保与之前批次不重复。
ID 从 Q{len(all_personas) + 1:03d} 开始编号。
输出 JSON。"""

        try:
            result = engine.chat_json(system_prompt, user_prompt, temperature=0.9, max_tokens=4000)
            batch_personas = result.get("personas", [])
            all_personas.extend(batch_personas)
        except Exception as e:
            print(f"批次 {batch_idx + 1} 生成失败: {e}")

    return all_personas[:count]


def run_quantitative_scoring(
    engine,
    personas: List[Dict],
    concept: str,
    scoring_dimensions: List[Dict],
    progress_callback=None,
) -> pd.DataFrame:
    """
    批量执行定量打分

    Args:
        engine: SynthEngine 实例
        personas: Persona 列表
        concept: 待验证概念描述
        scoring_dimensions: 打分维度列表，如 [{"name": "购买意愿", "description": "..."}]

    Returns:
        DataFrame，每行一个 persona，每列一个维度的得分
    """
    dimensions_text = "\n".join([
        f"- {d} (请打1-5分)"
        for d in scoring_dimensions
    ])

    dim_schema = {d: "1-5整数" for d in scoring_dimensions}

    system_prompt = f"""你是一个模拟用户。请基于你的身份背景，对以下概念进行打分。

待评估概念：{concept}

打分维度：
{dimensions_text}

返回 JSON 格式：
{json.dumps(dim_schema, ensure_ascii=False, indent=2)}

每个维度只能打 1-5 的整数分（1=非常不认同，5=非常认同）。
必须基于你的性格和痛点来决定分数，不要随机打分。"""

    results = []

    for persona in personas:
        demo = persona.get("demographics", {})
        psych = persona.get("psychographics", {})
        traits = persona.get("behavioral_traits", {})

        user_prompt = f"""你是 {persona.get('name', '未知')}，{demo.get('age', '?')}岁，{demo.get('occupation', '未知')}。
你的性格是 {psych.get('disc_profile', '未知')}。
你的痛点是：{', '.join(traits.get('frustrations', []))}。
你的价值观是：{', '.join(traits.get('values', []))}。

请对上述概念进行打分。输出 JSON。"""

        try:
            scores = engine.chat_json(system_prompt, user_prompt, temperature=0.6, max_tokens=200)
            row = {
                "name": persona.get("name", "未知"),
                "age": demo.get("age", 0),
                "gender": demo.get("gender", "未知"),
                "occupation": demo.get("occupation", "未知"),
                "disc": psych.get("disc_profile", "未知"),
            }
            for dim_name in scoring_dimensions:
                score = scores.get(dim_name, 3)
                if isinstance(score, (int, float)):
                    row[dim_name] = max(1, min(5, int(score)))
                else:
                    row[dim_name] = 3
            results.append(row)
        except Exception as e:
            print(f"打分失败 ({persona.get('name', '?')}): {e}")

        # Report progress
        if progress_callback:
            progress_callback(len(results), len(personas))

    return pd.DataFrame(results)


def analyze_results(df: pd.DataFrame, scoring_dimensions: List[str]) -> Dict:
    """
    分析定量打分结果

    Returns:
        {
            "overall_scores": {维度: 平均分},
            "disc_analysis": {DISC类型: {维度: 平均分}},
            "age_analysis": {年龄段: {维度: 平均分}},
            "top_supporters": [...],
            "top_critics": [...]
        }
    """
    dim_names = scoring_dimensions

    analysis = {
        "overall_scores": {},
        "disc_analysis": {},
        "age_analysis": {},
        "top_supporters": [],
        "top_critics": [],
    }

    # 整体平均分
    for dim in dim_names:
        if dim in df.columns:
            analysis["overall_scores"][dim] = round(df[dim].mean(), 2)

    # 按 DISC 类型分析
    if "DISC" in df.columns:
        for disc_type in ["D", "I", "S", "C"]:
            mask = df["DISC"].str.contains(disc_type, case=False, na=False)
            if mask.any():
                analysis["disc_analysis"][disc_type] = {}
                for dim in dim_names:
                    if dim in df.columns:
                        analysis["disc_analysis"][disc_type][dim] = round(df.loc[mask, dim].mean(), 2)

    # 按年龄段分析
    if "年龄" in df.columns:
        bins = [0, 25, 35, 45, 55, 100]
        labels = ["25以下", "25-35", "35-45", "45-55", "55以上"]
        df["age_group"] = pd.cut(df["年龄"], bins=bins, labels=labels, right=False)
        for group in labels:
            mask = df["age_group"] == group
            if mask.any():
                analysis["age_analysis"][group] = {}
                for dim in dim_names:
                    if dim in df.columns:
                        analysis["age_analysis"][group][dim] = round(df.loc[mask, dim].mean(), 2)
        df.drop("age_group", axis=1, inplace=True, errors="ignore")

    # 最支持和最反对的用户
    if dim_names:
        df["_avg_score"] = df[dim_names].mean(axis=1)
        top = df.nlargest(3, "_avg_score")
        bottom = df.nsmallest(3, "_avg_score")
        analysis["top_supporters"] = top[["姓名", "职业", "DISC", "_avg_score"]].to_dict("records")
        analysis["top_critics"] = bottom[["姓名", "职业", "DISC", "_avg_score"]].to_dict("records")
        df.drop("_avg_score", axis=1, inplace=True, errors="ignore")

    return analysis
