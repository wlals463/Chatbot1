import streamlit as st
from openai import OpenAI

# --- 페이지 설정 ---
st.set_page_config(page_title="Streamlit Chatbot", page_icon="🤖", layout="centered")

st.title("💬 Streamlit Chatbot")
st.write("OpenAI API 키를 입력하고 챗봇과 대화해보세요!")

# --- API 키 입력 ---
api_key = st.text_input("🔑 OpenAI API 키를 입력하세요:", type="password")

if not api_key:
    st.warning("API 키를 입력해야 합니다.")
    st.stop()

# --- 클라이언트 생성 ---
try:
    client = OpenAI(api_key=api_key)
except Exception as e:
    st.error(f"API 키가 유효하지 않습니다: {e}")
    st.stop()

# --- 대화 저장소 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 이전 대화 출력 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 사용자 입력 ---
if prompt := st.chat_input("무엇이든 물어보세요!"):
    # 사용자 메시지 표시
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # OpenAI 응답 생성
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages,
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"오류 발생: {e}"

    # 챗봇 응답 표시
    with st.chat_message("assistant"):
        st.markdown(reply)

    # 대화 저장
    st.session_state.messages.append({"role": "assistant", "content": reply})
