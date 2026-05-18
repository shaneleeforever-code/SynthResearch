"""
SynthResearch - 合成用户调研平台
主入口：Apple-Inspired Workflow UI
"""

import sys
import os
import json
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from dotenv import load_dotenv

from app.styles import inject_css
from app.engine import SynthEngine
from app.pages import (
    page_dashboard, page_init, page_path_select,
    page_designer, page_personas, page_execution, page_report,
    load_project, save_current_project,
)
from app.i18n import t
from app.project_store import (
    get_project_landing_page,
    load_projects,
    save_projects,
    serialize_value,
    deserialize_value,
)

# ============================================================
# Page Config
# ============================================================
st.set_page_config(
    page_title="SynthResearch",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()
load_dotenv("config/.env")

CACHE_FILE = "config/session_cache.json"
CACHE_KEYS = [
    "current_page", "current_project_id", "research_mode", "project_name", "project_desc",
    "target_audience", "challenges", "sample_size", "concepts",
    "questions", "personas", "interview_mode", "interview_results",
    "focus_group_history", "quant_results", "quant_phase", "quant_personas",
    "report", "projects", "scoring_dims", "quant_analysis",
    "quant_report_text", "quant_report_key",
    "_qual_generating", "_quant_generating", "_ai_suggestions",
    "ui_lang", "output_lang"
]

# ============================================================
# Session State Defaults
# ============================================================
# Load state on fresh start
if "loaded_from_cache" not in st.session_state:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                saved_state = json.load(f)
            for k, v in saved_state.items():
                if k in CACHE_KEYS:
                    st.session_state[k] = deserialize_value(v)
        except Exception as e:
            pass
    st.session_state["loaded_from_cache"] = True

defaults = {
    "current_page": 0,
    "current_project_id": "",
    "research_mode": "qualitative",
    "project_name": "",
    "project_desc": "",
    "target_audience": "",
    "challenges": [],
    "sample_size": 10,
    "concepts": [{"name": "", "description": ""}],
    "questions": [],
    "personas": [],
    "interview_mode": "1v1",
    "interview_results": {},
    "focus_group_history": [],
    "quant_results": None,
    "quant_phase": 0,
    "quant_personas": [],
    "report": None,
    "engine": None,
    "projects": [],
    "ui_lang": "English",
    "output_lang": "English",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "loaded_projects_store" not in st.session_state:
    disk_projects = load_projects()
    if disk_projects:
        st.session_state.projects = disk_projects
    elif st.session_state.get("projects"):
        save_projects(st.session_state.projects)
    st.session_state["loaded_projects_store"] = True


def _query_param_value(name: str):
    try:
        value = st.query_params.get(name)
        if isinstance(value, list):
            return value[0] if value else None
        return value
    except Exception:
        return None


open_project_id = _query_param_value("open_project")
if open_project_id:
    target_project = next(
        (p for p in st.session_state.get("projects", []) if p.get("project_id") == open_project_id),
        None,
    )
    if target_project:
        raw_page = _query_param_value("page")
        try:
            target_page = int(raw_page) if raw_page is not None else get_project_landing_page(target_project)
        except (TypeError, ValueError):
            target_page = get_project_landing_page(target_project)
        load_project(target_project)
        st.session_state.current_page = target_page
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()

# ============================================================
# Persistent Header
# ============================================================
# 注入 CSS 统一样式：强制单行显示，并且修复 button 和 popover 的边框一致性
st.markdown("""
<style>
div[data-testid="stButton"] > button, div[data-testid="stPopover"] > button {
    white-space: nowrap !important;
    border-radius: 8px !important;
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.3s ease !important;
}
.status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    transition: all 0.3s ease;
}
.status-online {
    background-color: #10b981;
    box-shadow: 0 0 10px #10b981, 0 0 20px rgba(16, 185, 129, 0.4);
}
.status-offline {
    background-color: #ef4444;
    box-shadow: 0 0 10px #ef4444, 0 0 20px rgba(239, 68, 68, 0.4);
}
</style>
""", unsafe_allow_html=True)

col_title, col_home, col_config, col_lang, col_status = st.columns([0.45, 0.18, 0.14, 0.16, 0.07], vertical_alignment="center")

with col_title:
    st.markdown("<h1 style='margin: 0; padding: 0; white-space: nowrap; font-size: 26px;'>🔬 SynthResearch</h1>", unsafe_allow_html=True)

with col_home:
    if st.session_state.get("current_page", 0) != 0:
        if st.button(t("🏠 返回主页"), key="btn_gohome", use_container_width=True):
            from app.pages import save_current_project
            save_current_project()
            st.session_state.current_page = 0
            st.rerun()

with col_config:
    with st.popover(t("⚙️ 设置"), use_container_width=True):
        api_key = st.text_input(t("API Key"), type="password",
                                value=os.getenv("OPENAI_API_KEY", ""), key="api_key_input")
        base_url = st.text_input(t("Base URL"),
                                 value=os.getenv("BASE_URL", "https://api.openai.com/v1"), key="base_url_input")
        model_name = st.text_input(t("模型"), value=os.getenv("MODEL_NAME", "gpt-4o"),
                                   placeholder=t("gpt-4o / deepseek-chat"), key="model_input")

        if api_key:
            st.session_state.engine = SynthEngine(api_key=api_key, base_url=base_url, model=model_name)

def on_ui_lang_change():
    new_ui = st.session_state.ui_lang_radio
    st.session_state.ui_lang = new_ui
    st.session_state.output_lang = new_ui

current_lang = st.session_state.get("ui_lang_radio", st.session_state.get("ui_lang", "English"))
st.session_state.ui_lang = current_lang
st.session_state.output_lang = current_lang

with col_lang:
    with st.popover(t("🌐 语言"), use_container_width=True):
        st.radio(t("显示语言 (UI)"), ["中文", "English"],
            index=0 if st.session_state.get("ui_lang", "English") == "中文" else 1,
            key="ui_lang_radio", on_change=on_ui_lang_change)

with col_status:
    if "engine" in st.session_state and st.session_state.engine:
        st.markdown(
            f"<div style='display: flex; justify-content: flex-start; align-items: center;' title='{t('模型已连接')}'>"
            "<div class='status-indicator status-online'></div>"
            "</div>", 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div style='display: flex; justify-content: flex-start; align-items: center;' title='{t('模型未连接')}'>"
            "<div class='status-indicator status-offline'></div>"
            "</div>", 
            unsafe_allow_html=True
        )

st.divider()

# ============================================================
# Page Router
# ============================================================
page = st.session_state.current_page

if page == 0:
    page_dashboard()
elif page == 1:
    page_init()
elif page == 2:
    page_path_select()
elif page == 3:
    page_designer()
elif page == 4:
    page_personas()
elif page == 5:
    page_execution()
elif page == 6:
    page_report()
else:
    page_dashboard()

try:
    if st.session_state.get("current_page", 0) != 0 and st.session_state.get("project_name"):
        save_current_project()
except Exception:
    pass

# ============================================================
# Save State to Cache
# ============================================================
try:
    state_to_save = {}
    for k in CACHE_KEYS:
        if k in st.session_state:
            v = st.session_state[k]
            state_to_save[k] = serialize_value(v)
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_to_save, f, ensure_ascii=False)
except Exception as e:
    pass
