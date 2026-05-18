"""
SynthResearch - CSS 样式注入模块
Minimalist Modern Design System
Inspired by Clarity, Bold Detail, and Premium Aesthetics
"""

import streamlit as st

# ============================================================
# Design Tokens (Minimalist Modern)
# ============================================================
ACCENT_BLUE = "#0052FF"         # Electric Blue
ACCENT_LIGHT = "#4D7CFF"        # Sky Blue
BG_PRIMARY = "#FAFAFA"          # Warmer Off-White
BG_SECONDARY = "#F1F5F9"        # Slate-100 (Muted)
FG_PRIMARY = "#0F172A"          # Slate-900 (Deep Text)
FG_BODY = "#334155"             # Slate-700
FG_MUTED = "#64748B"            # Slate-500
BORDER_COLOR = "#E2E8F0"        # Slate-200
SURFACE_CARD = "#FFFFFF"        # Pure White

DISC_COLORS = {
    "D": "#EF4444", # Red
    "I": "#F59E0B", # Amber
    "S": "#10B981", # Emerald
    "C": "#0052FF", # Blue (Matching Accent)
}

MAIN_CSS = """
<style>
/* ========================================
   SynthResearch — Minimalist Modern
   Clarity through structure, character through bold detail.
   ======================================== */

@import url('https://fonts.googleapis.com/css2?family=Calistoga&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ---- Variables ---- */
:root {
    --accent: #0052FF;
    --accent-light: #4D7CFF;
    --background: #FAFAFA;
    --foreground: #0F172A;
    --muted: #F1F5F9;
    --muted-foreground: #64748B;
    --border: #E2E8F0;
    --card: #FFFFFF;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
    --shadow-lg: 0 10px 15px rgba(0,0,0,0.08);
    --shadow-xl: 0 20px 25px rgba(0,0,0,0.1);
    --shadow-accent: 0 4px 14px rgba(0, 82, 255, 0.25);
    --shadow-accent-lg: 0 8px 24px rgba(0, 82, 255, 0.35);
    --font-display: 'Calistoga', serif;
    --font-sans: 'Inter', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    --radius-xl: 12px;
    --radius-2xl: 16px;
}

/* ---- Keyframe Animations ---- */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(28px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulseDot {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.3); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
}

@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
    100% { transform: translateY(0px); }
}

/* ---- Global Style ---- */
.stApp {
    background-color: var(--background);
    color: var(--foreground);
    font-family: var(--font-sans);
}

/* Hide Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {
    background: rgba(250, 250, 250, 0.8) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
}

/* ---- Layout ---- */
.block-container {
    max-width: 1200px; 
    padding-top: 5rem;
    padding-bottom: 5rem;
}

/* ---- Typography ---- */
h1, h2, .display-font {
    font-family: var(--font-display) !important;
    font-weight: 400 !important;
    color: var(--foreground);
}

h1 {
    font-size: 3.5rem !important;
    line-height: 1.05 !important;
    margin-bottom: 1.5rem !important;
    letter-spacing: -0.02em;
}

h2 {
    font-size: 2.25rem !important;
    margin-bottom: 1.25rem !important;
}

h3, .stMarkdown h3 {
    font-family: var(--font-sans) !important;
    font-weight: 600 !important;
    font-size: 1.25rem !important;
    color: var(--foreground);
    letter-spacing: -0.01em;
}

.gradient-text {
    background: linear-gradient(to right, var(--accent), var(--accent-light));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
    position: relative;
}

.gradient-underline-wrap {
    position: relative;
    display: inline-block;
}

.gradient-underline-wrap::after {
    content: "";
    position: absolute;
    bottom: -4px;
    left: 0;
    height: 8px;
    width: 100%;
    border-radius: 2px;
    background: linear-gradient(to right, rgba(0, 82, 255, 0.15), rgba(77, 124, 255, 0.1));
    z-index: -1;
}

p, li, .stMarkdown p {
    color: var(--muted-foreground);
    font-size: 1.05rem;
    line-height: 1.75;
}

/* ---- Sidebar (Modern Slate) ---- */
section[data-testid="stSidebar"] {
    background-color: var(--foreground) !important;
    border-right: 1px solid rgba(255,255,255,0.05);
}

section[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
}

section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}

/* ---- Streamlit Buttons ---- */
div[data-testid="stButton"] > button, div[data-testid="stPopover"] > button {
    background: linear-gradient(to right, var(--accent), var(--accent-light)) !important;
    border: none !important;
    border-radius: var(--radius-xl) !important;
    padding: 14px 32px;
    font-weight: 600;
    color: #FFFFFF !important; /* 强制白色文字 */
    text-shadow: 0 1px 2px rgba(0,0,0,0.1); /* 增加微弱投影提升清晰度 */
    font-size: 1rem;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: var(--shadow-sm);
    height: auto;
}

/* Ensure text inside buttons (which Streamlit wraps in <p>) is readable */
div[data-testid="stButton"] > button p, div[data-testid="stPopover"] > button p {
    color: inherit !important;
}


div[data-testid="stButton"] > button:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-accent-lg);
    filter: brightness(1.1);
    color: #FFFFFF !important;
}

div[data-testid="stButton"] > button:active {
    transform: scale(0.98);
}

/* Secondary Buttons */
div[data-testid="stButton"] > button[kind="secondary"] {
    background: var(--card) !important;
    color: var(--foreground) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm);
}

div[data-testid="stButton"] > button[kind="secondary"]:hover {
    background: var(--muted) !important;
    border-color: rgba(0, 82, 255, 0.3) !important;
    color: var(--accent) !important;
    box-shadow: var(--shadow-md);
}

/* ---- Inputs ---- */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background-color: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-xl) !important;
    color: var(--foreground) !important;
    padding: 12px 16px !important;
    font-size: 1rem !important;
    transition: all 0.2s ease;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(0, 82, 255, 0.1) !important;
}

/* ---- Cards & Custom Elements ---- */
.project-card, .persona-card, .stat-card, .path-card, .chat-bubble, .asymmetric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-2xl);
    padding: 32px;
    box-shadow: var(--shadow-md);
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    animation: fadeInUp 0.7s ease-out both;
}

/* Fix popover text readability */
div[data-testid="stPopoverContent"] p {
    color: var(--foreground) !important;
    font-weight: 500;
}

.project-card:hover, .persona-card:hover, .path-card:hover, .asymmetric-card:hover {
    transform: translateY(-8px);
    box-shadow: var(--shadow-xl);
    border-color: var(--accent);
}

.path-card {
    height: 420px;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48px 32px !important;
    margin-bottom: 40px; /* 增加与下方按钮的距离 */
}

.path-card .path-icon {
    height: 100px; /* 固定高度确保对齐 */
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    font-size: 4rem;
    filter: drop-shadow(0 10px 15px rgba(0, 82, 255, 0.15));
}

.path-card h2 {
    height: 70px; /* 固定高度确保标题行数不同时依然对齐 */
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 0 16px 0 !important;
    text-align: center;
    width: 100%;
    font-size: 1.75rem !important;
}

.path-card .path-desc {
    flex-grow: 1; /* 占据剩余空间 */
    display: flex;
    align-items: flex-start;
    justify-content: center;
    text-align: center;
    width: 100%;
}

.path-card .path-desc p {
    margin: 0 !important;
    padding: 0 10px !important;
    font-size: 1.05rem;
    line-height: 1.6;
    color: var(--muted-foreground);
}

/* Asymmetric Shape */
.asymmetric-shape {
    border-top-left-radius: 4rem !important;
    border-bottom-right-radius: 4rem !important;
}

/* Featured Card (Gradient Border Hack) */
.featured-card-outer {
    background: linear-gradient(135deg, var(--accent), var(--accent-light));
    padding: 2px;
    border-radius: var(--radius-2xl);
}
.featured-card-inner {
    background: var(--card);
    border-radius: calc(var(--radius-2xl) - 2px);
    height: 100%;
    width: 100%;
}

/* Section Label Badge */
.section-label {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    background: rgba(0, 82, 255, 0.05);
    border: 1px solid rgba(0, 82, 255, 0.2);
    border-radius: 99px;
    padding: 8px 20px;
    margin-bottom: 1.5rem;
}

.section-label-dot {
    width: 8px;
    height: 8px;
    background: var(--accent);
    border-radius: 50%;
    animation: pulseDot 2s infinite;
}

.section-label-text {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--accent);
    font-weight: 500;
}

/* ---- Pill Badges ---- */
.pill-badge {
    display: inline-flex;
    align-items: center;
    padding: 6px 14px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 4px 8px 4px 0;
    letter-spacing: 0.02em;
}

.pill-badge-tag {
    background: var(--muted);
    color: var(--muted-foreground);
    border: 1px solid var(--border);
}

.pill-badge-pain {
    background: #FEF2F2;
    color: #EF4444;
    border: 1px solid #FEE2E2;
}

.pill-badge-accent {
    background: linear-gradient(to right, var(--accent), var(--accent-light));
    color: white;
}

/* ---- Inverted Section Style ---- */
.inverted-section {
    background-color: var(--foreground);
    color: #FFFFFF;
    padding: 80px 48px;
    border-radius: 32px;
    margin: 48px 0;
    position: relative;
    overflow: hidden;
    background-image: radial-gradient(circle, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 32px 32px;
    box-shadow: var(--shadow-xl);
}

.inverted-section::before {
    content: "";
    position: absolute;
    top: -150px;
    right: -150px;
    width: 300px;
    height: 300px;
    background: var(--accent);
    filter: blur(150px);
    opacity: 0.08;
    border-radius: 50%;
}

.inverted-section h2, .inverted-section p {
    color: #FFFFFF !important;
}

/* ---- Stat Card Enhanced ---- */
.stat-card {
    text-align: center;
    padding: 40px 24px;
}
.stat-value {
    font-family: var(--font-display);
    font-size: 4rem;
    line-height: 1;
    background: linear-gradient(to bottom, var(--accent), var(--accent-light));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 12px;
}
.stat-label {
    font-family: var(--font-mono);
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--muted-foreground);
}

/* ---- Chat Bubble (Minimal) ---- */
.chat-bubble {
    border: 1px solid var(--border);
    background: #FFFFFF;
    margin-bottom: 24px;
    border-radius: 16px 16px 16px 0;
    padding: 24px;
    position: relative;
}

.chat-bubble-moderator {
    background: var(--muted);
    border-radius: 16px 16px 0 16px;
    border-color: var(--border);
    border-left: 4px solid var(--muted-foreground);
}

/* ---- Progress Indicators ---- */
.workflow-steps {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    margin-bottom: 48px;
}
.workflow-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--border);
    transition: all 0.3s ease;
}
.workflow-dot-active {
    background: var(--accent);
    box-shadow: 0 0 16px rgba(0, 82, 255, 0.5);
    transform: scale(1.3);
}
.workflow-dot-done {
    background: var(--accent-light);
}

/* Floating Animation Utility */
.animate-float {
    animation: float 5s ease-in-out infinite;
}

/* ---- Scoring Card (Quantitative) ---- */
.scoring-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-2xl);
    overflow: hidden;
    margin-bottom: 24px;
    box-shadow: var(--shadow-md);
    transition: all 0.3s ease;
}

.scoring-card:hover {
    box-shadow: var(--shadow-lg);
    border-color: var(--accent);
}

.scoring-card-header {
    background: #FFFFFF;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 16px;
}

.scoring-card-body {
    background: #F8FAFC; /* Light Slate */
    padding: 24px;
    font-size: 0.925rem;
    line-height: 1.6;
    color: var(--foreground);
    min-height: 100px;
}

.scoring-status-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--accent);
}

.scoring-status-dot {
    width: 6px;
    height: 6px;
    background: var(--accent);
    border-radius: 50%;
}

@keyframes pulseDot {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5); opacity: 0.5; }
    100% { transform: scale(1); opacity: 1; }
}

@keyframes pulseStatus {
    0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(245, 158, 11, 0); }
    100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
}

.scoring-status-pulse {
    animation: pulseStatus 2s infinite;
}

/* Pulse Animation for Status Indicators */
@keyframes pulse-status {
    0% { opacity: 0.6; transform: scale(0.98); }
    50% { opacity: 1; transform: scale(1); }
    100% { opacity: 0.6; transform: scale(0.98); }
}

.progress-pill {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 20px;
    background: var(--muted);
    border: 1px solid var(--border);
    font-size: 0.85rem;
    color: var(--muted-foreground);
    margin-bottom: 1rem;
}

.progress-pill.active {
    border-color: var(--accent);
    color: var(--accent);
    animation: pulse-status 2s infinite ease-in-out;
}

.thinking-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: var(--card);
    border: 1px solid var(--accent);
    border-radius: 99px;
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: 0.8rem;
    font-weight: 500;
    box-shadow: var(--shadow-accent);
    animation: pulse-status 2s infinite ease-in-out;
}

.thinking-pill::before {
    content: "";
    width: 8px;
    height: 8px;
    background: var(--accent);
    border-radius: 50%;
}

</style>
"""

def inject_css():
    """注入 Minimalist Modern 风格 CSS 样式"""
    st.markdown(MAIN_CSS, unsafe_allow_html=True)
