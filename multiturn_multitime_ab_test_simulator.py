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
if "simulation_prompt" not in st.session_state:
    st.session_state.simulation_prompt = "시뮬레이션 사용자 역할입니다."
if "selected_prompts" not in st.session_state:
    st.session_state.selected_prompts = []
if "turn_limit" not in st.session_state:
    st.session_state.turn_limit = 1

st.title("멀티턴 AI 시뮬레이션 테스트")

# 사이드바에 설정 추가
st.sidebar.title("설정")
new_system_prompt = st.sidebar.text_area("새 테스트 프롬프트 추가:", height=100)
if st.sidebar.button("테스트 프롬프트 추가") and new_system_prompt:
    st.session_state.system_prompts.append(new_system_prompt)

st.sidebar.write("### 시뮬레이션 프롬프트")
st.session_state.simulation_prompt = st.sidebar.text_area(
    "시뮬레이션 사용자 역할 프롬프트:", value=st.session_state.simulation_prompt, height=100
)

# 현재 테스트 프롬프트 리스트와 선택 옵션
st.sidebar.write("### 현재 테스트 프롬프트")
for idx, prompt in enumerate(st.session_state.system_prompts):
    if st.sidebar.checkbox(f"버전 {idx + 1}", key=f"prompt_{idx}"):
        if idx not in st.session_state.selected_prompts:
            st.session_state.selected_prompts.append(idx)
    else:
        if idx in st.session_state.selected_prompts:
            st.session_state.selected_prompts.remove(idx)

# 선택된 테스트 프롬프트 표시
st.sidebar.write("**선택된 테스트 프롬프트:**")
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
st.session_state.turn_limit = st.sidebar.number_input("대화 턴 수:", min_value=1, max_value=10, value=1, step=1)

# 대화 기록 표시
st.write("### 사용자 대화 기록")
for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.text_area("사용자:", value=message["content"], height=100, disabled=True, key=f"user_{idx}")
    else:
        st.text_area("AI:", value=message["content"], height=100, disabled=True, key=f"ai_{idx}")

# 채팅 입력 부분
if st.button("메시지 추가"):
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        # 페이지를 새로고침하는 대신 입력된 메시지를 업데이트
        st.experimental_set_query_params(reload="true")

# 응답 구조체 정의
class ChatResponse(TypedDict):
    total_round: int
    answer_count: int
    current_answer: str
    hint: List[str]
    check_answer: bool
    is_end: bool
    message: str

# 시뮬레이션 실행
if st.button("시뮬레이션 실행"):
    simulation_results = []

    if not st.session_state.selected_prompts:
        st.error("테스트 프롬프트를 하나 이상 선택해야 합니다.")
    else:
        messages = []
        messages.extend(st.session_state.messages)

        for prompt_idx in st.session_state.selected_prompts:
            prompt = st.session_state.system_prompts[prompt_idx]
            simulation_prompt = st.session_state.simulation_prompt

            for turn in range(st.session_state.turn_limit):
                try:
                    # 테스트 프롬프트 사용
                    response_a = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "system", "content": prompt}] + messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        response_format={"type": "json_object"}
                    )

                    ai_response_a = response_a.choices[0].message.content
                    structured_response_a = json.loads(ai_response_a)

                    validated_response_a = ChatResponse(
                        total_round=structured_response_a.get('total_round', 1),
                        answer_count=structured_response_a.get('answer_count', 0),
                        current_answer=structured_response_a.get('current_answer', ''),
                        hint=structured_response_a.get('hint', []),
                        check_answer=structured_response_a.get('check_answer', False),
                        is_end=structured_response_a.get('is_end', False),
                        message=structured_response_a.get('message', '')
                    )

                    messages.append({"role": "assistant", "content": validated_response_a["message"]})

                    # 시뮬레이션 프롬프트 사용
                    response_b = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "system", "content": simulation_prompt}] + messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p
                    )

                    ai_response_b = response_b.choices[0].message.content

                    try:
                        structured_response_b = json.loads(ai_response_b)
                        validated_response_b = ChatResponse(
                            total_round=structured_response_b.get('total_round', 1),
                            answer_count=structured_response_b.get('answer_count', 0),
                            current_answer=structured_response_b.get('current_answer', ''),
                            hint=structured_response_b.get('hint', []),
                            check_answer=structured_response_b.get('check_answer', False),
                            is_end=structured_response_b.get('is_end', False),
                            message=structured_response_b.get('message', '')
                        )
                        messages.append({"role": "assistant", "content": validated_response_b["message"]})
                    except json.JSONDecodeError:
                        messages.append({"role": "assistant", "content": ai_response_b})

                    if validated_response_a["is_end"]:
                        break

                except json.JSONDecodeError:
                    st.error("AI 응답을 JSON으로 파싱할 수 없습니다.")
                    break
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {str(e)}")
                    break

            simulation_results.append({
                "prompt_version": prompt_idx + 1,
                "response": messages
            })

    # 시뮬레이션 결과 표시
    st.write("### 시뮬레이션 결과")
    for result in simulation_results:
        with st.expander(f"테스트 프롬프트 버전 {result['prompt_version']} 결과"):
            for message in result['response']:
                role = "사용자" if message["role"] == "user" else "AI"
                st.text_area(f"{role}:", value=message["content"], height=100, disabled=True)

# 대화 기록 초기화 버튼
if st.button("대화 기록 초기화"):
    st.session_state.messages = []
    st.experimental_rerun()

# 대화 내용 JSON 다운로드 버튼
if st.button("대화 내용 다운로드"):
    chat_data = {
        "system_prompts": st.session_state.system_prompts,
        "simulation_prompt": st.session_state.simulation_prompt,
        "selected_prompts": [st.session_state.system_prompts[idx] for idx in st.session_state.selected_prompts],
        "messages": st.session_state.messages,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "turn_limit": st.session_state.turn_limit
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
