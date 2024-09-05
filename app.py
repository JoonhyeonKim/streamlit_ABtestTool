import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI 클라이언트 초기화 (API 키가 없으면 None으로 설정)
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

# 페이지 설정을 와이드 모드로 변경하고 한글 폰트 지원
st.set_page_config(layout="wide", page_title="AB Test Tool", page_icon="🤖")
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태 초기화
if 'test_results' not in st.session_state:
    st.session_state.test_results = []
if 'last_run_results' not in st.session_state:
    st.session_state.last_run_results = None
if 'current_settings' not in st.session_state:
    st.session_state.current_settings = {
        'model_a': 'gpt-3.5-turbo',
        'model_b': 'gpt-3.5-turbo',
        'temperature_a': 0.7,
        'temperature_b': 0.7,
        'max_tokens_a': 256,
        'max_tokens_b': 256,
        'top_p_a': 1.0,
        'top_p_b': 1.0,
        'presence_penalty_a': 0.0,
        'presence_penalty_b': 0.0,
        'frequency_penalty_a': 0.0,
        'frequency_penalty_b': 0.0,
        'system_prompt': '당신은 도움이 되는 AI입니다.',
    }
if 'save_results' not in st.session_state:
    st.session_state.save_results = False

# 모델 응답을 생성하는 함수
def generate_model_response(model, system_prompt, user_input, temperature, max_tokens, top_p, presence_penalty, frequency_penalty):
    if model == "ClovaX":
        return f"ClovaX의 응답: 이것은 테스트 응답입니다. 한글 테스트: 안녕하세요."
    elif client is None:
        return "OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요."
    else:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

# 사용자 입력 처리 및 테스트 실행 함수
def process_user_input_and_run_test():
    st.session_state.processed_input = st.session_state.user_input
    st.session_state.run_test = True

# 결과를 JSON 파일로 저장하는 함수
def save_results_to_json(results):
    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        st.success(f"결과가 {filename}에 저장되었습니다.")
    else:
        st.warning("저장할 테스트 결과가 없습니다.")

# 제목 및 설명
st.title("Chatbot Arena")
st.write("챗봇 아레나 방식으로 두 개의 LLM을 비교해보세요.")

# 메인 레이아웃
col1, col2 = st.columns([3, 1])

# 결과 표시 부분 (왼쪽 칼럼)
with col1:
    st.subheader("모델 응답 비교")
    
    # 테스트 횟수 설정
    num_tests = st.number_input("테스트 횟수", min_value=1, max_value=30, value=1, step=1)
    
    # 저장 옵션
    save_option = st.checkbox("결과 저장", value=False)
    
    if 'processed_input' in st.session_state and st.session_state.processed_input:
        st.write(f"**사용자:** {st.session_state.processed_input}")
        
        if st.session_state.get('run_test', False):
            st.session_state.last_run_results = []
            for test_num in range(num_tests):
                st.write(f"**테스트 #{test_num + 1}**")
                subcol1, subcol2 = st.columns(2)
                test_result = {
                    "test_number": test_num + 1,
                    "user_input": st.session_state.processed_input,
                    "system_prompt": st.session_state.current_settings['system_prompt'],
                    "models": {}
                }
                for col, model_key, model_name in [(subcol1, 'model_a', '모델 A'), (subcol2, 'model_b', '모델 B')]:
                    with col:
                        response = generate_model_response(
                            st.session_state.current_settings[model_key],
                            st.session_state.current_settings['system_prompt'],
                            st.session_state.processed_input,
                            st.session_state.current_settings[f'temperature_{model_key[-1]}'],
                            st.session_state.current_settings[f'max_tokens_{model_key[-1]}'],
                            st.session_state.current_settings[f'top_p_{model_key[-1]}'],
                            st.session_state.current_settings[f'presence_penalty_{model_key[-1]}'],
                            st.session_state.current_settings[f'frequency_penalty_{model_key[-1]}']
                        )
                        st.markdown(f"""
                        <div style="border:1px solid #ddd; padding:10px; border-radius:5px;">
                            <h4 style="margin-top:0;">{st.session_state.current_settings[model_key]}</h4>
                            <p>{response}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        test_result["models"][model_name] = {
                            "name": st.session_state.current_settings[model_key],
                            "response": response,
                            "settings": {
                                "temperature": st.session_state.current_settings[f'temperature_{model_key[-1]}'],
                                "max_tokens": st.session_state.current_settings[f'max_tokens_{model_key[-1]}'],
                                "top_p": st.session_state.current_settings[f'top_p_{model_key[-1]}'],
                                "presence_penalty": st.session_state.current_settings[f'presence_penalty_{model_key[-1]}'],
                                "frequency_penalty": st.session_state.current_settings[f'frequency_penalty_{model_key[-1]}']
                            }
                        }
                st.write("---")
                st.session_state.last_run_results.append(test_result)
            st.session_state.run_test = False
            
            # 저장 옵션이 선택되었을 때만 결과 저장
            if save_option:
                save_results_to_json(st.session_state.last_run_results)
        
        if st.session_state.last_run_results:
            # 이전 실행 결과 표시
            for test_result in st.session_state.last_run_results:
                st.write(f"**테스트 #{test_result['test_number']}**")
                subcol1, subcol2 = st.columns(2)
                for col, model_name in [(subcol1, '모델 A'), (subcol2, '모델 B')]:
                    with col:
                        response = test_result["models"][model_name]["response"]
                        st.markdown(f"""
                        <div style="border:1px solid #ddd; padding:10px; border-radius:5px;">
                            <h4 style="margin-top:0;">{test_result["models"][model_name]["name"]}</h4>
                            <p>{response}</p>
                        </div>
                        """, unsafe_allow_html=True)
                st.write("---")
    else:
        st.write("아직 사용자 입력이 없습니다.")

# 설정 및 입력 부분 (오른쪽 칼럼)
with col2:
    st.subheader("설정 및 입력")
    
    # API 키 상태 표시
    if api_key:
        st.success("OpenAI API 키가 설정되었습니다.")
    else:
        st.warning("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")
    
    tab1, tab2 = st.tabs(["채팅 인터페이스", "모델 설정"])
    
    # 채팅 인터페이스 탭
    with tab1:
        st.session_state.current_settings['system_prompt'] = st.text_area("시스템 프롬프트", value=st.session_state.current_settings['system_prompt'])
        user_input = st.text_input("사용자 입력", key="user_input")

        # 대화 처리
        if st.button("전송"):
            if st.session_state.user_input:
                process_user_input_and_run_test()
            else:
                st.write("사용자 입력을 입력해주세요.")

    # 모델 설정 탭
    with tab2:
        st.subheader("모델 A 설정")
        st.session_state.current_settings['model_a'] = st.selectbox("모델 A 선택", ("gpt-3.5-turbo", "gpt-4", "ClovaX"), key="model_a")
        st.session_state.current_settings['temperature_a'] = st.slider("Temperature (모델 A)", 0.0, 1.0, st.session_state.current_settings['temperature_a'], key="temperature_a")
        st.session_state.current_settings['max_tokens_a'] = st.slider("Max Tokens (모델 A)", 50, 1024, st.session_state.current_settings['max_tokens_a'], key="max_tokens_a")
        st.session_state.current_settings['top_p_a'] = st.slider("Top P (모델 A)", 0.0, 1.0, st.session_state.current_settings['top_p_a'], key="top_p_a")
        st.session_state.current_settings['presence_penalty_a'] = st.slider("Presence Penalty (모델 A)", -2.0, 2.0, st.session_state.current_settings['presence_penalty_a'], key="presence_penalty_a")
        st.session_state.current_settings['frequency_penalty_a'] = st.slider("Frequency Penalty (모델 A)", -2.0, 2.0, st.session_state.current_settings['frequency_penalty_a'], key="frequency_penalty_a")

        st.subheader("모델 B 설정")
        st.session_state.current_settings['model_b'] = st.selectbox("모델 B 선택", ("gpt-3.5-turbo", "gpt-4", "ClovaX"), key="model_b")
        st.session_state.current_settings['temperature_b'] = st.slider("Temperature (모델 B)", 0.0, 1.0, st.session_state.current_settings['temperature_b'], key="temperature_b")
        st.session_state.current_settings['max_tokens_b'] = st.slider("Max Tokens (모델 B)", 50, 1024, st.session_state.current_settings['max_tokens_b'], key="max_tokens_b")
        st.session_state.current_settings['top_p_b'] = st.slider("Top P (모델 B)", 0.0, 1.0, st.session_state.current_settings['top_p_b'], key="top_p_b")
        st.session_state.current_settings['presence_penalty_b'] = st.slider("Presence Penalty (모델 B)", -2.0, 2.0, st.session_state.current_settings['presence_penalty_b'], key="presence_penalty_b")
        st.session_state.current_settings['frequency_penalty_b'] = st.slider("Frequency Penalty (모델 B)", -2.0, 2.0, st.session_state.current_settings['frequency_penalty_b'], key="frequency_penalty_b")