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
if "results" not in st.session_state:
    st.session_state.results = []

st.title("프롬프트 테스트 도구")

# 사이드바에 설정 추가
st.sidebar.title("설정")

# 사용자 정의 시스템 프롬프트 입력
new_prompt = st.sidebar.text_area(
    "새 시스템 프롬프트 추가:", height=100
)
if st.sidebar.button("프롬프트 추가") and new_prompt:
    st.session_state.system_prompts.append(new_prompt)

# 모델 선택
model = st.sidebar.selectbox(
    "AI 모델을 선택하세요:", ("gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo")
)

# 추가 매개변수 설정
temperature = st.sidebar.slider("온도:", 0.0, 1.0, 0.7, 0.1)
max_tokens = st.sidebar.number_input("최대 토큰 수:", 1, 4096, 256, 1)
top_p = st.sidebar.slider("Top P:", 0.0, 1.0, 1.0, 0.1)
num_iterations = st.sidebar.number_input("반복 횟수:", min_value=1, max_value=10, value=1, step=1)

# A/B 테스트 활성화 여부
ab_testing_enabled = st.sidebar.checkbox("A/B 테스트 사용")

# 대화 기록 초기화 버튼
if st.sidebar.button("대화 기록 초기화"):
    st.session_state.messages = []
    st.session_state.results = []
    st.experimental_rerun()

# 시스템 프롬프트 리스트 표시
st.sidebar.write("### 현재 시스템 프롬프트")
for idx, prompt in enumerate(st.session_state.system_prompts):
    st.sidebar.write(f"{idx + 1}. {prompt}")

# 사용자 입력
user_input = st.text_input("메시지를 입력하세요:")

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
if st.button("프롬프트 테스트"):
    if user_input and client:
        for _ in range(num_iterations):
            responses = []

            if ab_testing_enabled:
                # A/B 테스트 활성화: Prompt A와 Prompt B 동시 테스트
                prompt_a = st.sidebar.text_area("Prompt A:", value=st.session_state.system_prompts[0], height=100)
                prompt_b = st.sidebar.text_area("Prompt B:", value="당신은 지식이 풍부한 AI 도우미입니다.", height=100)

                for prompt in [prompt_a, prompt_b]:
                    try:
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": prompt},
                                {"role": "user", "content": user_input}
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
                        st.error(f"응답 생성 중 오류 발생: {str(e)}")

            else:
                # 일반 테스트: 모든 프롬프트 순차 테스트
                for prompt in st.session_state.system_prompts:
                    try:
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": prompt},
                                {"role": "user", "content": user_input}
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
                        st.error(f"응답 생성 중 오류 발생: {str(e)}")

            # 결과 저장
            st.session_state.messages.extend(responses)

        st.experimental_rerun()

# 대화 기록 표시
for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.text_area("사용자:", value=message["content"], height=100, disabled=True, key=f"user_{idx}")
    else:
        st.text_area("AI:", value=message["content"], height=100, disabled=True, key=f"ai_{idx}")

# JSON 다운로드 버튼
if st.session_state.messages:
    if st.button("JSON 결과 다운로드"):
        chat_data = {
            "system_prompts": st.session_state.system_prompts,
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
            label="JSON 다운로드",
            data=json_string,
            file_name=filename,
            mime="application/json"
        )