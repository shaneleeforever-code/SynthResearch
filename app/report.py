"""
SynthResearch - 报告生成模块
定性报告汇总 + 定量图表 + 数据导出
"""

import json
import pandas as pd
from typing import List, Dict, Optional
from .i18n import t

REPORT_DIRECT_CHAR_LIMIT = 12000
REPORT_CHUNK_CHAR_LIMIT = 9000


def _chunk_text_blocks(blocks: List[str], limit: int = REPORT_CHUNK_CHAR_LIMIT) -> List[str]:
    chunks = []
    current = ""
    for block in blocks:
        block = str(block or "").strip()
        if not block:
            continue
        if len(block) > limit:
            if current:
                chunks.append(current.strip())
                current = ""
            for start in range(0, len(block), limit):
                chunks.append(block[start:start + limit])
            continue
        if current and len(current) + len(block) + 2 > limit:
            chunks.append(current.strip())
            current = block
        else:
            current = f"{current}\n\n{block}" if current else block
    if current.strip():
        chunks.append(current.strip())
    return chunks


def _records_from_interviews(interview_transcripts) -> List[str]:
    records = []
    if not interview_transcripts:
        return records
    records.append(f"=== {t('1v1 Deep Interview Records')} ===")
    if isinstance(interview_transcripts, list):
        for res in interview_transcripts:
            p_name = res.get("persona", {}).get("姓名", t("未知用户"))
            lines = [f"--- {t('Interview with {n}', n=p_name)} ---"]
            for msg in res.get("history", []):
                role_key = msg.get("role", "user")
                role = t("Researcher") if role_key == "user" else p_name
                content = msg.get("content", "")
                if content:
                    lines.append(f"{role}: {content}")
            records.append("\n".join(lines))
    elif isinstance(interview_transcripts, dict):
        for persona_id, convo in interview_transcripts.items():
            lines = [f"--- {t('Interview with {n}', n=persona_id)} ---"]
            for msg in convo:
                speaker = msg.get("speaker")
                if not speaker:
                    speaker = t("Researcher") if msg.get("role") == "user" or msg.get("type") == "question" else persona_id
                content = msg.get("content", "")
                if content:
                    lines.append(f"{speaker}: {content}")
            records.append("\n".join(lines))
    return records


def _records_from_focus_group(focus_group_history) -> List[str]:
    records = []
    if not focus_group_history:
        return records
    records.append(f"=== {t('Focus Group Discussion Records')} ===")
    current_round = []
    for msg in focus_group_history:
        if msg.get("type") == "round_header":
            if current_round:
                records.append("\n".join(current_round))
            current_round = [msg.get("content", "")]
        else:
            speaker = msg.get("speaker", t("未知发言者"))
            content = msg.get("content", "")
            current_round.append(f"{speaker}: {content}")
    if current_round:
        records.append("\n".join(current_round))
    return records


def _summarize_report_chunk(engine, research_concept: str, chunk: str, idx: int, total: int) -> Dict:
    system_prompt = t("Report Chunk Summary System Prompt")
    user_prompt = f"""Chunk {idx}/{total}
{t('Research Concept Label')}: {research_concept}

{chunk}

{t('Please summarize this chunk for a final research report. Output JSON.')}"""
    result = engine.chat_json(system_prompt, user_prompt, temperature=0.2, max_tokens=1800)
    return result if isinstance(result, dict) else {"summary": str(result)}


def _reduce_report_context(engine, research_concept: str, records: List[str]) -> str:
    combined = "\n\n".join(records)
    if len(combined) <= REPORT_DIRECT_CHAR_LIMIT:
        return combined

    blocks = records
    for _level in range(3):
        chunks = _chunk_text_blocks(blocks, REPORT_CHUNK_CHAR_LIMIT)
        summaries = []
        for idx, chunk in enumerate(chunks, start=1):
            summary = _summarize_report_chunk(engine, research_concept, chunk, idx, len(chunks))
            summaries.append(json.dumps(summary, ensure_ascii=False))
        combined = "\n\n".join(summaries)
        if len(combined) <= REPORT_DIRECT_CHAR_LIMIT:
            return f"=== {t('Summarized Research Evidence')} ===\n\n{combined}"
        blocks = summaries

    return f"=== {t('Summarized Research Evidence')} ===\n\n{combined[:REPORT_DIRECT_CHAR_LIMIT]}"


def generate_qualitative_report(
    engine,
    research_concept: str,
    interview_transcripts: Dict[str, List[Dict]] = None,
    focus_group_history: List[Dict] = None,
) -> Dict:
    """
    生成定性研究报告

    Returns:
        {
            "executive_summary": str,
            "resonance_points": [str],
            "opposition_points": [str],
            "improvement_suggestions": [str],
            "key_quotes": [{"speaker": str, "quote": str}],
            "full_report": str
        }
    """
    records = _records_from_interviews(interview_transcripts)
    records.extend(_records_from_focus_group(focus_group_history))
    all_content = _reduce_report_context(engine, research_concept, records) if records else ""

    if not all_content.strip():
        return {
            "executive_summary": t("No interview data"),
            "resonance_points": [],
            "opposition_points": [],
            "improvement_suggestions": [],
            "key_quotes": [],
            "full_report": t("No data to generate report"),
        }

    system_prompt = t("Report Generation System Prompt")

    user_prompt = f"""{t('Research Concept Label')}: {research_concept}

{t('Below are the full interview/discussion records')}:

{all_content}

{t('Please generate analysis report. Output JSON.')}"""

    try:
        result = engine.chat_json(system_prompt, user_prompt, temperature=0.3, max_tokens=4000)
        
        # 强制确保 result 是字典
        if not isinstance(result, dict):
            result = {"executive_summary": str(result)}

        # 辅助函数：清洗列表，移除占位符
        def clean_list(lst):
            if not lst or not isinstance(lst, list): return []
            placeholders = ["暂无", "none", "n/a", "无", "nothing", "暂无数据", "未能生成"]
            return [str(item) for item in lst if str(item).strip().lower() not in placeholders]

        # 确保关键字段存在且不为空，针对专业版报告增加字段
        keys_to_check = [
            "executive_summary", "resonance_points", "opposition_points", 
            "improvement_suggestions", "key_insights", "product_evaluation", 
            "strategic_recommendations", "key_quotes"
        ]
        for key in keys_to_check:
            val = result.get(key)
            if val is None or (isinstance(val, (list, str, dict)) and not val):
                if key in ["resonance_points", "opposition_points", "improvement_suggestions", "key_quotes", "strategic_recommendations"]:
                    result[key] = []
                elif key == "key_insights":
                    result[key] = [{"title": t("暂无显著发现"), "description": ""}]
                elif key == "product_evaluation":
                    result[key] = {"strengths": [], "weaknesses": [], "opportunities": []}
                else:
                    result[key] = t("未能生成该部分分析")
            
            # 清洗列表
            if key in ["resonance_points", "opposition_points", "improvement_suggestions"]:
                result[key] = clean_list(result[key])
            elif key == "product_evaluation":
                pe = result[key]
                pe["strengths"] = clean_list(pe.get("strengths", []))
                pe["weaknesses"] = clean_list(pe.get("weaknesses", []))
                pe["opportunities"] = clean_list(pe.get("opportunities", []))

        # 生成完整的可读报告文本 (Markdown)
        full_report = f"# SynthResearch {t('Qualitative Research Report')}\n\n"
        full_report += f"## {t('Research Concept Label')}：{research_concept}\n\n---\n\n"
        
        # 1. Executive Summary
        full_report += f"## {t('Executive Summary')}\n{result.get('executive_summary', '')}\n\n"
        
        # 2. Resonance, Objections, Improvements
        if result.get("resonance_points"):
            full_report += f"### ✅ {t('Resonance Points')}\n"
            for p in result["resonance_points"]: full_report += f"- {p}\n"
            full_report += "\n"
        
        if result.get("opposition_points"):
            full_report += f"### ❌ {t('Objections')}\n"
            for p in result["opposition_points"]: full_report += f"- {p}\n"
            full_report += "\n"
            
        if result.get("improvement_suggestions"):
            full_report += f"### 💡 {t('Improvements')}\n"
            for p in result["improvement_suggestions"]: full_report += f"- {p}\n"
            full_report += "\n"
        
        full_report += "---\n"

        # 3. Strategic Insights
        full_report += f"## {t('Strategic Insights')}\n"
        insights = result.get('key_insights', [])
        for insight in insights:
            title = insight.get('title', '')
            desc = insight.get('description', insight.get('content', ''))
            full_report += f"### {title}\n{desc}\n\n"
        
        # 4. Product Evaluation
        pe = result.get('product_evaluation', {})
        full_report += f"---\n## {t('Product Evaluation')}\n"
        full_report += f"### {t('Strengths')}\n"
        for s in pe.get('strengths', []): full_report += f"- {s}\n"
        full_report += f"\n### {t('Weaknesses')}\n"
        for w in pe.get('weaknesses', []): full_report += f"- {w}\n"
        full_report += f"\n### {t('Opportunities')}\n"
        for o in pe.get('opportunities', []): full_report += f"- {o}\n"
        
        # 5. Recommendations
        full_report += f"\n---\n## {t('Recommended Roadmap')}\n"
        recs = result.get('strategic_recommendations', [])
        for r in recs:
            prio = r.get('priority', 'Medium')
            sug = r.get('suggestion', r.get('action', ''))
            impact = r.get('impact', r.get('reason', ''))
            full_report += f"- **[{prio}]** {sug}  \n  *{t('Impact')}: {impact}*\n"
        
        # 6. Key Quotes
        full_report += f"\n---\n## {t('Key Quotes')}\n"
        quotes = result.get('key_quotes', [])
        for quote in quotes:
            if isinstance(quote, dict):
                full_report += f"> \"{quote.get('quote', '')}\" —— {quote.get('speaker', t('Unknown'))}\n\n"
            else:
                full_report += f"> \"{str(quote)}\" —— {t('Unknown')}\n\n"

        result["full_report"] = full_report
        return result

    except Exception as e:
        error_msg = f"{t('Report generation failed')}: {str(e)}"
        return {
            "executive_summary": error_msg,
            "resonance_points": [t("未能生成有效分析")],
            "opposition_points": [t("未能生成有效分析")],
            "improvement_suggestions": [t("未能生成有效分析")],
            "key_quotes": [],
            "full_report": error_msg,
        }


def generate_quantitative_report(
    engine,
    research_concept: str,
    df: pd.DataFrame,
    analysis: Dict
) -> str:
    """
    生成定量研究的文本洞察报告
    """
    data_summary = f"{t('Total Respondents')}: {len(df)}\n"
    
    data_summary += f"{t('Overall Scores by Dimension')}:\n"
    for dim, score in analysis.get("overall_scores", {}).items():
        data_summary += f"- {dim}: {score}\n"
        
    data_summary += f"\n{t('Top Supporters')} (Top 3):\n"
    for u in analysis.get("top_supporters", []):
        data_summary += f"- {t('Name')}: {u['姓名']}, {t('Occupation')}: {u['职业']}, DISC: {u['DISC']}, {t('Average Score')}: {u.get('_avg_score', 0):.2f}\n"
    data_summary += f"\n{t('Top Critics')} (Bottom 3):\n"
    for u in analysis.get("top_critics", []):
        data_summary += f"- {t('Name')}: {u['姓名']}, {t('Occupation')}: {u['职业']}, DISC: {u['DISC']}, {t('Average Score')}: {u.get('_avg_score', 0):.2f}\n"

    system_prompt = t("Quantitative Insight System Prompt")
    user_prompt = f"""{t('Research Concept Label')}: {research_concept}

{t('Below is the summary information of quantitative scoring data')}:

{data_summary}

{t('Please generate quantitative research insight report.')}"""

    try:
        res = engine.chat(system_prompt, user_prompt, temperature=0.6, max_tokens=2500)
        if not res or not res.strip():
            return f"{t('Report generation failed')}: LLM returned empty response"
        return res
    except Exception as e:
        return f"{t('Report generation failed')}: {str(e)}"


def export_transcripts_csv(
    interview_transcripts: Dict[str, List[Dict]],
    focus_group_history: List[Dict] = None,
) -> pd.DataFrame:
    """导出访谈记录为 DataFrame（可转 CSV）"""
    rows = []

    if interview_transcripts:
        if isinstance(interview_transcripts, dict):
            for persona_id, convo in interview_transcripts.items():
                for msg in convo:
                    rows.append({
                        t("Type"): t("1v1 Deep Interview Records"),
                        t("Name"): t("Researcher") if msg.get("type") == "question" else persona_id,
                        t("Role"): msg.get("type", "unknown"),
                        t("Content"): msg.get("content", ""),
                    })
        elif isinstance(interview_transcripts, list):
             for res in interview_transcripts:
                p_name = res.get("persona", {}).get("姓名", t("未知用户"))
                for msg in res.get("history", []):
                    rows.append({
                        t("Type"): t("1v1 Deep Interview Records"),
                        t("Name"): t("Researcher") if msg.get("role") == "user" else p_name,
                        t("Role"): msg.get("role", "unknown"),
                        t("Content"): msg.get("content", ""),
                    })

    if focus_group_history:
        for msg in focus_group_history:
            rows.append({
                t("Type"): t("Focus Group Discussion Records"),
                t("Name"): msg.get("speaker", t("未知")),
                t("Role"): "moderator" if msg.get("speaker") == t("Researcher") else "agent",
                t("Content"): msg.get("content", ""),
            })

    return pd.DataFrame(rows)


def export_personas_json(personas: List[Dict]) -> str:
    """导出 Persona 为 JSON 字符串"""
    # 移除内部标记字段
    clean = []
    for p in personas:
        cleaned = {k: v for k, v in p.items() if not k.startswith("_")}
        clean.append(cleaned)
    return json.dumps({"personas": clean}, ensure_ascii=False, indent=2)
