import os
import json
import time
import streamlit as st
from openai import OpenAI

# -------------------------------
# Page config & custom styles
# -------------------------------
st.set_page_config(
    page_title="여행용 챗봇과 대화하기",
    page_icon="🧭",
    layout="centered"
)

# Custom CSS for sleek look
st.markdown("""
<style>
/* Base font & width */
html, body, [class*="css"]  { font-family: "Pretendard", -apple-system, BlinkMacSystemFont, Inter, "Segoe UI", Roboto, "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", "Helvetica Neue", Arial, sans-serif; }
.block-container { max-width: 880px !important; }

/* Gradient header */
.app-header {
  background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 60%, #a855f7 100%);
  color: white; padding: 22px 22px; border-radius: 18px;
  box-shadow: 0 10px 24px rgba(36, 37, 47, 0.25);
  margin-bottom: 16px;
}
.app-header h1 { margin: 0 0 4px 0; font-weight: 800; letter-spacing: -0.02em; }
.app-header .sub { opacity: 0.92; font-size: 14.5px; }

/* Sidebar polishing */
section[data-testid="stSidebar"] { border-right: 1px solid rgba(0,0,0,0.06); }
.stMarkdown .sidebar-title { font-weight: 700; font-size: 15px; letter-spacing: .2px; }

/* Chat bubbles */
.chat-bubble { padding: 14px 16px; border-radius: 16px; margin: 8px 0; line-height: 1.55; }
.user { background: #111827; color: #f9fafb; border: 1px solid rgba(255,255,255,0.06); }
.assistant { background: #1118270d; border: 1px solid #e5e7eb; }
.role {
  font-size: 13px; font-weight: 700; margin-bottom: 4px; opacity: 0.7; display:flex; align-items:center; gap:8px;
}
.role .icon { width: 22px; height: 22px; display:inline-flex; align-items:center; justify-content:center; }
.footer-tip { opacity: 0.7; font-size: 12.5px; margin-top: 4px; }

/* System preview box */
.sysbox {
  background: #0f172a; color: #e2e8f0; border: 1px solid #334155;
  padding: 10px 12px; border-radius: 12px; font-size: 12.8px; line-height: 1.4;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Header
# -------------------------------
st.markdown("""
<div class="app-header">
  <h1>🧭 여행용 멀티링구얼 챗봇</h1>
  <div class="sub">여행지 추천 · 준비물 · 문화 · 음식까지 — 여러 언어로 한 번에 답해드려요.</div>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# Sidebar Controls
# -------------------------------
st.sidebar.markdown("### ⚙️ 설정", unsafe_allow_html=True)

# API Key
openai_api_key = st.sidebar.text_input("OpenAI API 키", type="password", help="환경변수 OPENAI_API_KEY도 인식합니다.")
effective_api_key = openai_api_key or os.getenv("OPENAI_API_KEY", "")

# Model & params
model = st.sidebar.selectbox("모델 선택", ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"], index=0)
temperature = st.sidebar.slider("창의성 (temperature)", 0.0, 1.5, 0.8, 0.1)

# Languages
languages = {
    "한국어": "ko", "영어": "en", "일본어": "ja", "중국어": "zh"
}
selected_languages = st.sidebar.multiselect(
    "지원할 언어",
    list(languages.keys()),
    default=["한국어"]
)

# System prompt builder
def build_system_prompt(selected_langs):
    langs = ", ".join(selected_langs) if selected_langs else "한국어"
    return (
        "당신은 여행에 관한 질문에 답하는 챗봇입니다. "
        "여행지 추천, 준비물, 문화, 음식 등 다양한 주제에 대해 친절하게 안내해 주세요. "
        f"모든 답변은 다음 언어로 동시에 제공하세요: {langs}. "
        "각 언어는 제목 이모지와 함께 구분된 섹션(---)으로 나누어 주세요. "
        "간결하되 핵심 정보(예산 범위, 계절, 교통수단, 로컬 팁)를 포함하세요."
    )

system_prompt = build_system_prompt(selected_languages)

with st.sidebar.expander("🧠 시스템 프롬프트 미리보기", expanded=False):
    st.markdown(f"<div class='sysbox'>{system_prompt}</div>", unsafe_allow_html=True)

# Clear / Export
col_a, col_b = st.sidebar.columns(2)
clear_chat = col_a.button("🧹 초기화")
export_chat = col_b.button("💾 내보내기")

# -------------------------------
# Init Session State
# -------------------------------
if "messages" not in st.session_state or clear_chat:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# -------------------------------
# OpenAI Client
# -------------------------------
if not effective_api_key:
    st.warning("🔑 좌측 사이드바에서 OpenAI API 키를 입력하세요.")
    st.stop()

client = OpenAI(api_key=effective_api_key)

# -------------------------------
# Chat Area
# -------------------------------
def render_message(msg):
    if msg["role"] == "system":
        return  # hide system
    is_user = (msg["role"] == "user")
    bubble_class = "user" if is_user else "assistant"
    icon = "👤" if is_user else "🤖"
    who = "나" if is_user else "어시스턴트"

    st.markdown(f"""
    <div class="chat-bubble {bubble_class}">
      <div class="role"><span class="icon">{icon}</span>{who}</div>
      <div>{msg['content']}</div>
    </div>
    """, unsafe_allow_html=True)

# Existing history
for m in st.session_state.messages:
    render_message(m)

# -------------------------------
# Input & Completion
# -------------------------------
prompt = st.chat_input("여행에 대해 무엇이든 물어보세요 (예: 오사카 3박 4일 코스, 10월 유럽 날씨, 저예산 맛집)")

if prompt:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_message({"role": "user", "content": prompt})

    # Call OpenAI
    with st.spinner("답변 생성 중..."):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=st.session_state.messages
            )
            assistant_reply = response.choices[0].message.content
        except Exception as e:
            assistant_reply = f"오류가 발생했어요: {e}"

    # Append assistant message
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    render_message({"role": "assistant", "content": assistant_reply})

# -------------------------------
# Export
# -------------------------------
if export_chat:
    export_msgs = [m for m in st.session_state.messages if m["role"] != "system"]
    fname = f"travel_chat_{int(time.time())}.json"
    st.download_button(
        "대화 JSON 다운로드",
        data=json.dumps(export_msgs, ensure_ascii=False, indent=2),
        file_name=fname,
        mime="application/json"
    )
    st.caption("💡 시스템 프롬프트는 제외된 대화만 저장됩니다.")

# -------------------------------
# Footer tip
# -------------------------------
st.markdown("""
<div class="footer-tip">
💡 팁: 사이드바에서 언어를 여러 개 선택하면 응답이 언어별 섹션으로 정리되어 출력돼요.
</div>
""", unsafe_allow_html=True)
