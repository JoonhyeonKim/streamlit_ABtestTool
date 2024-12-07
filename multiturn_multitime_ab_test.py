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
    "AI 모델 선택:", ("gpt-4", "gpt-4-turbo", "gpt-3.5-turbo")
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
    prompt: str
    user_message: str
    model_response: str
    feedback: str
    improvement_suggestions: str

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
                            prompt=prompt,
                            user_message=user_input,
                            model_response=structured_response.get('message', ''),
                            feedback="",
                            improvement_suggestions=""
                        )

                        responses.append(validated_response)
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
                            prompt=prompt,
                            user_message=user_input,
                            model_response=structured_response.get('message', ''),
                            feedback="",
                            improvement_suggestions=""
                        )

                        responses.append(validated_response)
                    except json.JSONDecodeError:
                        st.error("AI 응답을 JSON으로 파싱할 수 없습니다.")
                    except Exception as e:
                        st.error(f"응답 생성 중 오류 발생: {str(e)}")

            # 결과 저장
            st.session_state.results.extend(responses)

        st.experimental_rerun()

# 결과 표시
if st.session_state.results:
    st.write("## 테스트 결과")
    for idx, result in enumerate(st.session_state.results):
        st.write(f"### 테스트 {idx + 1}")
        st.text_area("시스템 프롬프트", result["prompt"], height=100, disabled=True)
        st.text_area("사용자 메시지", result["user_message"], height=50, disabled=True)
        st.text_area("모델 응답", result["model_response"], height=150, disabled=True)

        feedback = st.text_area(
            "피드백 (선택 사항)", result["feedback"], height=50, key=f"feedback_{idx}"
        )

        if feedback and feedback != result["feedback"]:
            # Provide improvement suggestions based on feedback
            improvement_suggestions = (
                "프롬프트를 더 명확하게 작성하는 것을 고려하세요."  # Placeholder for feedback analysis logic
            )
            result.update({"feedback": feedback, "improvement_suggestions": improvement_suggestions})

        if result["improvement_suggestions"]:
            st.write("**개선 제안:**")
            st.write(result["improvement_suggestions"])

# JSON 다운로드 버튼
if st.session_state.results:
    if st.button("JSON 결과 다운로드"):
        results_data = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "num_iterations": num_iterations,
            "tests": st.session_state.results
        }
        json_string = json.dumps(results_data, ensure_ascii=False, indent=2)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prompt_test_results_{timestamp}.json"
        st.download_button(
            label="JSON 다운로드",
            data=json_string,
            file_name=filename,
            mime="application/json"
        )
