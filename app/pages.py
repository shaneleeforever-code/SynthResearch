"""
SynthResearch - 页面模块
每个函数对应 PRD 中的一个页面
"""
import streamlit as st
import json
import hashlib
import uuid
import pandas as pd
import re
import time
import html
import plotly.express as px
from app.styles import DISC_COLORS
from app.components import (
    render_empty_state, render_project_card, render_path_card,
    render_persona_card, render_chat_bubble, render_stat_card,
    render_focus_mode_header, render_workflow_dots,
    render_hero_section, render_page_header, get_chat_bubble_html,
    render_simplified_persona_card, render_scoring_persona_card, clean_html
)
from app.persona import generate_personas, generate_ai_questions
from app.interview import InterviewEngine
from app.focus_group import FocusGroupEngine
from app.quantitative import generate_quant_personas, run_quantitative_scoring, analyze_results, build_quant_scoring_prompts
from app.report import generate_qualitative_report, export_transcripts_csv, export_personas_json, generate_quantitative_report
from app.project_store import get_project_landing_page, save_projects
from app.input_limits import (
    SAMPLE_MIN, SAMPLE_MAX, SAMPLE_DEFAULT,
    TARGET_AUDIENCE_MAX_CHARS, CONCEPT_NAME_MAX_CHARS, CONCEPT_DESC_MAX_CHARS,
    CHALLENGE_MAX_ITEMS, CHALLENGE_MAX_CHARS,
    QUESTION_MAX_ITEMS, QUESTION_MAX_CHARS,
    append_limited_unique, clamp_int, normalize_limited_list, trim_text, weighted_text_units,
)
from datetime import datetime
from app.i18n import t


def goto(page: int):
    st.session_state.current_page = page
    st.rerun()


def _normalize_project_name(name: str) -> str:
    return (name or "").strip().casefold()


def _ensure_project_ids():
    projects = st.session_state.get("projects", [])
    changed = False
    for p in projects:
        if not p.get("project_id"):
            p["project_id"] = uuid.uuid4().hex
            changed = True
    if changed:
        st.session_state.projects = projects
        _persist_projects()


def _persist_projects():
    save_projects(st.session_state.get("projects", []))


def _project_name_exists(name: str, exclude_project_id: str = "") -> bool:
    target = _normalize_project_name(name)
    if not target:
        return False
    _ensure_project_ids()
    for p in st.session_state.get("projects", []):
        if exclude_project_id and p.get("project_id") == exclude_project_id:
            continue
        if _normalize_project_name(p.get("name", "")) == target:
            return True
    return False


def save_current_project():
    if not st.session_state.get("project_name"):
        return
    _sync_designer_inputs()
    _ensure_project_ids()
    project_id = st.session_state.get("current_project_id") or uuid.uuid4().hex
    st.session_state.current_project_id = project_id
    proj_data = {
        "project_id": project_id,
        "name": st.session_state.project_name,
        "desc": st.session_state.get("project_desc", ""),
        "mode": st.session_state.get("research_mode", "qualitative"),
        "created_at": st.session_state.get("project_created_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
        "target_audience": st.session_state.get("target_audience", ""),
        "challenges": st.session_state.get("challenges", []),
        "sample_size": st.session_state.get("sample_size", SAMPLE_DEFAULT),
        "concepts": st.session_state.get("concepts", [{"name": "", "description": ""}]),
        "questions": st.session_state.get("questions", []),
        "personas": st.session_state.get("personas", []),
        "interview_mode": st.session_state.get("interview_mode", "1v1"),
        "interview_results": st.session_state.get("interview_results", {}),
        "focus_group_history": st.session_state.get("focus_group_history", []),
        "quant_results": st.session_state.get("quant_results", None),
        "quant_phase": st.session_state.get("quant_phase", 0),
        "quant_personas": st.session_state.get("quant_personas", []),
        "report": st.session_state.get("report", None),
        "scoring_dims": st.session_state.get("scoring_dims", []),
        "quant_analysis": st.session_state.get("quant_analysis", {}),
        "quant_report_text": st.session_state.get("quant_report_text", ""),
        "quant_report_key": st.session_state.get("quant_report_key", ""),
    }
    
    projects = st.session_state.get("projects", [])
    found = False
    for i, p in enumerate(projects):
        if p.get("project_id") == project_id:
            projects[i] = proj_data
            found = True
            break
    if not found:
        projects.append(proj_data)
    st.session_state.projects = projects
    _persist_projects()

def clear_current_project():
    keys_to_clear = [
        "project_name", "project_desc", "target_audience", "challenges",
        "current_project_id",
        "sample_size", "concepts", "questions", "personas", "interview_mode",
        "interview_results", "focus_group_history", "quant_results", "quant_phase",
        "quant_personas", "report", "scoring_dims", "quant_analysis", "_ai_suggestions",
        "quant_report_text", "quant_report_key",
        "_qual_generating", "_quant_generating", "project_created_at", "research_mode"
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]

def load_project(proj_data):
    _ensure_project_ids()
    clear_current_project()
    if not proj_data.get("project_id"):
        proj_data["project_id"] = uuid.uuid4().hex
    for k, v in proj_data.items():
        st.session_state[k] = v
    st.session_state.current_project_id = proj_data["project_id"]
    # Ensure research_mode is set properly
    st.session_state.research_mode = proj_data.get("mode", "qualitative")


def open_project(proj_data, page: int = None):
    load_project(proj_data)
    st.session_state.current_page = page if page is not None else get_project_landing_page(proj_data)
    st.rerun()


def _project_link(project_id: str, page: int) -> str:
    return f"?open_project={project_id}&page={page}"


def _render_project_links(project_id: str, proj: dict):
    links = [
        ("查看用户画像", 4),
        ("查看访谈/打分记录", 5),
        ("查看报告", 6),
    ]
    html_links = []
    for label, page in links:
        html_links.append(
            f'<a href="{_project_link(project_id, page)}" target="_self" '
            f'style="font-size: 0.9rem; color: var(--primary); text-decoration: none; margin-right: 16px;">'
            f'{html.escape(t(label))}</a>'
        )
    st.markdown("".join(html_links), unsafe_allow_html=True)


def _quant_report_key(concept_text: str, df: pd.DataFrame, analysis: dict) -> str:
    payload = {
        "concept": concept_text,
        "columns": list(df.columns),
        "rows": df.to_dict(orient="records"),
        "overall_scores": analysis.get("overall_scores", {}),
        "scoring_dims": st.session_state.get("scoring_dims", []),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _valid_comparison_concepts() -> list:
    concepts = st.session_state.get("concepts", [])
    comparisons = []
    for concept in concepts[1:]:
        name = concept.get("name", "").strip()
        desc = concept.get("description", "").strip()
        if name or desc:
            comparisons.append({"name": name, "description": desc})
    return comparisons


def _contains_comparison_item(items: list, main_name: str, comparison_concepts: list) -> bool:
    main_name = (main_name or "").strip().lower()
    comparison_names = [c.get("name", "").strip().lower() for c in comparison_concepts if c.get("name", "").strip()]
    if not main_name or not comparison_names:
        return False
    for item in items:
        text = str(item).lower()
        if main_name in text and any(name in text for name in comparison_names):
            return True
    return False


def _comparison_names_text(comparison_concepts: list) -> str:
    names = [c.get("name", "").strip() for c in comparison_concepts if c.get("name", "").strip()]
    return "、".join(names)


def _limit_caption(value: str, max_units: int):
    used = weighted_text_units(value)
    used_text = str(int(used)) if used == int(used) else f"{used:.1f}"
    caption = t("等效字数：{used}/{limit}", used=used_text, limit=max_units)
    over_limit = used > max_units
    st.caption(f":red[{caption}]" if over_limit else caption)
    return over_limit


def _ensure_text_state(key: str, value: str):
    if key not in st.session_state:
        st.session_state[key] = value or ""


def _apply_pending_text_state(key: str, pending_key: str):
    if pending_key in st.session_state:
        st.session_state[key] = st.session_state.pop(pending_key)


def _is_over_limit(value: str, max_units: int) -> bool:
    return weighted_text_units(value or "") > max_units


def _designer_persisted_inputs_over_limit() -> bool:
    checks = [
        (st.session_state.get("target_audience_input", st.session_state.get("target_audience", "")), TARGET_AUDIENCE_MAX_CHARS),
    ]

    concepts = st.session_state.get("concepts", [])
    if concepts:
        checks.extend([
            (st.session_state.get("main_concept_name_input", concepts[0].get("name", "")), CONCEPT_NAME_MAX_CHARS),
            (st.session_state.get("main_concept_desc_input", concepts[0].get("description", "")), CONCEPT_DESC_MAX_CHARS),
        ])
        for i in range(1, len(concepts)):
            checks.extend([
                (st.session_state.get(f"cn_{i}", concepts[i].get("name", "")), CONCEPT_NAME_MAX_CHARS),
                (st.session_state.get(f"cd_{i}", concepts[i].get("description", "")), CONCEPT_DESC_MAX_CHARS),
            ])

    ch_version = st.session_state.get("ch_version")
    for i, value in enumerate(st.session_state.get("challenges", [])):
        key = f"ch_v{ch_version}_{i}" if ch_version is not None else ""
        checks.append((st.session_state.get(key, value), CHALLENGE_MAX_CHARS))

    q_version = st.session_state.get("q_version")
    for i, value in enumerate(st.session_state.get("questions", [])):
        key = f"qe_v{q_version}_{i}" if q_version is not None else ""
        checks.append((st.session_state.get(key, value), QUESTION_MAX_CHARS))

    return any(_is_over_limit(value, max_units) for value, max_units in checks)


def _sync_designer_inputs():
    if "target_audience_input" in st.session_state:
        st.session_state.target_audience = trim_text(st.session_state.target_audience_input, TARGET_AUDIENCE_MAX_CHARS)

    if st.session_state.get("concepts"):
        if "main_concept_name_input" in st.session_state:
            st.session_state.concepts[0]["name"] = trim_text(st.session_state.main_concept_name_input, CONCEPT_NAME_MAX_CHARS)
        if "main_concept_desc_input" in st.session_state:
            st.session_state.concepts[0]["description"] = trim_text(st.session_state.main_concept_desc_input, CONCEPT_DESC_MAX_CHARS)

        for i in range(1, len(st.session_state.concepts)):
            name_key = f"cn_{i}"
            desc_key = f"cd_{i}"
            if name_key in st.session_state:
                st.session_state.concepts[i]["name"] = trim_text(st.session_state[name_key], CONCEPT_NAME_MAX_CHARS)
            if desc_key in st.session_state:
                st.session_state.concepts[i]["description"] = trim_text(st.session_state[desc_key], CONCEPT_DESC_MAX_CHARS)

    if "ch_version" in st.session_state:
        for i in range(len(st.session_state.get("challenges", []))):
            key = f"ch_v{st.session_state.ch_version}_{i}"
            if key in st.session_state:
                st.session_state.challenges[i] = trim_text(st.session_state[key], CHALLENGE_MAX_CHARS)
        st.session_state.challenges = normalize_limited_list(st.session_state.challenges, CHALLENGE_MAX_ITEMS, CHALLENGE_MAX_CHARS)

    if "q_version" in st.session_state:
        for i in range(len(st.session_state.get("questions", []))):
            key = f"qe_v{st.session_state.q_version}_{i}"
            if key in st.session_state:
                st.session_state.questions[i] = trim_text(st.session_state[key], QUESTION_MAX_CHARS)
        st.session_state.questions = normalize_limited_list(st.session_state.questions, QUESTION_MAX_ITEMS, QUESTION_MAX_CHARS)


# ============================================================
# Page 0: Dashboard
# ============================================================
def page_dashboard():
    _ensure_project_ids()
    render_hero_section(
        title=t("探索未来的研究洞察"),
        subtitle=t("利用 AI 驱动的合成画像，深入挖掘用户痛点，加速产品创新验证。"),
        label=t("合成研究工作台")
    )

    c_btn, c_search = st.columns([0.25, 0.75], vertical_alignment="center")
    with c_btn:
        if st.button(t("＋ 创建新研究"), key="new_project", use_container_width=True, type="primary"):
            clear_current_project()
            goto(1)
    with c_search:
        search_query = st.text_input(t("搜索"), key="search_proj", label_visibility="collapsed", placeholder=t("🔍 输入项目名称搜索..."))

    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

    projects = st.session_state.get("projects", [])
    
    if search_query:
        display_projects = [p for p in projects if search_query.lower() in p["name"].lower() or search_query.lower() in p.get("desc", "").lower()]
    else:
        display_projects = projects

    if not projects:
        render_empty_state("📋", t("还没有研究项目"), t("点击上方按钮创建你的第一个研究项目"))
    elif not display_projects:
        render_empty_state("🔍", t("没有找到相关项目"), t("换个搜索词试试"))
    else:
        cols = st.columns(2)
        for i, proj in enumerate(display_projects):
            project_id = proj.get("project_id", str(i))
            with cols[i % 2]:
                render_project_card(
                    proj["name"], proj.get("desc", ""),
                    proj.get("mode", "qualitative"),
                    proj.get("created_at", ""),
                )
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                c_open, c_del = st.columns([0.7, 0.3])
                with c_open:
                    if st.button(t("打开 →"), key=f"open_{project_id}", use_container_width=True):
                        open_project(proj)
                _render_project_links(project_id, proj)
                with c_del:
                    with st.popover(t("🗑️ 删除"), use_container_width=True):
                        st.markdown(t("确定删除该项目？"))
                        if st.button(t("确认删除"), key=f"del_confirm_{project_id}", type="primary", use_container_width=True):
                            st.session_state.projects = [p for p in st.session_state.get("projects", []) if p.get("project_id") != project_id]
                            _persist_projects()
                            st.rerun()
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


# ============================================================
# Page 1: Project Init
# ============================================================
def page_init():
    render_page_header(t("创建新研究"), t("开始你的研究之旅，定义项目的核心目标"))

    with st.container():
        name = st.text_input(t("项目名称"), value=st.session_state.project_name,
                             placeholder=t("例如：智能家居产品市场调研"))
        desc = st.text_input(t("项目描述"), value=st.session_state.get("project_desc", ""),
                             placeholder=t("例如：针对一线城市年轻用户的需求验证"))
        
        # Save to session state immediately so navigation doesn't reset it
        st.session_state.project_name = name
        st.session_state.project_desc = desc

    st.markdown("")
    c1, c2 = st.columns([0.5, 0.5])
    with c1:
        if st.button(t("← 返回"), key="back_1"):
            goto(0)
    with c2:
        if st.button(t("下一步 →"), key="next_1", use_container_width=True):
            if name.strip():
                if _project_name_exists(name, st.session_state.get("current_project_id", "")):
                    st.error(t("项目名称已存在，请使用不同的名称"))
                    st.stop()
                if not st.session_state.get("current_project_id"):
                    st.session_state.current_project_id = uuid.uuid4().hex
                goto(2)
            else:
                st.error(t("请输入项目名称"))


# ============================================================
# Page 2: Path Selection
# ============================================================
def page_path_select():
    render_page_header(st.session_state.project_name, t("选择最适合你研究目标的路径"))

    c1, c2 = st.columns(2)
    with c1:
        render_path_card("🔍", t("定性痛点挖掘"), t("1v1 深度访谈或焦点小组讨论\n适用于早期需求探索与痛点验证"))
        if st.button(t("选择定性研究"), key="sel_qual", use_container_width=True):
            st.session_state.research_mode = "qualitative"
            goto(3)
    with c2:
        render_path_card("📊", t("定量概念验证"), t("大规模打分与概念评分测试\n适用于产品验证与统计分析"))
        if st.button(t("选择定量验证"), key="sel_quant", use_container_width=True):
            st.session_state.research_mode = "quantitative"
            goto(3)

    st.markdown("")
    if st.button(t("← 返回"), key="back_2"):
        goto(1)


# ============================================================
# Page 3: Designer Workspace (Tabs)
# ============================================================
def page_designer():
    mode = st.session_state.research_mode
    render_workflow_dots(6, 1)

    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] {
            display: flex;
            justify-content: center;
            gap: 48px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 4px;
            margin-bottom: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 72px;
            white-space: nowrap;
            background-color: transparent !important;
            border: none !important;
            transition: all 0.3s ease;
        }
        .stTabs [data-baseweb="tab"] p {
            font-size: 1.45rem !important;
            font-weight: 600 !important;
            font-family: var(--font-display) !important;
            letter-spacing: -0.015em;
            color: var(--muted-foreground);
        }
        .stTabs [aria-selected="true"] p {
            color: var(--accent) !important;
            transform: scale(1.05);
        }
        .stTabs [data-baseweb="tab"]:hover p {
            color: var(--foreground);
        }
        </style>
    """, unsafe_allow_html=True)

    if mode == "qualitative":
        tabs = st.tabs([t("Audience"), t("Sample Size"), t("Concept"), t("Questions")])
    else:
        tabs = st.tabs([t("Audience"), t("Sample Size"), t("Concept"), t("Dimensions")])

    # Tab 1: Audience
    with tabs[0]:
        _tab_audience()

    # Tab 2: Sample Size
    with tabs[1]:
        _tab_sample()

    # Tab 3: Concepts
    with tabs[2]:
        _tab_concepts()

    # Tab 4: Questions / Scoring
    with tabs[3]:
        if mode == "qualitative":
            _tab_questions()
        else:
            _tab_scoring()

    # Bottom nav
    st.divider()
    c1, c2 = st.columns([0.5, 0.5])
    with c1:
        if st.button(t("← 返回"), key="back_3"):
            goto(2)
    with c2:
        label = t("生成画像并继续 →")
        has_over_limit_input = _designer_persisted_inputs_over_limit()
        if has_over_limit_input:
            st.warning(t("有输入内容超出上限，请缩短后继续"))
        if st.button(label, key="next_3", use_container_width=True, disabled=has_over_limit_input):
            _sync_designer_inputs()
            if not st.session_state.target_audience:
                st.error(t("请填写研究对象描述"))
            elif not st.session_state.concepts or not st.session_state.concepts[0].get("name", "").strip() or not st.session_state.concepts[0].get("description", "").strip():
                st.error(t("请填写主概念名称和概念详情"))
            elif mode == "qualitative" and not st.session_state.questions:
                st.error(t("请至少添加一个问题"))
            elif mode == "quantitative" and not st.session_state.scoring_dims:
                st.error(t("请至少添加一个打分维度"))
            else:
                goto(4)


def _tab_audience():
    engine = st.session_state.engine
    st.session_state.challenges = normalize_limited_list(
        st.session_state.get("challenges", []),
        CHALLENGE_MAX_ITEMS,
        CHALLENGE_MAX_CHARS,
    )
    st.markdown(f"#### {t('人群描述')}")
    _apply_pending_text_state("target_audience_input", "_pending_target_audience_input")
    _ensure_text_state("target_audience_input", st.session_state.get("target_audience", ""))
    target_audience_draft = st.text_area(
        t("人群描述"),
        placeholder=t("例如：25-30岁，一二线城市独居女性，注重悦己消费"),
        height=80, key="target_audience_input", label_visibility="collapsed")
    target_over_limit = _limit_caption(target_audience_draft, TARGET_AUDIENCE_MAX_CHARS)

    # AI 描述优化按钮（始终显示）
    if st.button(t("✨ AI 描述优化"), key="ai_enhance", disabled=target_over_limit):
        if not engine:
            st.error(t("请先在侧边栏配置 API Key"))
        elif not target_audience_draft.strip():
            st.error(t("请先输入人群描述"))
        else:
            with st.spinner(t("AI 正在优化描述...")):
                enhanced = engine.chat(
                    t("Audience Optimization Prompt"),
                    target_audience_draft, temperature=0.4, max_tokens=500)
                st.session_state.target_audience = trim_text(enhanced, TARGET_AUDIENCE_MAX_CHARS)
                st.session_state["_pending_target_audience_input"] = st.session_state.target_audience
                st.rerun()

    st.markdown("---")
    st.markdown(f"#### {t('痛点 / 目标 / 挑战')}")

    # AI 推测痛点按钮
    if st.button(t("✨ AI 推测痛点与挑战"), key="ai_challenges", disabled=target_over_limit or len(st.session_state.challenges) >= CHALLENGE_MAX_ITEMS):
        if not engine:
            st.error(t("请先在侧边栏配置 API Key"))
        elif not target_audience_draft.strip():
            st.error(t("请先输入人群描述"))
        else:
            with st.spinner(t("AI 正在分析目标人群的痛点与挑战...")):
                result = engine.chat_json(
                    t("Challenges Prediction Prompt"),
                    f"{t('目标人群')}：{trim_text(target_audience_draft, TARGET_AUDIENCE_MAX_CHARS)}",
                    temperature=0.5, max_tokens=800)
                if isinstance(result, dict):
                    ai_items = result.get("items")
                    if not ai_items:
                        # Support for specific keys from the new prompt
                        for key in ["pains", "goals", "challenges"]:
                            val = result.get(key)
                            if isinstance(val, list):
                                if ai_items is None: ai_items = []
                                ai_items.extend(val)
                    if not ai_items:
                        for val in result.values():
                            if isinstance(val, list):
                                ai_items = val
                                break
                elif isinstance(result, list):
                    ai_items = result
                else:
                    ai_items = []
                
                for item in ai_items:
                    val_str = ""
                    if isinstance(item, str):
                        val_str = item
                    elif isinstance(item, dict):
                        val_str = " - ".join(str(v) for v in item.values() if isinstance(v, str) and v)
                    else:
                        val_str = str(item)
                    append_limited_unique(
                        st.session_state.challenges,
                        val_str,
                        CHALLENGE_MAX_ITEMS,
                        CHALLENGE_MAX_CHARS,
                    )
                st.rerun()

    # 手动添加
    ch = st.text_input(
        t("手动添加痛点/目标"),
        placeholder=t("例如：硬件供应链响应慢"),
        key="ch_input",
        disabled=len(st.session_state.challenges) >= CHALLENGE_MAX_ITEMS,
    )
    ch_over_limit = _limit_caption(ch, CHALLENGE_MAX_CHARS)
    if st.button(t("➕ 添加"), key="add_ch", disabled=ch_over_limit or not ch or len(st.session_state.challenges) >= CHALLENGE_MAX_ITEMS):
        if append_limited_unique(st.session_state.challenges, ch, CHALLENGE_MAX_ITEMS, CHALLENGE_MAX_CHARS):
            st.rerun()

    # 痛点列表（可编辑）
    if "ch_version" not in st.session_state:
        st.session_state.ch_version = 0

    if st.session_state.challenges:
        def _rm_challenge(idx):
            st.session_state.challenges.pop(idx)
            st.session_state.ch_version += 1

        for i, c in enumerate(st.session_state.challenges):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                # 使用版本号作为 key 的一部分，确保列表变动后强制刷新所有组件状态
                edited = st.text_input(
                    f"{t('痛点')} {i+1}",
                    value=c,
                    key=f"ch_v{st.session_state.ch_version}_{i}",
                    label_visibility="collapsed",
                )
                _limit_caption(edited, CHALLENGE_MAX_CHARS)
            with col2:
                # 统一使用 on_click 避免索引偏移导致的删除错误
                st.button("🗑️", key=f"rm_ch_v{st.session_state.ch_version}_{i}", on_click=_rm_challenge, args=(i,))


def _tab_sample():
    mode = st.session_state.research_mode
    st.session_state.sample_size = clamp_int(
        st.session_state.get("sample_size", SAMPLE_DEFAULT),
        SAMPLE_MIN,
        SAMPLE_MAX,
    )
    if mode == "qualitative":
        st.markdown(f"#### {t('虚拟受访者数量')}")
        st.session_state.sample_size = st.slider(
            t("虚拟受访者数量"), SAMPLE_MIN, SAMPLE_MAX, st.session_state.sample_size,
            help=t("建议 10-100 人，最少 3 人"), label_visibility="collapsed")
        
        st.markdown(f"#### {t('访谈模式')}")
        st.session_state.interview_mode = st.radio(
            t("访谈模式"), ["1v1", "focus_group"],
            format_func=lambda x: t("🎙️ 1v1 深度访谈") if x == "1v1" else t("💬 焦点小组"),
            key="iv_mode", label_visibility="collapsed")
    else:
        st.markdown(f"#### {t('虚拟样本量')}")
        st.session_state.sample_size = st.slider(
            t("虚拟样本量"), SAMPLE_MIN, SAMPLE_MAX, st.session_state.sample_size,
            help=t("建议 10-100 人，最少 3 人"), label_visibility="collapsed")


def _tab_concepts():
    if not st.session_state.concepts:
        st.session_state.concepts = [{"name": "", "description": ""}]

    st.markdown(f"#### {t('主概念')}")
    _ensure_text_state("main_concept_name_input", st.session_state.concepts[0].get("name", ""))
    main_name = st.text_input(
        t("概念名称"),
        placeholder=t("例如：AI 智能营养师 App"),
        key="main_concept_name_input")
    _limit_caption(main_name, CONCEPT_NAME_MAX_CHARS)
    _ensure_text_state("main_concept_desc_input", st.session_state.concepts[0].get("description", ""))
    main_desc = st.text_area(
        t("概念详情"),
        placeholder=t("描述产品概念的核心功能和价值主张..."), height=100,
        key="main_concept_desc_input")
    _limit_caption(main_desc, CONCEPT_DESC_MAX_CHARS)

    with st.expander(t("对照概念 (可选)")):
        for i in range(len(st.session_state.concepts)-1):
            with st.container():
                _ensure_text_state(f"cn_{i+1}", st.session_state.concepts[i+1].get("name", ""))
                comp_name = st.text_input(
                    t("对照概念 {n} 名称", n=i+1),
                    key=f"cn_{i+1}",
                )
                _limit_caption(comp_name, CONCEPT_NAME_MAX_CHARS)
                _ensure_text_state(f"cd_{i+1}", st.session_state.concepts[i+1].get("description", ""))
                comp_desc = st.text_area(
                    t("描述"),
                    key=f"cd_{i+1}",
                    height=60,
                )
                _limit_caption(comp_desc, CONCEPT_DESC_MAX_CHARS)
                if st.button(t("删除"), key=f"del_concept_{i+1}"):
                    st.session_state.concepts.pop(i+1)
                    st.rerun()
        if len(st.session_state.concepts) < 3:
            if st.button(t("添加对照概念")):
                st.session_state.concepts.append({"name": "", "description": ""})
                st.rerun()


def _tab_questions():
    engine = st.session_state.engine

    # AI 生成建议问题按钮（始终显示）
    remaining_slots = QUESTION_MAX_ITEMS - len(st.session_state.questions)
    setup_over_limit = _designer_persisted_inputs_over_limit()
    if st.button(t("✨ AI生成建议问题"), key="ai_q", disabled=setup_over_limit or remaining_slots <= 0):
        if not engine:
            st.error(t("请先在侧边栏配置 API Key"))
        else:
            _sync_designer_inputs()
            with st.spinner(t("AI 正在生成问题...")):
                main_concept = st.session_state.concepts[0]
                main_name = main_concept.get("name", "").strip()
                comparison_concepts = _valid_comparison_concepts()
                research_concept = f"{main_concept.get('name', '')}: {main_concept.get('description', '')}"
                ai_questions = generate_ai_questions(
                    engine, st.session_state.target_audience,
                    research_concept,
                    comparison_concepts=comparison_concepts,
                    count=min(5, remaining_slots))
                if not isinstance(ai_questions, list):
                    if isinstance(ai_questions, str):
                        ai_questions = [ai_questions]
                    else:
                        ai_questions = []
                
                extracted_items = []
                for q in ai_questions:
                    if isinstance(q, str):
                        extracted_items.append(trim_text(q, QUESTION_MAX_CHARS))
                    elif isinstance(q, dict):
                        extracted_items.append(trim_text(" - ".join(str(v) for v in q.values() if isinstance(v, str) and v), QUESTION_MAX_CHARS))
                    else:
                        extracted_items.append(trim_text(str(q), QUESTION_MAX_CHARS))

                if comparison_concepts and not _contains_comparison_item(extracted_items, main_name, comparison_concepts):
                    extracted_items.insert(0, t(
                        "相比 {comparisons}，你更倾向选择 {main} 还是对照概念？是什么取舍让你产生这个倾向？",
                        main=main_name,
                        comparisons=_comparison_names_text(comparison_concepts)
                    ))

                st.session_state["_ai_suggestions"] = [
                    q for q in normalize_limited_list(extracted_items, remaining_slots, QUESTION_MAX_CHARS)
                    if q and q not in st.session_state.questions
                ]
                st.rerun()

    # Show AI suggestions if any
    suggestions = st.session_state.get("_ai_suggestions", [])
    if suggestions:
        st.markdown(f"##### {t('💡 AI 建议问题')}")
        for idx, s in enumerate(suggestions):
            c1, c2 = st.columns([0.88, 0.12])
            with c1:
                st.markdown(f'<div class="ai-suggestion-text">{s}</div>', unsafe_allow_html=True)
            with c2:
                if st.button("＋", key=f"add_sug_{idx}"):
                    if append_limited_unique(st.session_state.questions, s, QUESTION_MAX_ITEMS, QUESTION_MAX_CHARS):
                        st.session_state["_ai_suggestions"].remove(s)
                        st.rerun()
        st.markdown("---")

    # Manual add
    nq = st.text_input(
        t("手动添加问题"),
        placeholder=t("输入问题后点击添加"),
        key="nq_input",
        disabled=len(st.session_state.questions) >= QUESTION_MAX_ITEMS,
    )
    nq_over_limit = _limit_caption(nq, QUESTION_MAX_CHARS)
    if st.button(t("➕ 添加问题"), key="add_q", disabled=nq_over_limit or not nq or len(st.session_state.questions) >= QUESTION_MAX_ITEMS):
        if append_limited_unique(st.session_state.questions, nq, QUESTION_MAX_ITEMS, QUESTION_MAX_CHARS):
            st.rerun()

    # Question list
    if "q_version" not in st.session_state:
        st.session_state.q_version = 0

    if st.session_state.questions:
        st.markdown(f"##### {t('当前问题清单')}")
        
        def _rm_question(idx):
            st.session_state.questions.pop(idx)
            st.session_state.q_version += 1

        for i, q in enumerate(st.session_state.questions):
            c1, c2 = st.columns([0.92, 0.08])
            with c1:
                edited = st.text_input(
                    f"{t('Q')}{i+1}",
                    value=q,
                    key=f"qe_v{st.session_state.q_version}_{i}",
                    label_visibility="collapsed",
                )
                _limit_caption(edited, QUESTION_MAX_CHARS)
            with c2:
                st.button("🗑️", key=f"qd_v{st.session_state.q_version}_{i}", on_click=_rm_question, args=(i,))
    else:
        st.caption(t("暂无问题，请手动添加或使用 AI 生成"))


def _tab_scoring():
    engine = st.session_state.engine

    if "scoring_dims" not in st.session_state:
        st.session_state.scoring_dims = [
            t("购买意愿：你有多大意愿购买/使用该产品？"),
            t("需求紧迫度：你对该产品解决的问题有多紧迫？"),
            t("独特价值：相比现有方案，该产品有多独特？"),
        ]

    # AI 生成打分维度按钮
    setup_over_limit = _designer_persisted_inputs_over_limit()
    if st.button(t("✨ AI 生成建议打分维度"), key="ai_dims", disabled=setup_over_limit):
        if not engine:
            st.error(t("请先在侧边栏配置 API Key"))
        else:
            _sync_designer_inputs()
            concept_name = st.session_state.concepts[0].get("name", "")
            concept_desc = st.session_state.concepts[0].get("description", "")
            comparison_concepts = _valid_comparison_concepts()
            comparison_text = ""
            if comparison_concepts:
                comparison_text = f"\n{t('对照概念')}：\n"
                for idx, concept in enumerate(comparison_concepts, start=1):
                    comparison_text += f"{idx}. {concept.get('name', '')}: {concept.get('description', '')}\n"
                comparison_text += t("Comparison Dimension Requirement")
            with st.spinner(t("AI 正在生成打分维度...")):
                result = engine.chat_json(
                    t("Scoring Dims Prompt"),
                    f"{t('研究概念')}：{concept_name} - {concept_desc}\n{t('目标受众')}：{st.session_state.target_audience}{comparison_text}",
                    temperature=0.3, max_tokens=500)
                if isinstance(result, dict):
                    ai_dims = result.get("dims") or result.get("dimensions")
                    if not ai_dims:
                        for val in result.values():
                            if isinstance(val, list):
                                ai_dims = val
                                break
                elif isinstance(result, list):
                    ai_dims = result
                else:
                    ai_dims = []
                    
                if ai_dims:
                    extracted_dims = []
                    for dim in ai_dims:
                        val_str = ""
                        if isinstance(dim, str):
                            val_str = dim
                        elif isinstance(dim, dict):
                            vals = [str(v) for v in dim.values() if isinstance(v, str) and v]
                            if vals:
                                val_str = " - ".join(vals)
                        else:
                            val_str = str(dim)
                        if val_str and val_str not in st.session_state.scoring_dims:
                            extracted_dims.append(val_str)
                    if extracted_dims:
                        st.session_state.scoring_dims.extend(extracted_dims)
                    if comparison_concepts and not _contains_comparison_item(st.session_state.scoring_dims, concept_name, comparison_concepts):
                        st.session_state.scoring_dims.insert(0, t(
                            "对比偏好倾向：相比 {comparisons}，你有多倾向选择 {main} 而不是对照概念？",
                            main=concept_name,
                            comparisons=_comparison_names_text(comparison_concepts)
                        ))
                    st.rerun()

    st.markdown("---")

    if "d_version" not in st.session_state:
        st.session_state.d_version = 0

    if st.session_state.scoring_dims:
        def _rm_scoring_dim(idx):
            st.session_state.scoring_dims.pop(idx)
            st.session_state.d_version += 1

        for i, dim in enumerate(st.session_state.scoring_dims):
            c1, c2 = st.columns([0.9, 0.1])
            with c1:
                st.session_state.scoring_dims[i] = st.text_input(
                    t("维度"), value=dim, key=f"d_v{st.session_state.d_version}_{i}", label_visibility="collapsed")
            with c2:
                st.button("🗑️", key=f"ddel_v{st.session_state.d_version}_{i}", on_click=_rm_scoring_dim, args=(i,))

    nd = st.text_input(t("手动添加维度"), placeholder=t("输入打分维度后点击添加"), key="nd_input")
    if st.button(t("➕ 添加维度"), key="add_d") and nd:
        st.session_state.scoring_dims.append(nd)
        st.rerun()


# ============================================================
# Page 4: Persona Roster
# ============================================================
def page_personas():
    engine = st.session_state.engine
    if not engine:
        st.error(t("⚠️ 请先在侧边栏配置 API Key"))
        st.stop()

    render_workflow_dots(6, 2)
    render_page_header(t("合成画像管理"), t("基于大五人格与 DISC 模型生成的深度用户画像"))
    concept_text = f"{st.session_state.concepts[0]['name']}: {st.session_state.concepts[0]['description']}"

    if not st.session_state.personas:
        with st.status(t("🧬 正在生成 {n} 位合成用户画像...", n=st.session_state.sample_size)) as status:
            progress_bar = st.progress(0, text=t("准备分批生成画像..."))

            def _persona_progress(done, total, batch, batches):
                progress_bar.progress(
                    min(1.0, done / max(1, total)),
                    text=t(
                        "正在分批生成画像：第 {batch}/{batches} 批，已完成 {done}/{total}",
                        batch=batch,
                        batches=batches,
                        done=done,
                        total=total,
                    ),
                )

            try:
                st.session_state.personas = generate_personas(
                    engine, st.session_state.target_audience, concept_text,
                    st.session_state.sample_size, st.session_state.challenges,
                    progress_callback=_persona_progress)
                progress_bar.progress(1.0, text=t("画像批次生成完成：{done}/{total}", done=len(st.session_state.personas), total=st.session_state.sample_size))
                status.update(label=t("画像生成完成"), state="complete")
            except Exception as e:
                status.update(label=t("画像生成失败"), state="error")
                st.error(f"{t('画像生成失败')}：{e}")
                st.stop()
        st.rerun()

    # Grid display
    n = len(st.session_state.personas)
    cols_per_row = min(3, n)
    for i, persona in enumerate(st.session_state.personas):
        if i % cols_per_row == 0:
            persona_cols = st.columns(cols_per_row)
        with persona_cols[i % cols_per_row]:
            render_persona_card(persona, show_radar=True, expanded=True, key_suffix=str(i))

            # 自定义标签管理
            new_tag = st.text_input(t("添加标签"), placeholder=t("例如：价格敏感"), key=f"ptag_{i}", label_visibility="collapsed")
            if st.button(t("＋ 添加标签"), key=f"ptag_add_{i}") and new_tag:
                if "extra_constraints" not in persona:
                    persona["extra_constraints"] = []
                persona["extra_constraints"].append(new_tag)
                st.rerun()

            extras = persona.get("extra_constraints", [])
            if extras:
                tag_row = st.columns(len(extras))
                for t_idx, tag in enumerate(extras):
                    with tag_row[t_idx]:
                        if st.button(f"🏷️ {tag} ✕", key=f"pdel_{i}_{t_idx}"):
                            persona["extra_constraints"].pop(t_idx)
                            st.rerun()
            
            def _rm_persona(p_idx):
                st.session_state.personas.pop(p_idx)
                # 清除相关组件的缓存状态
                for k in list(st.session_state.keys()):
                    if k.startswith(f"ptag_{p_idx}") or k.startswith(f"pdel_{p_idx}"):
                        del st.session_state[k]
                st.session_state.p_version = st.session_state.get("p_version", 0) + 1

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            st.button(t("🗑️ 删除该画像"), key=f"p_remove_{st.session_state.get('p_version',0)}_{i}", 
                      type="secondary", use_container_width=True, 
                      on_click=_rm_persona, args=(i,))

    st.markdown("<br>", unsafe_allow_html=True)
    add_col1, add_col2 = st.columns([0.2, 0.8])
    with add_col1:
        add_num = st.number_input(t("添加画像数量"), min_value=1, max_value=10, value=2, step=1, label_visibility="collapsed")
    with add_col2:
        if st.button(t("➕ 再生成 {n} 个新画像", n=add_num), use_container_width=False):
            with st.status(t("🧬 正在生成 {n} 个新合成用户画像...", n=add_num)) as status:
                progress_bar = st.progress(0, text=t("准备分批生成画像..."))

                def _new_persona_progress(done, total, batch, batches):
                    progress_bar.progress(
                        min(1.0, done / max(1, total)),
                        text=t(
                            "正在分批生成画像：第 {batch}/{batches} 批，已完成 {done}/{total}",
                            batch=batch,
                            batches=batches,
                            done=done,
                            total=total,
                        ),
                    )

                new_personas = generate_personas(
                    engine, st.session_state.target_audience, concept_text,
                    add_num, st.session_state.challenges,
                    existing_personas=st.session_state.personas,
                    progress_callback=_new_persona_progress)
                st.session_state.personas.extend(new_personas)
                progress_bar.progress(1.0, text=t("画像批次生成完成：{done}/{total}", done=len(new_personas), total=add_num))
                status.update(label=t("画像生成完成"), state="complete")
            st.rerun()

    st.divider()
    c1, c2 = st.columns([0.5, 0.5])
    with c1:
        if st.button(t("← 返回工作台"), key="back_4"):
            goto(3)
    with c2:
        next_label = t("🚀 开始访谈") if st.session_state.get("research_mode", "qualitative") == "qualitative" else t("🚀 开始打分")
        if st.button(next_label, key="next_4", use_container_width=True):
            goto(5)


# ============================================================
# Page 5: Execution (Focus Mode)
# ============================================================
def page_execution():
    engine = st.session_state.engine
    if not engine:
        st.error(t("⚠️ 请先配置 API Key"))
        st.stop()

    concept_text = f"{st.session_state.concepts[0]['name']}: {st.session_state.concepts[0]['description']}"
    mode = st.session_state.research_mode

    if mode == "qualitative":
        render_workflow_dots(6, 3)
        render_focus_mode_header(t("Qualitative Interviews"), t("{n} Participants Active", n=len(st.session_state.personas)))

        if st.session_state.interview_mode == "1v1":
            if not st.session_state.get("interview_results"):
                if st.button(t("▶️ 开始全部访谈"), key="start_iv", use_container_width=True):
                    st.session_state._qual_generating = True
                    iv_engine = InterviewEngine(engine, st.session_state.personas, concept_text)
                    interview_results = {}
                    
                    with st.container():
                        persona_placeholders = []
                        # Create all expanders upfront
                        for p in st.session_state.personas:
                            exp = st.expander(f"👤 {p.get('name', t('未知'))} - {t('Waiting')}", expanded=True)
                            with exp:
                                status_ph = st.empty()
                                content_ph = st.container()
                                with status_ph.container():
                                    st.markdown(f'<div class="thinking-pill">{t("QUEUED: WAITING FOR START")}</div>', unsafe_allow_html=True)
                                persona_placeholders.append({"status": status_ph, "content": content_ph, "expander": exp})
                        
                        # Sequential execution but with persistent state
                        for p_idx, persona in enumerate(st.session_state.personas):
                            placeholders = persona_placeholders[p_idx]
                            
                            # Update status to ACTIVE
                            placeholders["status"].markdown(f'<div class="thinking-pill">{t("LIVE: INTERVIEW IN PROGRESS")}</div>', unsafe_allow_html=True)
                            
                            transcript = []
                            full_answer = ""
                            answer_placeholder = None
                            
                            # Use the content container for messages
                            with placeholders["content"]:
                                for msg in iv_engine.run_interview_stream(persona, st.session_state.questions):
                                    if msg["type"] == "question":
                                        st.markdown(f"**{t('🙋 调研员：')}** {msg['content']}")
                                        transcript.append(msg)
                                        answer_placeholder = None
                                    elif msg["type"] == "answer_chunk":
                                        if answer_placeholder is None:
                                            answer_placeholder = st.empty()
                                        full_answer += msg["content"]
                                        answer_placeholder.markdown(get_chat_bubble_html(persona.get("name", t("未知")), full_answer + " ▌", persona, "agent"), unsafe_allow_html=True)
                                    elif msg["type"] == "answer_complete":
                                        full_answer = msg["content"]
                                        if answer_placeholder:
                                            answer_placeholder.markdown(get_chat_bubble_html(persona.get("name", t("未知")), full_answer, persona, "agent"), unsafe_allow_html=True)
                                        transcript.append({"type": "answer", "content": full_answer})
                                        full_answer = ""
                            
                            interview_results[persona.get("id", persona.get("name", "unknown"))] = transcript
                            
                            # Final Status: COMPLETED
                            placeholders["status"].markdown(clean_html(f'''
                                <div style="display: flex; align-items: center; gap: 12px; padding: 14px; background: #22C55E15; border-radius: 12px; border: 1px solid #22C55E40;">
                                    <div class="scoring-status-pill" style="background: #22C55E;">
                                        <div class="scoring-status-dot" style="background: white;"></div>
                                    </div>
                                    <span style="font-weight: 700; font-size: 0.95rem; color: #22C55E; font-family: var(--font-mono);">{t("FINISH: SESSION COMPLETED")}</span>
                                </div>
                            '''), unsafe_allow_html=True)
                        
                        st.balloons()
                    
                    st.session_state.interview_results = interview_results
                    st.session_state._qual_generating = False
            else:
                st.markdown(f'<div class="thinking-pill" style="border-color: var(--border); color: var(--muted-foreground); box-shadow: none; animation: none;">{t("Waiting")}</div>', unsafe_allow_html=True)
                for p_idx, persona in enumerate(st.session_state.personas):
                    persona_id = persona.get("id", persona.get("name", "unknown"))
                    transcript = st.session_state.interview_results.get(persona_id, [])
                    with st.expander(f"📝 {persona.get('name', t('未知'))} {t('的访谈')}", expanded=(p_idx == 0)):
                        for msg in transcript:
                            if msg["type"] == "question":
                                st.markdown(f"**{t('🙋 调研员：')}** {msg['content']}")
                            else:
                                render_chat_bubble(persona.get("name", t("未知")), msg["content"], persona, "agent")
        else:
            if not st.session_state.get("focus_group_history"):
                if st.button(t("▶️ 开始焦点小组"), key="start_fg", use_container_width=True):
                    fg = FocusGroupEngine(engine, st.session_state.personas, concept_text)
                    full_session = []

                    # ── Top live banner ──────────────────────────────────
                    top_status = st.empty()
                    top_status.markdown(clean_html(f'''
                        <div style="display:flex;align-items:center;gap:14px;padding:16px 20px;
                                    background:var(--muted);border-radius:14px;
                                    border:1px solid var(--border);margin-bottom:20px;">
                            <div class="scoring-status-pill scoring-status-pulse"
                                 style="background:var(--accent);">
                                <div class="scoring-status-dot" style="background:white;"></div>
                            </div>
                            <span style="font-weight:700;font-size:0.95rem;
                                         color:var(--accent);font-family:var(--font-mono);">
                                {t("LIVE: FOCUS GROUP IN PROGRESS")}
                            </span>
                        </div>
                    '''), unsafe_allow_html=True)

                    # ── Shared "thinking" pill – lives below the live banner ──
                    thinking_ph = st.empty()

                    def _show_thinking(speaker_name: str = ""):
                        label = f"{speaker_name} · " if speaker_name else ""
                        thinking_ph.markdown(clean_html(f'''
                            <div style="display:flex;align-items:center;gap:10px;
                                        padding:10px 16px;margin:4px 0 10px 0;
                                        background:var(--muted);border-radius:10px;
                                        border:1px dashed var(--border);">
                                <div class="scoring-status-pill scoring-status-pulse"
                                     style="background:var(--accent);opacity:0.8;">
                                    <div class="scoring-status-dot"
                                         style="background:white;"></div>
                                </div>
                                <span style="font-size:0.85rem;color:var(--muted-foreground);
                                             font-family:var(--font-mono);">
                                    {label}{t("采访中，请稍后...")}
                                </span>
                            </div>
                        '''), unsafe_allow_html=True)

                    for q_idx, question in enumerate(st.session_state.questions):
                        st.markdown(f"---\n#### {t('Round {n}', n=q_idx+1)}")
                        full_session.append({"type": "round_header", "content": f"#### {t('Round {n}', n=q_idx+1)}"})

                        # Peek-ahead iteration: show thinking BEFORE each API call
                        gen = fg.run_round(question)
                        try:
                            pending_msg = next(gen)
                            while True:
                                # Show thinking for NEXT speaker while this one is done
                                thinking_ph.empty()
                                full_session.append(pending_msg)
                                render_chat_bubble(
                                    pending_msg["speaker"],
                                    pending_msg["content"],
                                    pending_msg.get("persona"),
                                    pending_msg["type"],
                                )
                                # Show thinking pill before calling next()
                                _show_thinking()
                                pending_msg = next(gen)
                        except StopIteration:
                            thinking_ph.empty()

                    # ── Clear banners and save ───────────────────────────
                    top_status.empty()
                    st.session_state.focus_group_history = full_session
                    st.rerun()
            else:
                st.success(t("✅ 焦点小组讨论结束！"))
                for msg in st.session_state.focus_group_history:
                    if msg.get("type") == "round_header":
                        st.markdown(f"---\n{msg['content']}")
                    else:
                        render_chat_bubble(msg["speaker"], msg["content"], msg.get("persona"), msg["type"])
    else:
        render_workflow_dots(6, 3)

        personas = st.session_state.personas
        total = len(personas)

        # 如果还没有结果，执行打分
        if st.session_state.quant_results is None:
            render_focus_mode_header(t("📊 Quantitative Scoring"), t("Analyzing Concept with {n} Personas", n=total))
            
            # 创建容器列表
            respondent_placeholders = []
            for persona in personas:
                placeholder = st.empty()
                with placeholder:
                    render_scoring_persona_card(persona, is_loading=True)
                respondent_placeholders.append(placeholder)

            all_results = []
            for idx, persona in enumerate(personas):
                demo = persona.get("demographics", {})
                psych = persona.get("psychographics", {})
                system_prompt, user_prompt = build_quant_scoring_prompts(
                    persona,
                    concept_text,
                    st.session_state.scoring_dims,
                )

                with respondent_placeholders[idx]:
                    try:
                        full_response = ""
                        # 流式输出
                        for chunk in engine.chat_stream(system_prompt, user_prompt, temperature=0.7, max_tokens=700):
                            full_response += chunk
                            # 实时更新，移除最后的 JSON 块显示
                            display_text = re.split(r"```json|\{", full_response)[0].strip()
                            
                            with respondent_placeholders[idx]:
                                render_scoring_persona_card(persona, content=display_text, is_loading=True)
                        
                        # 尝试提取 JSON
                        json_match = re.search(r"(\{.*\}|```json\s*(\{.*\}))", full_response, re.DOTALL)
                        scores_json = {}
                        if json_match:
                            json_str = json_match.group(1) if not json_match.group(2) else json_match.group(2)
                            try:
                                scores_json = json.loads(json_str)
                            except:
                                clean_json = re.sub(r"//.*", "", json_str)
                                try: scores_json = json.loads(clean_json)
                                except: pass
                        
                        # 统一列名以适配分析引擎
                        row = {
                            "ID": idx + 1, 
                            "姓名": persona.get("name", t("未知")), 
                            "Name": persona.get("name", t("未知")),
                            "职业": demo.get("occupation", t("未知")),
                            "Role": demo.get("occupation", t("未知")),
                            "年龄": demo.get("age", 0),
                            "Age": demo.get("age", 0),
                            "DISC": psych.get("disc_profile", t("未知"))
                        }
                        
                        # 提取平均分
                        total_score = 0
                        valid_dims = 0
                        
                        for d_raw in st.session_state.scoring_dims:
                            d_name = d_raw['name'] if isinstance(d_raw, dict) else d_raw
                            d_name_clean = d_name.strip().lower()
                            raw_score = None
                            
                            if d_name in scores_json: raw_score = scores_json[d_name]
                            else:
                                for k, v in scores_json.items():
                                    if k.strip().lower() == d_name_clean:
                                        raw_score = v
                                        break
                            
                            if raw_score is None:
                                for k, v in scores_json.items():
                                    if d_name_clean in k.strip().lower() or k.strip().lower() in d_name_clean:
                                        raw_score = v
                                        break
                            
                            if raw_score is None: raw_score = 3

                            try:
                                s_str = str(raw_score).strip()
                                cn_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5}
                                if s_str and s_str[0] in cn_map:
                                    clean_score = cn_map[s_str[0]]
                                else:
                                    num_match = re.search(r'[1-5]', s_str)
                                    if num_match: clean_score = int(num_match.group(0))
                                    else: clean_score = int(float(s_str))
                                row[d_name] = max(1, min(5, clean_score))
                            except:
                                row[d_name] = 3
                        
                        # 计算平均分 (仅针对维度分)
                        dim_names = [d['name'] if isinstance(d, dict) else d for d in st.session_state.scoring_dims]
                        score_values = [v for k, v in row.items() if k in dim_names]
                        avg_score = sum(score_values) / len(score_values) if score_values else 3.0

                        # 最终渲染 (包含得分星级)
                        final_reason = re.sub(r"```json.*", "", full_response, flags=re.DOTALL).strip()
                        with respondent_placeholders[idx]:
                            render_scoring_persona_card(persona, content=final_reason, is_loading=False, scores=row)
                        
                        all_results.append(row)
                        
                    except Exception as e:
                        st.error(f"❌ {t('打分失败: {e}', e=str(e))}")

            # 打分完成，进入分析
            df = pd.DataFrame(all_results)
            st.session_state.quant_results = df
            st.session_state.quant_analysis = analyze_results(df, st.session_state.scoring_dims)
            st.session_state.pop("quant_report_text", None)
            st.session_state.pop("quant_report_key", None)
            time.sleep(1)
            st.rerun()

        else:
            # 已有结果，展示
            render_focus_mode_header(t("📊 打分完成"), t("共 {n} 位用户", n=total))
            st.markdown(f"### {t('📋 打分结果')}")
            st.dataframe(st.session_state.quant_results, use_container_width=True)

    st.divider()
    # 定量模式下，打分生成中时禁用底部按钮
    quant_generating = (mode == "quantitative" and st.session_state.quant_results is None)
    # 定性模式下，访谈生成中禁用底部按钮
    qual_generating = (mode == "qualitative" and st.session_state.get("_qual_generating", False))
    
    disabled_state = quant_generating or qual_generating

    c1, c2 = st.columns([0.5, 0.5])
    with c1:
        if st.button(t("← 返回上一步"), key="back_5", disabled=disabled_state):
            goto(4)
    with c2:
        if st.button(t("📄 生成报告"), key="next_5", use_container_width=True, disabled=disabled_state):
            goto(6)


# ============================================================
# Page 6: Report
# ============================================================
def page_report():
    engine = st.session_state.engine
    mode = st.session_state.research_mode
    render_workflow_dots(6, 5)

    st.markdown(f"## {t('📄 研究报告')}")

    if mode == "qualitative":
        # 自动触发生成（如果尚未生成）
        if not st.session_state.report:
            if not engine:
                st.error(t("请先在设置中配置 API Key 以生成报告"))
                if st.button(t("⚙️ 前往设置"), key="goto_settings_report"):
                    st.session_state.current_page = 0
                    st.rerun()
                return

            concept_text = f"{st.session_state.concepts[0]['name']}: {st.session_state.concepts[0]['description']}"
            with st.spinner(t("📝 正在生成分析报告...")):
                st.session_state.report = generate_qualitative_report(
                    engine, concept_text,
                    st.session_state.interview_results,
                    st.session_state.focus_group_history)
            st.rerun()

        report = st.session_state.report
        
        # 检查报告是否包含有效内容 (健壮性检查)
        exec_summary = report.get("executive_summary", "")
        is_failed = "failed" in exec_summary.lower() or t("No interview data") in exec_summary or not exec_summary.strip()
        
        if is_failed:
            st.warning(t("报告生成不完整或数据不足，请尝试重新生成"))
            if exec_summary:
                st.info(exec_summary)
            
            # 增加一个更显眼的再次生成按钮
            if st.button(t("🔄 再次尝试生成报告"), key="retry_gen_qual_top_huge", type="primary", use_container_width=True):
                st.session_state.report = None
                st.rerun()
                
            if not exec_summary.strip():
                st.error(t("生成的报告内容为空。这可能是因为访谈数据不足或 AI 解析失败。"))
                return
        
        if report and isinstance(report, dict):
            st.markdown(t("### 📋 执行摘要"))
            st.markdown(report.get("executive_summary", t("未知")))

            # 1. Resonance, Objections, Improvements (New Professional Sections)
            cols = st.columns(3)
            with cols[0]:
                st.markdown(f"#### ✅ {t('共鸣点')}")
                res = report.get("resonance_points", [])
                if res:
                    for p in res: st.markdown(f"- {p}")
                else: st.caption(t("暂无显著发现"))
            with cols[1]:
                st.markdown(f"#### ❌ {t('异议与担忧')}")
                objs = report.get("opposition_points", [])
                if objs:
                    for p in objs: st.markdown(f"- {p}")
                else: st.caption(t("暂无显著发现"))
            with cols[2]:
                st.markdown(f"#### 💡 {t('改进建议')}")
                imps = report.get("improvement_suggestions", [])
                if imps:
                    for p in imps: st.markdown(f"- {p}")
                else: st.caption(t("暂无显著发现"))

            # 2. Strategic Insights
            st.markdown(t("### 🎯 核心洞察"))
            insights = report.get("key_insights", [])
            if insights:
                for idx, insight in enumerate(insights):
                    with st.expander(f"{idx+1}. {insight.get('title', t('未知'))}", expanded=True):
                        st.markdown(insight.get("description", insight.get("content", "")))
            else:
                st.info(t("暂无显著发现"))

            # 3. Product Evaluation (Strengths, Weaknesses, Opportunities)
            st.markdown(t("### 📋 产品评估"))
            pe = report.get("product_evaluation", {})
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**{t('优势')}**")
                strengths = pe.get("strengths", [])
                if strengths:
                    for s in strengths: st.markdown(f"✅ {s}")
                else: st.caption(t("暂无"))
            with c2:
                st.markdown(f"**{t('劣势')}**")
                weaknesses = pe.get("weaknesses", [])
                if weaknesses:
                    for w in weaknesses: st.markdown(f"❌ {w}")
                else: st.caption(t("暂无"))
            with c3:
                st.markdown(f"**{t('机会')}**")
                opportunities = pe.get("opportunities", [])
                if opportunities:
                    for o in opportunities: st.markdown(f"💡 {o}")
                else: st.caption(t("暂无"))

            # 4. Strategic Recommendations / Roadmap
            st.markdown(t("### 🚀 建议路线图"))
            recommendations = report.get("strategic_recommendations", [])
            if recommendations:
                for rec in recommendations:
                    prio = rec.get("priority", "Medium")
                    # 设置优先级颜色
                    prio_color = "red" if prio.lower() == "high" else "orange" if prio.lower() == "medium" else "blue"
                    st.markdown(f"""
                    <div style="padding: 12px; border-radius: 8px; border-left: 5px solid {prio_color}; background-color: rgba(255,255,255,0.05); margin-bottom: 10px;">
                        <span style="font-weight: bold; color: {prio_color}; text-transform: uppercase; font-size: 0.8em;">[{t(prio)}]</span>
                        <div style="font-weight: 600; margin-top: 4px;">{rec.get("suggestion", rec.get("action", ""))}</div>
                        <div style="font-size: 0.9em; opacity: 0.8; margin-top: 4px;"><b>{t('影响')}:</b> {rec.get("impact", rec.get("reason", ""))}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info(t("暂无具体建议"))

            # 4. Key Quotes
            st.markdown(t("### 💬 Key Quotes"))
            quotes = report.get("key_quotes", [])
            if quotes:
                for q in quotes:
                    if isinstance(q, dict):
                        st.markdown(f'> "{q.get("quote", "")}" —— **{q.get("speaker", t("未知发言者"))}**')
                    else:
                        st.markdown(f'> "{str(q)}" —— **{t("未知发言者")}**')
            else:
                st.info(t("暂无关键引用"))

            st.divider()
            st.markdown(t("### 🛠️ {n}", n=t("操作与导出")))
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button(t("🔄 重新生成报告"), key="regen_qual", use_container_width=True):
                    st.session_state.report = None
                    st.rerun()
            with c2:
                st.download_button(t("📄 报告 Markdown"), data=report.get("full_report", ""),
                                   file_name=f"{st.session_state.project_name or 'report'}.md", mime="text/markdown", use_container_width=True)
            with c3:
                results = st.session_state.get("interview_results", [])
                history = st.session_state.get("focus_group_history", [])
                csv_df = export_transcripts_csv(results, history)
                if not csv_df.empty:
                    st.download_button(t("📊 访谈记录 CSV"), data=csv_df.to_csv(index=False, encoding="utf-8-sig"),
                                       file_name="transcripts.csv", mime="text/csv", use_container_width=True)
                else:
                    st.button(t("📊 访谈记录 CSV"), disabled=True, use_container_width=True)
            with c4:
                if st.session_state.personas:
                    st.download_button(t("👥 画像 JSON"), data=export_personas_json(st.session_state.personas),
                                       file_name="personas.json", mime="application/json", use_container_width=True)
    else:
        if st.session_state.quant_results is not None:
            df = st.session_state.quant_results
            analysis = st.session_state.get("quant_analysis", {})
            concept_text = f"{st.session_state.concepts[0]['name']}: {st.session_state.concepts[0]['description']}"
            current_report_key = _quant_report_key(concept_text, df, analysis)

            # 生成定量研究的文本报告
            if (
                "quant_report_text" not in st.session_state
                or not st.session_state.quant_report_text
                or st.session_state.get("quant_report_key") != current_report_key
            ):
                if not engine:
                    st.error(t("请先在设置中配置 API Key 以生成报告"))
                else:
                    with st.spinner(t("📝 正在生成定量研究深度分析报告...")):
                        st.session_state.quant_report_text = generate_quantitative_report(
                            engine, concept_text, df, analysis
                        )
                        st.session_state.quant_report_key = current_report_key
                    st.rerun()

            st.markdown(t("### 📝 深度分析报告"))
            quant_report = st.session_state.get("quant_report_text", "")
            
            # 增强错误检测
            if not quant_report or "failed" in quant_report.lower():
                if not quant_report:
                    st.warning(t("报告内容为空"))
                else:
                    st.error(quant_report)
                    
                if st.button(t("🔄 再次尝试生成报告"), key="retry_gen_quant_top", type="primary", use_container_width=True):
                    if "quant_report_text" in st.session_state:
                        del st.session_state.quant_report_text
                    if "quant_report_key" in st.session_state:
                        del st.session_state.quant_report_key
                    st.rerun()
                
                if not quant_report:
                    return # 空报告不继续渲染
            else:
                st.markdown(quant_report)
            st.divider()
            st.markdown(t("### 📊 整体评分"))
            overall = analysis.get("overall_scores", {})
            if overall:
                score_items = list(overall.items())
                for start in range(0, len(score_items), 3):
                    score_cols = st.columns(min(3, len(score_items) - start))
                    for col, (dim, score) in zip(score_cols, score_items[start:start + 3]):
                        with col:
                            render_stat_card(f"{score:.1f}", dim)

            st.markdown(t("### 🎯 DISC 类型分析"))
            disc_data = analysis.get("disc_analysis", {})
            if disc_data:
                disc_df = pd.DataFrame(disc_data).T
                fig = px.bar(disc_df, barmode="group", color_discrete_sequence=list(DISC_COLORS.values()))
                fig.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)

            age_data = analysis.get("age_analysis", {})
            if age_data:
                st.markdown(t("### 📈 年龄段分析"))
                age_df = pd.DataFrame(age_data).T
                fig2 = px.line(age_df, markers=True)
                fig2.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig2, use_container_width=True)

            st.divider()
            st.markdown(t("### 🛠️ {n}", n=t("操作与导出")))
            c1, c2 = st.columns(2)
            with c1:
                if st.button(t("🔄 重新生成报告"), key="regen_quant", use_container_width=True):
                    if "quant_report_text" in st.session_state:
                        del st.session_state.quant_report_text
                    if "quant_report_key" in st.session_state:
                        del st.session_state.quant_report_key
                    st.rerun()
            with c2:
                st.download_button(t("📥 下载数据 CSV"), data=df.to_csv(index=False, encoding="utf-8-sig"),
                                   file_name="quant_results.csv", mime="text/csv", use_container_width=True)
        else:
            st.info(t("暂无数据，请先执行验证"))

    st.divider()
    c1, c2 = st.columns([0.5, 0.5])
    with c1:
        if st.button(t("← 返回"), key="back_6"):
            goto(5)
    with c2:
        if st.button(t("🔄 新建研究"), key="restart"):
            save_current_project()
            clear_current_project()
            goto(0)
