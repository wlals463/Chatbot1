import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(page_title="ChatGPT Streamlit Bot", page_icon="💬")

# 제목
st.title("💬 Streamlit Chatbot powered by OpenAI")

# API Key 입력 또는 설정
openai_api_key = st.text_input("🔑 Enter your OpenAI API Key", type="password")

if not openai_api_key:
    st.warning("Please enter your API key to start chatting.")
    st.stop()

# 클라이언트 생성
client = OpenAI(api_key=openai_api_key)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

# 대화 출력
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").markdown(msg["content"])
    else:
        st.chat_message("assistant").markdown(msg["content"])

# 사용자 입력
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    # OpenAI API 호출
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages
        )
        reply = response.choices[0].message.content
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
