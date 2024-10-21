import streamlit as st
from openai import OpenAI
import os
import json
from datetime import datetime

# OpenAI API 키 설정
# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# OpenAI 클라이언트 초기화
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key) if api_key else None

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "당신은 도움이 되는 AI 어시스턴트입니다."

st.title("멀티턴 AI 채팅 테스트")

# 사이드바에 설정 추가
st.sidebar.title("설정")
new_system_prompt = st.sidebar.text_area("시스템 프롬프트:", value=st.session_state.system_prompt, height=100)
if new_system_prompt != st.session_state.system_prompt:
    st.session_state.system_prompt = new_system_prompt
    st.session_state.messages = []  # 시스템 프롬프트가 변경되면 대화 기록 초기화

# 모델 선택
model = st.sidebar.selectbox(
    "AI 모델을 선택하세요:",
    ("gpt-4o-mini", "gpt-3.5-turbo")
)

# 추가 매개변수 설정
temperature = st.sidebar.slider("Temperature:", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
max_tokens = st.sidebar.number_input("최대 토큰 수:", min_value=1, max_value=4096, value=256, step=1)
top_p = st.sidebar.slider("Top P:", min_value=0.0, max_value=1.0, value=1.0, step=0.1)

# 대화 기록 표시
for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.text_area("사용자:", value=message["content"], height=100, disabled=True, key=f"user_{idx}")
    else:
        st.text_area("AI:", value=message["content"], height=100, disabled=True, key=f"ai_{idx}")

# 채팅 입력 부분을 대화 기록 초기화 버튼 바로 위로 이동
user_input = st.text_input("메시지를 입력하세요:", key="user_input")

# 메시지 전송 버튼
if st.button("전송"):
    if user_input:
        # 사용자 메시지를 대화 기록에 추가
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # AI 응답 생성
        response = client.chat.completions.create(
            model=model,  # 선택된 모델 사용
            messages=[
                {"role": "system", "content": st.session_state.system_prompt},
                *st.session_state.messages
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        
        # AI 응답을 대화 기록에 추가
        ai_response = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        
        # 페이지 새로고침
        st.rerun()

# 대화 기록 초기화 버튼
if st.button("대화 기록 초기화"):
    st.session_state.messages = []
    st.rerun()

# 대화 내용 JSON 다운로드 버튼
if st.button("대화 내용 다운로드"):
    chat_data = {
        "system_prompt": st.session_state.system_prompt,
        "messages": st.session_state.messages,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p
    }
    json_string = json.dumps(chat_data, ensure_ascii=False, indent=2)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_history_{timestamp}.json"
    st.download_button(
        label="JSON 파일 다운로드",
        data=json_string,
        file_name=filename,
        mime="application/json"
    )
