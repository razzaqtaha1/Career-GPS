"""Career GPS UI design system.

One stylesheet plus small reusable HTML components. Nothing here touches
business logic, the database, or the AI layer.
"""

from contextlib import contextmanager
from html import escape as esc
from uuid import uuid4

import streamlit as st


# =====================================================
# DESIGN TOKENS + STYLESHEET
# =====================================================

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Sora:wght@500;600;700&display=swap');

:root {
  --bg: #080B14;
  --bg-2: #101625;
  --card: #151D2E;
  --card-2: #1A2438;
  --input: #0D1322;
  --blue: #477BFF;
  --cyan: #22D3EE;
  --violet: #8B7CFF;
  --green: #34D399;
  --amber: #FBBF24;
  --text: #EEF2FA;
  --muted: #94A3B8;
  --faint: #64748B;
  --border: rgba(148, 163, 184, .14);
  --border-strong: rgba(71, 123, 255, .38);
  --radius: 16px;
  --display: 'Sora', 'Manrope', sans-serif;
  --body: 'Manrope', 'Segoe UI', sans-serif;
}

/* ---------- base ---------- */
.stApp { background: var(--bg); color: var(--text); }
.stApp, .stMarkdown, .stMarkdown p, .stMarkdown li, button, input, textarea,
[data-baseweb="select"], label, [data-testid="stCaptionContainer"] {
  font-family: var(--body);
}
h1, h2, h3, h4 { font-family: var(--display) !important; letter-spacing: -0.015em; color: var(--text); }
.stMarkdown p, .stMarkdown li { line-height: 1.7; }
a { color: var(--cyan); }

[data-testid="stAppViewContainer"], [data-testid="stSidebar"] { position: relative; z-index: 1; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"], #MainMenu, footer, [data-testid="stStatusWidget"] { display: none !important; }
.stMainBlockContainer, .block-container { max-width: 1180px; padding-top: 2.4rem; padding-bottom: 5rem; }

/* ---------- animated ambient background ---------- */
.stApp::before {
  content: ""; position: fixed; inset: -10%; z-index: 0; pointer-events: none;
  background:
    radial-gradient(620px 420px at 82% 0%, rgba(71, 123, 255, .17), transparent 62%),
    radial-gradient(520px 380px at 4% 100%, rgba(34, 211, 238, .09), transparent 62%),
    radial-gradient(420px 320px at 58% 62%, rgba(139, 124, 255, .07), transparent 62%);
  animation: cg-drift 30s ease-in-out infinite alternate;
}
.stApp::after {
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image:
    linear-gradient(rgba(148, 163, 184, .045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, .045) 1px, transparent 1px);
  background-size: 56px 56px;
  -webkit-mask-image: radial-gradient(ellipse 80% 55% at 50% 0%, #000, transparent 75%);
  mask-image: radial-gradient(ellipse 80% 55% at 50% 0%, #000, transparent 75%);
}

/* ---------- keyframes ---------- */
@keyframes cg-drift { from { transform: translate3d(0, 0, 0) scale(1); } to { transform: translate3d(-2.5%, 3%, 0) scale(1.06); } }
@keyframes cg-rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@keyframes cg-fade { from { opacity: 0; } to { opacity: 1; } }
@keyframes cg-grow { from { width: 0; } }
@keyframes cg-pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(34, 211, 238, .45); } 50% { box-shadow: 0 0 0 7px rgba(34, 211, 238, 0); } }
@keyframes cg-bounce { 0%, 80%, 100% { transform: translateY(0); opacity: .35; } 40% { transform: translateY(-5px); opacity: 1; } }
@keyframes cg-spin { to { transform: rotate(360deg); } }
@keyframes cg-shimmer { from { background-position: -200% 0; } to { background-position: 200% 0; } }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0C1121 0%, #080B14 100%);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 1.4rem; }
.cg-brand { display: flex; align-items: center; gap: .75rem; padding: .2rem .4rem 1.2rem; }
.cg-logo {
  width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; flex: none;
  background: linear-gradient(135deg, var(--blue), var(--cyan));
  box-shadow: 0 6px 20px rgba(71, 123, 255, .4);
}
.cg-brand b { display: block; font: 700 1.08rem var(--display); color: var(--text); letter-spacing: -.01em; }
.cg-brand span { font-size: .76rem; color: var(--muted); }

[data-testid="stSidebar"] [data-testid="stRadio"], [data-testid="stSidebar"] [data-testid="stElementContainer"]:has([data-testid="stRadio"]) { width: 100% !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] { gap: .2rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label {
  width: 100%; padding: .62rem .85rem; border-radius: 12px; cursor: pointer;
  border: 1px solid transparent; transition: background .2s ease, border-color .2s ease, transform .2s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div { width: 100%; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label { display: flex; box-sizing: border-box; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label[data-testid="stRadioOption"] > div { display: block; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label[data-testid="stRadioOption"] > div > div:first-child { display: none; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label p { color: var(--muted); font-weight: 600; font-size: .93rem; margin: 0; transition: color .2s ease; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover { background: rgba(71, 123, 255, .1); transform: translateX(3px); }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover p { color: var(--text); }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
  background: linear-gradient(90deg, rgba(71, 123, 255, .24), rgba(34, 211, 238, .07));
  border-color: rgba(71, 123, 255, .35); box-shadow: inset 3px 0 0 var(--blue);
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p { color: #fff; }
.cg-side-note {
  margin-top: .6rem; padding: .9rem 1rem; border-radius: 14px; font-size: .82rem; line-height: 1.55;
  color: var(--muted); background: rgba(71, 123, 255, .07); border: 1px solid rgba(71, 123, 255, .18);
}
.cg-side-foot { margin-top: .9rem; padding: 0 .3rem; font-size: .74rem; color: var(--faint); }

/* ---------- page header ---------- */
.cg-pagehead { display: flex; align-items: center; gap: 1.05rem; margin: 0 0 1.7rem; animation: cg-rise .55s ease both; }
.cg-ico {
  width: 52px; height: 52px; border-radius: 16px; display: grid; place-items: center; flex: none; font-size: 1.5rem;
  background: linear-gradient(135deg, rgba(71, 123, 255, .26), rgba(34, 211, 238, .1));
  border: 1px solid rgba(71, 123, 255, .38); box-shadow: 0 0 28px rgba(71, 123, 255, .16);
}
.cg-pagehead h1 { margin: 0; padding: 0; font-size: 1.95rem; line-height: 1.15; }
.cg-pagehead p { margin: .3rem 0 0; color: var(--muted); font-size: .98rem; max-width: 62ch; line-height: 1.55; }

/* ---------- cards ---------- */
[class*="st-key-card"] {
  background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 1.35rem 1.45rem; margin-bottom: .9rem; animation: cg-fade .5s ease both;
  box-shadow: 0 10px 34px rgba(0, 0, 0, .22);
}
[class*="st-key-card"] > [data-testid="stVerticalBlock"] { gap: .75rem; }
[class*="st-key-card_tone_good"] { border-left: 3px solid var(--green); }
[class*="st-key-card_tone_warn"] { border-left: 3px solid var(--amber); }
[class*="st-key-card_tone_info"] { border-left: 3px solid var(--blue); }
[class*="st-key-card_result"] { border-color: rgba(71, 123, 255, .3); background: linear-gradient(180deg, #172036, var(--card)); }
[class*="st-key-card_feature"] { transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease; padding: 1.15rem 1.2rem; }
[class*="st-key-card_feature"]:hover { transform: translateY(-3px); border-color: var(--border-strong); box-shadow: 0 16px 40px rgba(0, 0, 0, .35), 0 0 30px rgba(71, 123, 255, .12); }

.cg-sec { display: flex; align-items: center; gap: .6rem; margin: 0 0 .15rem; font: 600 1.08rem var(--display); color: var(--text); }
.cg-sec i { font-style: normal; font-size: 1.15rem; }
.cg-sub { margin: 0 0 .2rem; color: var(--muted); font-size: .9rem; line-height: 1.55; }
.cg-h2 { margin: 1.7rem 0 .9rem; font: 600 1.25rem var(--display); color: var(--text); }

/* ---------- hero ---------- */
.cg-hero {
  position: relative; overflow: hidden; border-radius: 22px; padding: 2.3rem 2.4rem; margin-bottom: .9rem;
  background: linear-gradient(135deg, rgba(71, 123, 255, .22) 0%, rgba(21, 29, 46, .95) 48%, rgba(34, 211, 238, .09) 100%);
  border: 1px solid rgba(71, 123, 255, .32); box-shadow: 0 20px 60px rgba(0, 0, 0, .35), 0 0 60px rgba(71, 123, 255, .1);
  animation: cg-rise .6s ease both;
}
.cg-hero::after {
  content: ""; position: absolute; width: 340px; height: 340px; right: -90px; top: -120px; border-radius: 50%;
  background: radial-gradient(circle, rgba(34, 211, 238, .22), transparent 68%); pointer-events: none;
}
.cg-hero .tag {
  display: inline-flex; align-items: center; gap: .5rem; padding: .32rem .8rem; border-radius: 999px;
  font-size: .78rem; font-weight: 600; color: var(--cyan); background: rgba(34, 211, 238, .09); border: 1px solid rgba(34, 211, 238, .25);
}
.cg-hero .tag::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); animation: cg-pulse 2.4s infinite; }
.cg-hero h1 { margin: 1rem 0 .55rem; font-size: 2.45rem; line-height: 1.12; position: relative; z-index: 1; }
.cg-hero p { margin: 0; color: #B8C4D9; font-size: 1.02rem; max-width: 58ch; line-height: 1.65; position: relative; z-index: 1; }
.cg-grad { background: linear-gradient(90deg, var(--blue), var(--cyan)); -webkit-background-clip: text; background-clip: text; color: transparent; }

/* ---------- stat cards ---------- */
.cg-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: .9rem; margin: .9rem 0; }
.cg-stat {
  padding: 1.15rem 1.25rem; border-radius: var(--radius); background: var(--card); border: 1px solid var(--border);
  animation: cg-rise .55s ease both; transition: transform .25s ease, border-color .25s ease;
}
.cg-stat:nth-child(2) { animation-delay: .07s; } .cg-stat:nth-child(3) { animation-delay: .14s; } .cg-stat:nth-child(4) { animation-delay: .21s; }
.cg-stat:hover { transform: translateY(-3px); border-color: var(--border-strong); }
.cg-stat .top { display: flex; align-items: center; justify-content: space-between; color: var(--muted); font-size: .85rem; font-weight: 600; }
.cg-stat .top span:last-child { font-size: 1.25rem; }
.cg-stat .val { margin-top: .55rem; font: 700 1.9rem var(--display); color: var(--text); letter-spacing: -.02em; }
.cg-stat .hint { margin-top: .15rem; font-size: .8rem; color: var(--faint); }

/* ---------- progress / score bars ---------- */
.cg-bar { margin: .7rem 0; }
.cg-bar .row { display: flex; justify-content: space-between; font-size: .88rem; color: var(--muted); margin-bottom: .38rem; font-weight: 600; }
.cg-bar .row b { color: var(--text); font-weight: 700; }
.cg-bar .track { height: 8px; border-radius: 99px; background: rgba(148, 163, 184, .13); overflow: hidden; }
.cg-bar .fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, var(--blue), var(--cyan)); animation: cg-grow 1.1s cubic-bezier(.2, .8, .2, 1) both; box-shadow: 0 0 14px rgba(34, 211, 238, .35); }
.cg-check { display: flex; align-items: center; gap: .6rem; padding: .28rem 0; font-size: .9rem; color: var(--muted); }
.cg-check .dot { width: 18px; height: 18px; border-radius: 50%; display: grid; place-items: center; font-size: .68rem; flex: none; border: 1px solid var(--border); }
.cg-check.done { color: var(--text); }
.cg-check.done .dot { background: rgba(52, 211, 153, .18); border-color: rgba(52, 211, 153, .5); color: var(--green); }

/* ---------- activity ---------- */
.cg-act { display: flex; align-items: center; gap: .9rem; padding: .75rem 0; border-bottom: 1px solid var(--border); }
.cg-act:last-child { border-bottom: 0; }
.cg-act .ic { width: 38px; height: 38px; border-radius: 11px; display: grid; place-items: center; background: rgba(71, 123, 255, .12); flex: none; }
.cg-act b { display: block; font-size: .93rem; color: var(--text); }
.cg-act span { font-size: .8rem; color: var(--faint); }

/* ---------- badges / avatar / empty ---------- */
.cg-badges { display: flex; flex-wrap: wrap; gap: .5rem; }
.cg-badge {
  padding: .4rem .85rem; border-radius: 999px; font-size: .85rem; font-weight: 600; color: #CFE0FF;
  background: rgba(71, 123, 255, .13); border: 1px solid rgba(71, 123, 255, .3); transition: transform .2s ease, background .2s ease;
}
.cg-badge:hover { transform: translateY(-2px); background: rgba(71, 123, 255, .22); }
.cg-badge.alt { color: #BDF3FB; background: rgba(34, 211, 238, .1); border-color: rgba(34, 211, 238, .28); }
.cg-profile { display: flex; align-items: center; gap: 1.3rem; }
.cg-avatar {
  width: 78px; height: 78px; border-radius: 22px; display: grid; place-items: center; flex: none; color: #fff;
  font: 700 1.7rem var(--display); background: linear-gradient(135deg, var(--blue), var(--violet) 60%, var(--cyan));
  box-shadow: 0 10px 30px rgba(71, 123, 255, .35);
}
.cg-profile h2 { margin: 0; font-size: 1.7rem; }
.cg-profile p { margin: .25rem 0 0; color: var(--muted); }
.cg-empty { text-align: center; padding: 2.4rem 1rem; color: var(--muted); }
.cg-empty .big { font-size: 2.3rem; margin-bottom: .4rem; }
.cg-empty b { display: block; color: var(--text); font: 600 1.05rem var(--display); margin-bottom: .3rem; }

/* ---------- interview ---------- */
.cg-steps { display: flex; gap: .45rem; margin: .2rem 0 .9rem; }
.cg-steps span { flex: 1; height: 6px; border-radius: 99px; background: rgba(148, 163, 184, .15); }
.cg-steps span.on { background: linear-gradient(90deg, var(--blue), var(--cyan)); box-shadow: 0 0 10px rgba(34, 211, 238, .3); }
.cg-question {
  padding: 1.2rem 1.35rem; border-radius: 14px; background: rgba(71, 123, 255, .09);
  border: 1px solid rgba(71, 123, 255, .3); color: var(--text); font-size: 1.05rem; line-height: 1.65;
}
.cg-total { display: flex; align-items: baseline; gap: .5rem; margin: .2rem 0 .6rem; }
.cg-total b { font: 700 2.5rem var(--display); }
.cg-total span { color: var(--muted); font-weight: 600; }

/* ---------- chat ---------- */
.cg-welcome { text-align: center; padding: 2.2rem 1rem 1.2rem; animation: cg-rise .6s ease both; }
.cg-orb {
  width: 76px; height: 76px; margin: 0 auto 1.2rem; border-radius: 24px; display: grid; place-items: center;
  background: linear-gradient(135deg, var(--blue), var(--cyan)); box-shadow: 0 0 0 8px rgba(71, 123, 255, .1), 0 14px 44px rgba(71, 123, 255, .5);
}
.cg-welcome h2 { font-size: 1.85rem; margin: 0 0 .5rem; }
.cg-welcome p { color: var(--muted); max-width: 52ch; margin: 0 auto; line-height: 1.65; }
.cg-chip-label { text-align: center; color: var(--faint); font-size: .82rem; margin: 1.3rem 0 .6rem; }

[data-testid="stChatMessage"] { background: transparent; padding: .45rem 0; gap: .85rem; animation: cg-rise .4s ease both; }
[data-testid="stChatMessageContent"] {
  background: var(--card); border: 1px solid var(--border); border-radius: 5px 20px 20px 20px; padding: .95rem 1.2rem; max-width: 86%;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { flex-direction: row-reverse; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  background: linear-gradient(135deg, rgba(71, 123, 255, .9), rgba(54, 98, 220, .9)); border-color: rgba(120, 160, 255, .5);
  border-radius: 20px 5px 20px 20px; color: #fff; max-width: 74%; box-shadow: 0 10px 28px rgba(71, 123, 255, .25);
}
[data-testid="stChatMessageAvatarAssistant"] { background: linear-gradient(135deg, var(--blue), var(--cyan)) !important; color: #fff !important; }
[data-testid="stChatMessageAvatarUser"] { background: var(--card-2) !important; }
[data-testid="stChatMessage"] { justify-content: flex-start; }
[data-testid="stChatMessageContent"] { flex: 0 1 auto !important; width: fit-content; min-width: 0; }
[data-testid="stChatMessageContent"] { margin: 0 auto 0 0 !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] { margin: 0 0 0 auto !important; }
[data-testid="stChatMessageContent"] h1, [data-testid="stChatMessageContent"] h2 { font-size: 1.25rem; margin: .2rem 0 .5rem; padding: 0; }
[data-testid="stChatMessageContent"] h3, [data-testid="stChatMessageContent"] h4 { font-size: 1.05rem; margin: .2rem 0 .4rem; padding: 0; }

.cg-typing { display: inline-flex; align-items: center; gap: .45rem; padding: .35rem 0; color: var(--muted); font-size: .9rem; }
.cg-typing i { width: 8px; height: 8px; border-radius: 50%; background: var(--cyan); animation: cg-bounce 1.2s infinite; }
.cg-typing i:nth-child(2) { animation-delay: .15s; } .cg-typing i:nth-child(3) { animation-delay: .3s; }

[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background: transparent !important; }
[data-testid="stChatInput"] { background: var(--card); border: 1px solid var(--border); border-radius: 18px; box-shadow: 0 12px 40px rgba(0, 0, 0, .4); transition: border-color .2s, box-shadow .2s; }
[data-testid="stChatInput"]:focus-within { border-color: var(--blue); box-shadow: 0 0 0 3px rgba(71, 123, 255, .2), 0 12px 40px rgba(0, 0, 0, .4); }
[data-testid="stChatInput"] textarea { background: transparent; color: var(--text); }

/* ---------- AI loader ---------- */
.cg-loader { display: flex; align-items: center; gap: 1rem; padding: 1.1rem 1.3rem; border-radius: var(--radius); background: var(--card); border: 1px solid rgba(71, 123, 255, .3); margin: .6rem 0; overflow: hidden; position: relative; }
.cg-loader .ring { width: 34px; height: 34px; border-radius: 50%; flex: none; border: 3px solid rgba(71, 123, 255, .2); border-top-color: var(--cyan); border-right-color: var(--blue); animation: cg-spin .9s linear infinite; }
.cg-loader b { display: block; font-size: .95rem; color: var(--text); }
.cg-loader span { font-size: .8rem; color: var(--faint); }
.cg-loader::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 2px; background: linear-gradient(90deg, transparent, var(--cyan), transparent); background-size: 200% 100%; animation: cg-shimmer 1.6s linear infinite; }

/* ---------- native widgets ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  border-radius: 12px; font-weight: 600; padding: .55rem 1.1rem; transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease, background .2s ease;
  background: var(--card-2); border: 1px solid var(--border); color: var(--text);
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover { transform: translateY(-2px); border-color: var(--border-strong); color: #fff; box-shadow: 0 8px 22px rgba(0, 0, 0, .3); }
.stButton > button:active, .stFormSubmitButton > button:active { transform: translateY(0); }
button[kind="primary"], button[kind="primaryFormSubmit"] {
  background: linear-gradient(135deg, #477BFF, #2F9BF2 70%, #22D3EE) !important; border: 0 !important; color: #fff !important;
  box-shadow: 0 8px 24px rgba(71, 123, 255, .34);
}
button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover { box-shadow: 0 12px 34px rgba(71, 123, 255, .55), 0 0 0 1px rgba(34, 211, 238, .4); }
button[kind="primary"]:disabled { opacity: .45; box-shadow: none; }
button:focus-visible, [data-baseweb="radio"] input:focus-visible + div { outline: 2px solid var(--cyan) !important; outline-offset: 2px; }

[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
  background: var(--input) !important; border-radius: 12px !important; border: 1px solid var(--border) !important; transition: border-color .2s, box-shadow .2s;
}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea { background: transparent !important; color: var(--text); }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"] > div:focus-within {
  border-color: var(--blue) !important; box-shadow: 0 0 0 3px rgba(71, 123, 255, .18);
}
[data-testid="stWidgetLabel"] p, label[data-testid="stWidgetLabel"] { color: #C4CFE2; font-weight: 600; font-size: .9rem; }

[data-testid="stFileUploaderDropzone"] { background: var(--input); border: 1.5px dashed rgba(71, 123, 255, .4); border-radius: 14px; transition: border-color .2s, background .2s; }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--cyan); background: rgba(34, 211, 238, .04); }

[data-testid="stForm"] { background: transparent; border: 1px solid var(--border); border-radius: var(--radius); padding: 1.3rem; background: rgba(21, 29, 46, .6); }
[data-testid="stExpander"] { background: var(--card); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; margin-bottom: .55rem; transition: border-color .2s; }
[data-testid="stExpander"]:hover { border-color: var(--border-strong); }
[data-testid="stExpander"] summary { padding: .7rem 1rem; font-weight: 600; }
[data-testid="stAlert"] { border-radius: 14px; border: 1px solid var(--border); background: rgba(21, 29, 46, .85); }
[data-testid="stProgress"] > div > div { background: rgba(148, 163, 184, .15); height: 8px; border-radius: 99px; }
[data-testid="stProgress"] > div > div > div { background: linear-gradient(90deg, var(--blue), var(--cyan)); border-radius: 99px; }
hr { border-color: var(--border) !important; }
[data-testid="stSidebar"] hr { margin: 1rem 0; }
::-webkit-scrollbar { width: 9px; height: 9px; } ::-webkit-scrollbar-thumb { background: #26324B; border-radius: 99px; } ::-webkit-scrollbar-track { background: transparent; }

/* ---------- responsive ---------- */
@media (max-width: 760px) {
  .stMainBlockContainer, .block-container { padding: 1.2rem 1rem 4rem; }
  .cg-hero { padding: 1.5rem 1.25rem; } .cg-hero h1 { font-size: 1.75rem; }
  .cg-pagehead h1 { font-size: 1.5rem; } .cg-profile { flex-direction: column; align-items: flex-start; }
  [data-testid="stChatMessageContent"], [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] { max-width: 100%; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
"""


# =====================================================
# HELPERS
# =====================================================

def _html(markup):
    """Render HTML safely through markdown (strips indentation so it never becomes a code block)."""
    st.markdown(" ".join(line.strip() for line in markup.splitlines() if line.strip()), unsafe_allow_html=True)


def inject_css():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def card(name):
    """Styled card container. `name` becomes the CSS hook, e.g. card('tone_good_1')."""
    return st.container(key=f"card_{name}")


# =====================================================
# COMPONENTS
# =====================================================

LOGO_SVG = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/>'
    '<path d="M16 8l-2.4 5.6L8 16l2.4-5.6z" fill="rgba(255,255,255,.25)"/></svg>'
)


def sidebar_brand():
    _html(f"""
    <div class="cg-brand">
      <div class="cg-logo">{LOGO_SVG}</div>
      <div><b>Career GPS</b><span>Your AI-powered career guide</span></div>
    </div>""")


def sidebar_footer():
    _html("""
    <div class="cg-side-note">Guidance across technology, healthcare, education, business,
    finance, engineering, law, creative industries and more.</div>
    <div class="cg-side-foot">Powered by Gemini, LangChain and FAISS</div>""")


def page_header(icon, title, subtitle=""):
    sub = f"<p>{esc(subtitle)}</p>" if subtitle else ""
    _html(f'<div class="cg-pagehead"><div class="cg-ico">{icon}</div><div><h1>{esc(title)}</h1>{sub}</div></div>')


def section(icon, title, subtitle=""):
    sub = f'<p class="cg-sub">{esc(subtitle)}</p>' if subtitle else ""
    _html(f'<div class="cg-sec"><i>{icon}</i>{esc(title)}</div>{sub}')


def heading(text):
    _html(f'<div class="cg-h2">{esc(text)}</div>')


def hero(greeting_html, text):
    _html(f"""
    <div class="cg-hero">
      <span class="tag">AI career assistant online</span>
      <h1>{greeting_html}</h1>
      <p>{esc(text)}</p>
    </div>""")


def stat_cards(items):
    """items: list of (icon, label, value, hint)."""
    cells = "".join(
        f'<div class="cg-stat"><div class="top"><span>{esc(label)}</span><span>{icon}</span></div>'
        f'<div class="val">{esc(str(value))}</div><div class="hint">{esc(hint)}</div></div>'
        for icon, label, value, hint in items
    )
    _html(f'<div class="cg-stats">{cells}</div>')


def progress_bar(label, percent, display=None):
    percent = max(0, min(100, int(percent)))
    shown = display if display is not None else f"{percent}%"
    _html(f"""
    <div class="cg-bar"><div class="row"><span>{esc(label)}</span><b>{esc(str(shown))}</b></div>
    <div class="track"><div class="fill" style="width:{percent}%"></div></div></div>""")


def checklist(items):
    """items: list of (label, done)."""
    rows = "".join(
        f'<div class="cg-check {"done" if done else ""}"><span class="dot">{"✓" if done else ""}</span>{esc(label)}</div>'
        for label, done in items
    )
    _html(rows)


def activity_list(rows):
    """rows: list of (icon, title, meta)."""
    out = "".join(
        f'<div class="cg-act"><div class="ic">{icon}</div><div><b>{esc(title)}</b><span>{esc(meta)}</span></div></div>'
        for icon, title, meta in rows
    )
    _html(out)


def badges(items, alt=False):
    cls = "cg-badge alt" if alt else "cg-badge"
    _html('<div class="cg-badges">' + "".join(f'<span class="{cls}">{esc(i)}</span>' for i in items) + "</div>")


def empty_state(icon, title, text):
    _html(f'<div class="cg-empty"><div class="big">{icon}</div><b>{esc(title)}</b>{esc(text)}</div>')


def stepper(current, total):
    dots = "".join(f'<span class="{"on" if i < current else ""}"></span>' for i in range(total))
    _html(f'<div class="cg-steps">{dots}</div>')


def question_box(text):
    _html(f'<div class="cg-question">{esc(text)}</div>')


def score_bars(scores, maximum=5):
    for criterion, score in scores.items():
        try:
            pct = float(score) / maximum * 100
        except (TypeError, ValueError):
            pct = 0
        progress_bar(str(criterion), pct, f"{score}/{maximum}")


def total_score(value, maximum=30):
    _html(f'<div class="cg-total"><b class="cg-grad">{esc(str(value))}</b><span>/ {maximum} total score</span></div>')


def profile_header(name, profession):
    initials = "".join(part[0] for part in (name or "").split()[:2]).upper() or "?"
    return f"""
    <div class="cg-profile"><div class="cg-avatar">{esc(initials)}</div>
    <div><h2>{esc(name or "Your Name")}</h2><p>{esc(profession or "Profession not added")}</p></div></div>"""


def render_profile_header(name, profession):
    _html(profile_header(name, profession))


def chat_welcome():
    _html(f"""
    <div class="cg-welcome">
      <div class="cg-orb">{LOGO_SVG.replace('width="22"', 'width="34"').replace('height="22"', 'height="34"')}</div>
      <h2>Hi, I'm your <span class="cg-grad">AI career advisor</span></h2>
      <p>Ask about careers, skills, education, job changes or interviews. When your knowledge base
      has relevant documents, I'll draw on them and show the sources.</p>
    </div>
    <div class="cg-chip-label">Try asking</div>""")


def typing_indicator(text="Thinking through your question"):
    return f'<div class="cg-typing"><i></i><i></i><i></i><span>{esc(text)}</span></div>'


@contextmanager
def ai_spinner(message="AI is processing your request..."):
    """Animated loader shown while a blocking AI call runs, cleared afterwards (also on errors)."""
    slot = st.empty()
    slot.markdown(
        f'<div class="cg-loader"><div class="ring"></div>'
        f'<div><b>{esc(message)}</b><span>This usually takes a few seconds</span></div></div>',
        unsafe_allow_html=True,
    )
    try:
        yield
    finally:
        slot.empty()


def unique_key(prefix):
    return f"{prefix}_{uuid4().hex[:8]}"