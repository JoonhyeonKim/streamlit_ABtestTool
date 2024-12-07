import streamlit as st
from openai import OpenAI
import os
import json
from datetime import datetime
from typing import TypedDict, List

# OpenAI API 키 설정
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key) if api_key else None

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "system_prompts" not in st.session_state:
    st.session_state.system_prompts = ["당신은 도움이 되는 AI 어시스턴트입니다."]
if "selected_prompts" not in st.session_state:
    st.session_state.selected_prompts = []

st.title("멀티턴 AI 채팅 테스트")

# 사이드바에 설정 추가
st.sidebar.title("설정")
new_system_prompt = st.sidebar.text_area("새 시스템 프롬프트 추가:", height=100)
if st.sidebar.button("프롬프트 추가") and new_system_prompt:
    st.session_state.system_prompts.append(new_system_prompt)

# 현재 프롬프트 리스트와 선택 옵션
st.sidebar.write("### 현재 시스템 프롬프트")
for idx, prompt in enumerate(st.session_state.system_prompts):
    if st.sidebar.checkbox(f"버전 {idx + 1}", key=f"prompt_{idx}"):
        if idx not in st.session_state.selected_prompts:
            st.session_state.selected_prompts.append(idx)
    else:
        if idx in st.session_state.selected_prompts:
            st.session_state.selected_prompts.remove(idx)

# 선택된 프롬프트 표시
st.sidebar.write("**선택된 프롬프트:**")
if st.session_state.selected_prompts:
    for idx in st.session_state.selected_prompts:
        with st.sidebar.expander(f"버전 {idx + 1}"):
            st.write(st.session_state.system_prompts[idx])
else:
    st.sidebar.write("선택된 프롬프트가 없습니다.")

# 모델 선택
model = st.sidebar.selectbox(
    "AI 모델을 선택하세요:",
    ("gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo")
)

# 추가 매개변수 설정
temperature = st.sidebar.slider("Temperature:", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
max_tokens = st.sidebar.number_input("최대 토큰 수:", min_value=1, max_value=4096, value=256, step=1)
top_p = st.sidebar.slider("Top P:", min_value=0.0, max_value=1.0, value=1.0, step=0.1)
num_iterations = st.sidebar.number_input("반복 횟수:", min_value=1, max_value=10, value=1, step=1)

# 대화 기록 표시
for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.text_area("사용자:", value=message["content"], height=100, disabled=True, key=f"user_{idx}")
    else:
        st.text_area("AI:", value=message["content"], height=100, disabled=True, key=f"ai_{idx}")

# 채팅 입력 부분을 대화 기록 초기화 버튼 바로 위로 이동
user_input = st.text_input("메시지를 입력하세요:", key="user_input")

# 응답 구조체 정의
class ChatResponse(TypedDict):
    total_round: int
    answer_count: int
    current_answer: str
    hint: List[str]
    check_answer: bool
    is_end: bool
    message: str

# 메시지 전송 버튼
if st.button("전송"):
    if user_input:
        # 사용자 메시지를 대화 기록에 추가
        st.session_state.messages.append({"role": "user", "content": user_input})

        # AI 응답 생성 반복
        for _ in range(num_iterations):
            responses = []
            for idx in st.session_state.selected_prompts:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": st.session_state.system_prompts[idx]},
                            *st.session_state.messages
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        response_format={"type": "json_object"}
                    )

                    ai_response = response.choices[0].message.content
                    structured_response = json.loads(ai_response)

                    validated_response = ChatResponse(
                        total_round=structured_response.get('total_round', 1),
                        answer_count=structured_response.get('answer_count', 0),
                        current_answer=structured_response.get('current_answer', ''),
                        hint=structured_response.get('hint', []),
                        check_answer=structured_response.get('check_answer', False),
                        is_end=structured_response.get('is_end', False),
                        message=structured_response.get('message', '')
                    )

                    responses.append({
                        "role": "assistant",
                        "content": json.dumps(validated_response, ensure_ascii=False, indent=2)
                    })
                except json.JSONDecodeError:
                    st.error("AI 응답을 JSON으로 파싱할 수 없습니다.")
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {str(e)}")

            # 대화 기록에 추가
            st.session_state.messages.extend(responses)

        # 페이지 새로고침
        st.rerun()

# 대화 기록 초기화 버튼
if st.button("대화 기록 초기화"):
    st.session_state.messages = []
    st.rerun()

# 대화 내용 JSON 다운로드 버튼
if st.button("대화 내용 다운로드"):
    chat_data = {
        "system_prompts": st.session_state.system_prompts,
        "selected_prompts": [st.session_state.system_prompts[idx] for idx in st.session_state.selected_prompts],
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