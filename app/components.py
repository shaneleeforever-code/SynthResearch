"""
SynthResearch - UI 组件库
Minimalist Modern 可复用 Streamlit 组件
"""

import streamlit as st
import plotly.graph_objects as go
import html as _html
import textwrap
import re
from typing import List, Dict, Optional
from app.styles import DISC_COLORS
from app.i18n import t

def clean_html(html: str) -> str:
    """
    清理 HTML 字符串，移除每行的领先空格并移除所有换行符。
    这是为了防止 Streamlit 将缩进的 HTML 误认为 Markdown 代码块。
    同时确保标签之间有必要的空格（如果原先有的话）。
    """
    if not html:
        return ""
    # 移除每行首尾空白，过滤空行
    lines = [line.strip() for line in html.splitlines() if line.strip()]
    # 用空格连接，确保标签属性不会粘在一起，然后再压缩多余空格
    joined = " ".join(lines)
    # 压缩多个空格为单个空格
    return re.sub(r'\s+', ' ', joined).strip()


def render_section_label(label: str):
    """
    渲染带有脉冲呼吸灯点的章节标签
    """
    html = f'''
    <div class="section-label">
        <div class="section-label-dot"></div>
        <span class="section-label-text">{label}</span>
    </div>
    '''
    st.markdown(clean_html(html), unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = None):
    """
    渲染标准页面标题
    """
    subtitle_html = f'<p style="margin-top: -8px; margin-bottom: 32px;">{subtitle}</p>' if subtitle else ""
    html = f'''
    <div style="margin-bottom: 40px;">
        <h1 class="display-font"><span class="gradient-underline-wrap">{title}</span></h1>
        {subtitle_html}
    </div>
    '''
    st.markdown(clean_html(html), unsafe_allow_html=True)


def render_hero_section(title: str, subtitle: str, label: str = None):
    """
    渲染高冲击力的 Hero 区域
    """
    label_html = f'<div class="section-label"><div class="section-label-dot"></div><span class="section-label-text">{label}</span></div>' if label else ""
    html = f'''
    <div style="padding: 60px 0 80px 0; text-align: left;">
        {label_html}
        <h1 style="font-size: 4.5rem !important; margin-bottom: 24px;">{title}</h1>
        <p style="font-size: 1.25rem; max-width: 700px; margin-bottom: 40px; color: var(--muted-foreground);">{subtitle}</p>
    </div>
    '''
    st.markdown(clean_html(html), unsafe_allow_html=True)


def render_focus_mode_header(title: str, subtitle: str):
    """
    渲染沉浸模式下的头部（访谈/打分中）
    """
    html = f'''
    <div style="text-align: center; margin-bottom: 48px; padding: 40px; background: var(--muted); border-radius: var(--radius-2xl); border: 1px solid var(--border);">
        <h2 class="display-font" style="margin-bottom: 8px;">{title}</h2>
        <p style="color: var(--muted-foreground); font-family: var(--font-mono); font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.1em;">{subtitle}</p>
    </div>
    '''
    st.markdown(clean_html(html), unsafe_allow_html=True)


def render_workflow_dots(total: int, current: int):
    """
    渲染工作流圆点进度指示器
    """
    html_parts = ['<div class="workflow-steps">']
    for i in range(total):
        if i < current:
            dot_class = "workflow-dot workflow-dot-done"
        elif i == current:
            dot_class = "workflow-dot workflow-dot-active"
        else:
            dot_class = "workflow-dot"
        html_parts.append(f'<div class="{dot_class}"></div>')
        if i < total - 1:
            html_parts.append('<div style="width: 24px; height: 1px; background: var(--border);"></div>')
    html_parts.append("</div>")
    st.markdown(clean_html("".join(html_parts)), unsafe_allow_html=True)


def render_stepper(steps: List[str], current_step: int):
    """渲染步骤进度条（兼容旧接口）"""
    render_workflow_dots(len(steps), current_step)


def render_empty_state(icon: str, title: str, description: str):
    """渲染空状态占位"""
    html = f'''
    <div style="text-align: center; padding: 64px 24px; border: 1px dashed var(--border); border-radius: 24px; background: var(--muted);">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <h3 style="margin-bottom: 0.5rem;">{title}</h3>
        <p>{description}</p>
    </div>
    '''
    st.markdown(clean_html(html), unsafe_allow_html=True)


def render_project_card(name: str, description: str, research_type: str, created_at: str):
    """渲染项目卡片"""
    badge_text = t("🔍 定性研究") if research_type == "qualitative" else t("📊 定量验证")
    
    html = f'''
    <div class="project-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
            <span class="pill-badge pill-badge-tag">{badge_text}</span>
            <span style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--muted-foreground); opacity: 0.8;">{created_at}</span>
        </div>
        <h3 style="margin-top: 0; font-size: 1.5rem; margin-bottom: 12px;">{name}</h3>
        <p style="margin-bottom: 16px; font-size: 0.95rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 3.5rem;">
            {description or t("暂无描述")}
        </p>
    </div>
    '''
    st.markdown(clean_html(html), unsafe_allow_html=True)


def render_path_card(icon: str, title: str, description: str):
    """渲染路径选择卡片"""
    html = f'''
    <div class="path-card">
        <div class="path-icon">{icon}</div>
        <h2>{title}</h2>
        <div class="path-desc">
            <p>{description}</p>
        </div>
    </div>
    '''
    st.markdown(clean_html(html), unsafe_allow_html=True)


def render_persona_card(persona: Dict, show_radar: bool = True, expanded: bool = False, key_suffix: str = ""):
    """
    渲染 Persona 卡片
    """
    demo = persona.get("demographics", {})
    psych = persona.get("psychographics", {})
    big5 = psych.get("big_five", {})
    traits = persona.get("behavioral_traits", {})
    disc_primary = persona.get("_disc_primary", "S")
    disc_color = DISC_COLORS.get(disc_primary, "#0052FF")

    name = persona.get("name", "?")
    
    # 提取首字母逻辑：如果是英文字母则大写，如果是中文则保留
    raw_initial = name[0] if name else "?"
    initial = raw_initial.upper() if ('a' <= raw_initial.lower() <= 'z') else raw_initial
    
    # 字体大小适配：中文字符视觉上更大，需要略微缩小以保持一致感
    is_cjk = any('\u4e00' <= char <= '\u9fff' for char in initial)
    avatar_font_size = "1.55rem" if is_cjk else "1.75rem"

    # Card header & Personality Summary (Premium Refined)
    personality_summary = psych.get("personality_summary", t("暂无描述")).replace("{", "{{").replace("}", "}}")
    safe_name = name.replace("{", "{{").replace("}", "}}")
    safe_occ = demo.get("occupation", t("未知")).replace("{", "{{").replace("}", "}}")
    disc_profile = psych.get("disc_profile", t("未知")).split('(')[0].strip()
    
    header_html = f'''<div class="persona-card">
<div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px;">
<div class="persona-avatar asymmetric-shape" style="background: linear-gradient(135deg, {disc_color}, {disc_color}aa); width: 64px; height: 64px; min-width: 64px; min-height: 64px; aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; font-size: {avatar_font_size}; color: white; font-family: var(--font-display); box-shadow: 0 8px 16px {disc_color}33; line-height: 1; flex-shrink: 0;">{initial}</div>
<div style="flex: 1; min-width: 0;">
                <h3 style="margin: 0; font-size: 1.35rem; color: var(--foreground); font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 6px;">{safe_name}</h3>
                <div style="margin-bottom: 8px;">
                    <span class="pill-badge" style="background: {disc_color}10; color: {disc_color}; margin: 0; font-family: var(--font-mono); font-size: 0.65rem; border: 1px solid {disc_color}20; line-height: 1; padding: 4px 8px; display: inline-block;">{disc_profile}</span>
                </div>
                <p style="margin: 0; font-size: 0.9rem; font-family: var(--font-mono); color: var(--muted-foreground); letter-spacing: 0.02em; line-height: 1.5; word-wrap: break-word;">{demo.get("age", "?")} {t("岁")} · {safe_occ}</p>
</div>
</div>

<!-- Personality Summary Box (Premium Refined) -->
<div style="background: #F9F7F2; border: 1px solid #E5E1DA; border-left: 4px solid #8B7E66; padding: 20px 24px; border-radius: 12px; margin-bottom: 28px; position: relative; overflow: hidden; box-shadow: inset 0 0 12px rgba(0,0,0,0.02);">
<div style="position: absolute; top: 12px; right: 18px; opacity: 0.1; font-size: 3.5rem; color: #8B7E66; line-height: 1; font-family: 'Times New Roman', serif; pointer-events: none;">&ldquo;</div>
<div style="font-family: var(--font-mono); font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.15em; color: #8B7E66; margin-bottom: 12px; opacity: 0.8; font-weight: 700;">{t("Personality Profile")}</div>
<p style="margin: 0; font-size: 0.95rem; line-height: 1.75; color: var(--foreground); font-style: italic; opacity: 0.9; word-wrap: break-word; word-break: break-word; position: relative; z-index: 1;">
{personality_summary}
</p>
</div>

<div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px;">'''

    # Value tags
    for val in traits.get("values", [])[:3]:
        header_html += f'<span class="pill-badge pill-badge-tag">{val}</span>'

    # Pain tags
    for frust in traits.get("frustrations", [])[:2]:
        header_html += f'<span class="pill-badge pill-badge-pain">{frust}</span>'

    header_html += "</div></div>"
    st.markdown(clean_html(header_html), unsafe_allow_html=True)

    # Radar chart (More Minimal)
    if show_radar and big5:
        categories = [t("Openness"), t("Conscientiousness"), t("Extraversion"), t("Agreeableness"), t("Neuroticism")]
        values = [
            big5.get("openness", 3),
            big5.get("conscientiousness", 3),
            big5.get("extraversion", 3),
            big5.get("agreeableness", 3),
            big5.get("neuroticism", 3),
        ]
        values_closed = values + [values[0]]
        categories_closed = categories + [categories[0]]

        fig = go.Figure(data=go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            fillcolor=f"rgba(0, 82, 255, 0.06)",
            line=dict(color="#0052FF", width=2),
            marker=dict(size=6, color="#0052FF"),
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 5], gridcolor="#F1F5F9", tickfont=dict(size=9, family="Inter")),
                angularaxis=dict(gridcolor="#F1F5F9", tickfont=dict(size=10, family="Inter", color="#94A3B8")),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=False,
            height=240,
            margin=dict(l=40, r=40, t=30, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True, key=f"radar_{persona.get('id', name)}_{key_suffix}")

    # Detailed info in expander
    with st.expander(t("View Detailed Profile"), expanded=expanded):
        st.markdown(f"#### 👤 {t('Demographics')}")
        st.markdown(f"**{t('Age')}**: {demo.get('age', '?')}")
        st.markdown(f"**{t('Occupation')}**: {demo.get('occupation', '?')}")
        st.markdown(f"**{t('Income')}**: {demo.get('income', '?')}")
        st.markdown(f"**{t('Location')}**: {demo.get('location', '?')}")
        
        st.markdown(f"#### 🧠 {t('Psychographics')}")
        st.markdown(f"**{t('Personality')}**: {psych.get('personality_summary', '?')}")
        st.markdown(f"**{t('DISC Profile')}**: {psych.get('disc_profile', '?')}")

        st.markdown(f"#### 🎯 {t('Behavior & Values')}")
        st.markdown(f"**{t('Values')}**: {', '.join(traits.get('values', []))}")
        st.markdown(f"**{t('Goals')}**: {', '.join(traits.get('goals', []))}")
        st.markdown(f"**{t('Pains/Frustrations')}**: {', '.join(traits.get('frustrations', []))}")
        st.markdown(f"**{t('Tech Adoption')}**: {traits.get('technology_adoption', '?')}")


def render_simplified_persona_card(persona: Dict):
    """
    渲染简化的 Persona 卡片，适用于定量打分列表
    """
    demo = persona.get("demographics", {})
    psych = persona.get("psychographics", {})
    disc_primary = persona.get("_disc_primary", "S")
    disc_color = DISC_COLORS.get(disc_primary, "#0052FF")
    name = persona.get("name", "?")
    
    # 统一首字母逻辑
    raw_initial = name[0] if name else "?"
    initial = raw_initial.upper() if ('a' <= raw_initial.lower() <= 'z') else raw_initial
    is_cjk = any('\u4e00' <= char <= '\u9fff' for char in initial)
    avatar_font_size = "0.95rem" if is_cjk else "1.1rem"
    
    disc_profile = psych.get("disc_profile", t("未知"))
    
    html = f'''
    <div class="scoring-card-header" style="border: 1px solid var(--border); border-radius: var(--radius-xl); margin-bottom: 12px; padding: 12px; display: flex; align-items: center; gap: 12px;">
        <div class="asymmetric-shape" style="background: linear-gradient(135deg, {disc_color}, {disc_color}aa); width: 40px; height: 40px; min-width: 40px; min-height: 40px; aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; font-size: {avatar_font_size}; color: white; font-family: var(--font-display); flex-shrink: 0; line-height: 1;">{initial}</div>
        <div style="flex: 1; min-width: 0;">
            <div style="font-weight: 600; font-size: 1rem; color: var(--foreground); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px;">{name}</div>
            <div style="margin-bottom: 4px;"><span style="background: {disc_color}10; color: {disc_color}; font-family: var(--font-mono); font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; border: 1px solid {disc_color}20; display: inline-block;">{disc_profile}</span></div>
            <div style="font-size: 0.75rem; color: var(--muted-foreground); line-height: 1.4; word-wrap: break-word;">
                {demo.get("age", "?")} {t("岁")} · {demo.get("occupation", t("未知"))}
            </div>
        </div>
    </div>
    '''
    st.markdown(clean_html(html), unsafe_allow_html=True)


def render_scoring_persona_card(persona: Dict, content: str = "", is_loading: bool = False, scores: Dict = None):
    """
    渲染正在打分的 Persona 卡片，支持流式内容与打分结果
    """
    demo = persona.get("demographics", {})
    psych = persona.get("psychographics", {})
    disc_primary = persona.get("_disc_primary", "S")
    disc_color = DISC_COLORS.get(disc_primary, "#0052FF")
    name = persona.get("name", "?")
    
    # Escape fields
    safe_name = _html.escape(name)
    safe_role = _html.escape(demo.get("occupation", demo.get("role", "?")))
    safe_age = _html.escape(str(demo.get("age", "?")))
    safe_content = _html.escape(content if content else "").replace("$", "&#36;")
    
    # Status Pill
    status_html = ""
    if is_loading:
        status_html = f'<div class="scoring-status-pill" style="margin-left: 10px; display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; background: #EEF2FF; border-radius: 20px; border: 1px solid #E0E7FF;"><div class="scoring-status-dot"></div><span style="font-size: 0.75rem; font-weight: 600; color: #4F46E5;">{t("打分中")}</span></div>'

    # Scores HTML
    scores_html = ""
    if scores:
        items_html = ""
        for dim, val in scores.items():
            if dim in ["ID", "姓名", "Name", "职业", "Role", "年龄", "Age", "DISC"]:
                continue
            try:
                val_num = float(val)
                val_int = int(round(val_num))
                stars_svg = "".join([f'<svg width="14" height="14" viewBox="0 0 24 24" fill="{"#F59E0B" if i < val_int else "#E2E8F0"}" style="margin-right: 2px;"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>' for i in range(5)])
                items_html += f'<div style="background: white; padding: 8px 14px; border-radius: 10px; border: 1px solid var(--border); font-size: 0.8rem; box-shadow: 0 2px 4px rgba(0,0,0,0.02); display: flex; align-items: center; gap: 10px;"><span style="color: var(--muted-foreground); font-weight: 500;">{t(dim)}</span><div style="display: flex; align-items: center;">{stars_svg}</div><span style="font-weight: 700; color: var(--foreground); min-width: 14px; text-align: center;">{val_int}</span></div>'
            except: continue
        if items_html:
            scores_html = f'<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 24px; padding-top: 20px; border-top: 1px dashed var(--border);">{items_html}</div>'
    
    # Avg Score
    avg_score_html = ""
    if scores:
        vals = []
        for k, v in scores.items():
            if k not in ["ID", "姓名", "Name", "职业", "Role", "年龄", "Age", "DISC"]:
                try: vals.append(float(v))
                except: continue
        if vals:
            avg = sum(vals) / len(vals)
            avg_score_html = f'<div style="background: var(--accent); color: white; padding: 2px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 800; display: flex; align-items: center; gap: 4px; box-shadow: 0 4px 10px var(--accent-30);"><span>★</span><span>{avg:.1f}</span></div>'

    # Body Content
    body_content = f'<div style="color: var(--muted-foreground); opacity: 0.5; font-style: italic; font-size: 0.9rem;">{t("准备中...")}</div>'
    if safe_content:
        body_content = f'<div style="white-space: pre-wrap; line-height: 1.7; color: var(--foreground); opacity: 0.9;">{safe_content}</div>'

    # 统一首字母逻辑
    raw_initial = name[0] if name else "?"
    initial = raw_initial.upper() if ('a' <= raw_initial.lower() <= 'z') else raw_initial
    is_cjk = any('\u4e00' <= char <= '\u9fff' for char in initial)
    avatar_font_size = "1.05rem" if is_cjk else "1.2rem"

    # 使用列表构建 HTML，最后用 clean_html 处理
    html_parts = [
        f'<div class="scoring-card" style="margin-bottom: 24px; border-radius: 16px; overflow: hidden; background: white; border: 1px solid var(--border); transition: all 0.3s ease; box-shadow: var(--shadow-sm);">',
        f'<div class="scoring-card-header" style="background: #F8FAFC; padding: 20px 28px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">',
        f'<div style="display: flex; align-items: center; gap: 16px;">',
        f'<div class="asymmetric-shape" style="width: 48px; height: 48px; min-width: 48px; min-height: 48px; aspect-ratio: 1/1; background: {disc_color}; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: {avatar_font_size}; line-height: 1; font-family: var(--font-display); flex-shrink: 0;">{initial}</div>',
        f'<div style="min-width: 0;">',
        f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">',
        f'<span style="font-weight: 700; font-size: 1.1rem; color: var(--foreground); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 1; min-width: 0; max-width: 140px;">{safe_name}</span>',
        f'{avg_score_html}{status_html}',
        f'</div>',
        f'<div style="margin-bottom: 6px;"><span class="pill-badge" style="background: {disc_color}20; color: {disc_color}; border: 1px solid {disc_color}40; font-size: 0.65rem; font-weight: 600; padding: 1px 6px; border-radius: 4px; display: inline-block;">{psych.get("disc_profile", "N/A")}</span></div>',
        f'<div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.4; word-wrap: break-word;">{safe_age} {t("岁")}, {safe_role}</div>',
        f'</div>',
        f'</div>',
        f'</div>',
        f'<div class="scoring-card-body" style="background: #FDFDFD; padding: 28px;">',
        f'{body_content}{scores_html}',
        f'</div>',
        f'</div>'
    ]
    
    st.markdown(clean_html("".join(html_parts)), unsafe_allow_html=True)



def get_chat_bubble_html(speaker: str, content: str, persona: Dict = None, msg_type: str = "agent") -> str:
    """
    获取对话气泡的 HTML 内容
    """
    if msg_type == "moderator":
        return f'''
        <div class="chat-bubble chat-bubble-moderator">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-family: var(--font-mono); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em;">
                <span>🎙️</span> {t("系统提示 / 主持人")}
            </div>
            <div style="font-size: 1.05rem; font-style: italic; line-height: 1.6;">{content}</div>
        </div>
        '''
    else:
        disc_primary = persona.get("_disc_primary", "S") if persona else "S"
        disc_color = DISC_COLORS.get(disc_primary, "#0052FF")
        
        # Behavior tag
        behavior_tag = ""
        if persona:
            big5 = persona.get("psychographics", {}).get("big_five", {})
            agreeableness = big5.get("agreeableness", 3)
            behavior_tag = t("直言") if agreeableness <= 2 else (t("温和") if agreeableness >= 4 else t("中立"))

        return f'''
        <div class="chat-bubble" style="border-left: 5px solid {disc_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div class="asymmetric-shape" style="width: 32px; height: 32px; min-width: 32px; min-height: 32px; aspect-ratio: 1/1; background: {disc_color}; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: {'0.7rem' if any('\u4e00' <= char <= '\u9fff' for char in speaker[0]) else '0.8rem'}; line-height: 1; flex-shrink: 0;">{speaker[0].upper() if ('a' <= speaker[0].lower() <= 'z') else speaker[0]}</div>
                    <span style="font-weight: 700; color: var(--foreground); font-size: 1rem;">{speaker}</span>
                </div>
                <span style="font-family: var(--font-mono); font-size: 0.7rem; text-transform: uppercase; color: {disc_color}; background: {disc_color}12; padding: 4px 10px; border-radius: 6px; font-weight: 600;">{disc_primary} · {behavior_tag}</span>
            </div>
            <div style="font-size: 1.05rem; color: var(--foreground); line-height: 1.7; opacity: 0.9;">{content}</div>
        </div>
        '''


def render_chat_bubble(speaker: str, content: str, persona: Dict = None, msg_type: str = "agent"):
    """
    渲染对话气泡 (Minimalist Style)
    """
    st.markdown(clean_html(get_chat_bubble_html(speaker, content, persona, msg_type)), unsafe_allow_html=True)


def render_stat_card(value: str, label: str):
    """渲染统计卡片"""
    html = f'''
    <div class="stat-card featured-card-outer">
        <div class="featured-card-inner" style="padding: 40px 24px;">
            <div class="stat-value">{value}</div>
            <div class="stat-label">{t(label)}</div>
        </div>
    </div>
    '''
    st.markdown(clean_html(html), unsafe_allow_html=True)


def render_question_card(question: str, index: int, editable: bool = True):
    """渲染问题卡片 (Minimalist)"""
    with st.container():
        st.markdown(clean_html(f'''
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <div class="section-label-dot" style="animation: none; width: 6px; height: 6px;"></div>
            <div class="display-font" style="font-size: 0.9rem; color: var(--accent);">{t("问题")} {index + 1}</div>
        </div>
        '''), unsafe_allow_html=True)
        col1, col2, col3 = st.columns([0.82, 0.09, 0.09])
        with col1:
            if editable:
                res = st.text_area(f"q_input_{index}", value=question, key=f"q_{index}", label_visibility="collapsed", height=70)
            else:
                st.markdown(f'<div class="chat-bubble" style="margin-bottom: 12px; padding: 20px; font-weight: 500;">{question}</div>', unsafe_allow_html=True)
                res = question
        with col2:
            if editable: st.button("✎", key=f"edit_{index}", help=t("编辑"), use_container_width=True)
        with col3:
            if editable: st.button("✕", key=f"del_{index}", help=t("删除"), use_container_width=True)
        return res
