import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
import json

# .env 파일 로드
load_dotenv()

# OpenAI 클라이언트 초기화 (API 키가 없으면 None으로 설정)
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

# Clova API 키 로드
clova_api_key = os.getenv("CLOVA_API_KEY")
clova_apigw_key = os.getenv("CLOVA_APIGW_KEY")

# Clova API 호출 함수
def generate_clova_response(system_prompt, user_input, max_tokens, temperature, top_p):
    api_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-DASH-001"
    headers = {
        "Content-Type": "application/json",
        "X-NCP-CLOVASTUDIO-API-KEY": clova_api_key,
        "X-NCP-APIGW-API-KEY": clova_apigw_key,
        'X-NCP-CLOVASTUDIO-REQUEST-ID': '35c5350c-355d-4e46-a8d7-8b80a5c70c6f'
    }
    data = {
        "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
        "maxTokens": max_tokens,
        "temperature": temperature,
        "topP": top_p,
        "n": 1,
        "echo": False
    }
    
    response = requests.post(api_url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        result = response.json()['result']
        return result['message']['content']
    else:
        return f"Error: {response.status_code}, {response.text}"

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
        'system_prompt': '당신은 도움이 되는 AI입니다.',
    }

# 모델 응답을 생성하는 함수
def generate_model_response(model, system_prompt, user_input, temperature, max_tokens, top_p):
    if model == "ClovaX":
        return generate_clova_response(system_prompt, user_input, max_tokens, temperature, top_p)
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
                top_p=top_p
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

# 결과를 JSON 파일로 저장하는 함수
def save_results_to_json():
    if st.session_state.test_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        # 새로운 JSON 구조 생성
        json_data = {
            "system_prompt": st.session_state.current_settings['system_prompt'],
            "user_input": st.session_state.test_results[0]['user_input'],
            "settings": {
                "model_a": {
                    "name": st.session_state.current_settings['model_a'],
                    "temperature": st.session_state.current_settings['temperature_a'],
                    "max_tokens": st.session_state.current_settings['max_tokens_a'],
                    "top_p": st.session_state.current_settings['top_p_a'],
                },
                "model_b": {
                    "name": st.session_state.current_settings['model_b'],
                    "temperature": st.session_state.current_settings['temperature_b'],
                    "max_tokens": st.session_state.current_settings['max_tokens_b'],
                    "top_p": st.session_state.current_settings['top_p_b'],
                }
            },
            "results": [
                {
                    "test_number": result['test_number'],
                    "model_a_response": result['model_a_response'],
                    "model_b_response": result['model_b_response']
                } for result in st.session_state.test_results
            ]
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        st.success(f"결과가 {filename}에 저장되었습니다.")
    else:
        st.warning("저장할 테스트 결과가 없습니다.")

# 제목 및 설명
st.title("Chatbot Arena")

# 메인 레이아웃
col1, col2 = st.columns([3, 1])

# 결과 표시 부분 (왼쪽 칼럼)
with col1:
    st.subheader("사용 방법")
    st.write("1. 모델 설정 탭에서 모델 A와 모델 B를 설정합니다. 모델 설정 탭에서 모델 A와 모델 B의 설정을 각각 변경할 수 있습니다.")
    st.write("2. 채팅 인터페이스 탭에서 사용자 입력을 입력하고 전송 버튼을 클릭하여 테스트를 시작합니다.")
    st.write("3. 결과를 확인 및 저장하려면 결과 저장 옵션을 선택시 저장 및 결과가 출력됩니다.")
    st.write("4. 결과는 테스트 횟수만큼 출력되며, 테스트 횟수는 최대 30회까지 설정할 수 있습니다. 가장 마지막으로 수행된 테스트 결과 묶음이 저장됩니다.")
    st.subheader("모델 응답 비교")
    

    
    # 저장 옵션
    save_option = st.checkbox("결과 저장", value=False)
    
    if st.session_state.test_results:
        for test_result in st.session_state.test_results:
            st.write(f"**사용자:** {test_result['user_input']}")
            st.write(f"**테스트 #{test_result['test_number']}**")
            subcol1, subcol2 = st.columns(2)
            for col, model_key in [(subcol1, 'model_a'), (subcol2, 'model_b')]:
                with col:
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; padding:10px; border-radius:5px;">
                        <h4 style="margin-top:0;">{st.session_state.current_settings[model_key]}</h4>
                        <p>{test_result[f'{model_key}_response']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("---")
    
    if save_option:
        save_results_to_json()

# 설정 및 입력 부분 (오른쪽 칼럼)
with col2:
    st.subheader("설정 및 입력")
    
    # API 키 상태 표시
    if api_key:
        st.success("OpenAI API 키가 설정되었습니다.")
    else:
        st.warning("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")
    
    if clova_api_key and clova_apigw_key:
        st.success("Clova API 키가 설정되었습니다.")
    else:
        st.warning("Clova API 키가 설정되지 않았습니다. .env 파일에 CLOVA_API_KEY와 CLOVA_APIGW_KEY를 추가해주세요.")
    # 테스트 횟수 설정
    num_tests = st.number_input("테스트 횟수", min_value=1, max_value=30, value=1, step=1)
    tab1, tab2 = st.tabs(["채팅 인터페이스", "모델 설정"])
    
    # 채팅 인터페이스 탭
    with tab1:
        st.session_state.current_settings['system_prompt'] = st.text_area("시스템 프롬프트", value=st.session_state.current_settings['system_prompt'])
        user_input = st.text_input("사용자 입력", key="user_input")

        # 대화 처리
        if st.button("전송"):
            if user_input:
                st.session_state.test_results = []
                for test_num in range(num_tests):
                    test_result = {
                        "test_number": test_num + 1,
                        "user_input": user_input,
                        "system_prompt": st.session_state.current_settings['system_prompt'],
                    }
                    for model_key in ['model_a', 'model_b']:
                        response = generate_model_response(
                            st.session_state.current_settings[model_key],
                            st.session_state.current_settings['system_prompt'],
                            user_input,
                            st.session_state.current_settings[f'temperature_{model_key[-1]}'],
                            st.session_state.current_settings[f'max_tokens_{model_key[-1]}'],
                            st.session_state.current_settings[f'top_p_{model_key[-1]}'],
                        )
                        test_result[f"{model_key}_response"] = response
                    st.session_state.test_results.append(test_result)
            else:
                st.write("사용자 입력을 입력해주세요.")

    # 모델 설정 탭
    with tab2:
        st.subheader("모델 A 설정")
        st.session_state.current_settings['model_a'] = st.selectbox("모델 A 선택", ("gpt-4o", "gpt-4o-mini", "ClovaX"), key="model_a")
        st.session_state.current_settings['temperature_a'] = st.slider("Temperature (모델 A)", 0.0, 1.0, st.session_state.current_settings['temperature_a'], key="temperature_a")
        st.session_state.current_settings['max_tokens_a'] = st.slider("Max Tokens (모델 A)", 50, 2048, st.session_state.current_settings['max_tokens_a'], key="max_tokens_a")
        st.session_state.current_settings['top_p_a'] = st.slider("Top P (모델 A)", 0.0, 1.0, st.session_state.current_settings['top_p_a'], key="top_p_a")

        st.subheader("모델 B 설정")
        st.session_state.current_settings['model_b'] = st.selectbox("모델 B 선택", ("gpt-4o", "gpt-4o-mini", "ClovaX"), key="model_b")
        st.session_state.current_settings['temperature_b'] = st.slider("Temperature (모델 B)", 0.0, 1.0, st.session_state.current_settings['temperature_b'], key="temperature_b")
        st.session_state.current_settings['max_tokens_b'] = st.slider("Max Tokens (모델 B)", 50, 2048, st.session_state.current_settings['max_tokens_b'], key="max_tokens_b")
        st.session_state.current_settings['top_p_b'] = st.slider("Top P (모델 B)", 0.0, 1.0, st.session_state.current_settings['top_p_b'], key="top_p_b")