import streamlit as st

# 모델 응답을 생성하는 함수
def generate_model_response(model, system_prompt, user_input, temperature, max_tokens):
    # TODO: 실제 모델 API 호출 및 응답 처리 로직 구현
    pass

# 사용자 입력 처리 함수
def process_user_input():
    st.session_state.processed_input = st.session_state.user_input

# 메인 페이지
st.title("Chatbot Arena")
st.write("챗봇 아레나 방식으로 두 개의 LLM을 비교해보세요.")

# 결과 표시 부분
st.subheader("모델 응답 비교")
if 'processed_input' in st.session_state and st.session_state.processed_input:
    st.write(f"**사용자:** {st.session_state.processed_input}")
    
    col1, col2 = st.columns(2)
    with col1:
        response_a = generate_model_response(st.session_state.get('model_a', '모델 A'), 
                                             st.session_state.get('system_prompt', ''), 
                                             st.session_state.processed_input, 
                                             st.session_state.get('temperature_a', 0.7), 
                                             st.session_state.get('max_tokens_a', 256))
        st.markdown(f"""
        <div style="border:1px solid #ddd; padding:10px; border-radius:5px;">
            <h4 style="margin-top:0;">{st.session_state.get('model_a', '모델 A')}</h4>
            <p>{response_a or '모델 A의 응답이 여기에 표시됩니다.'}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        response_b = generate_model_response(st.session_state.get('model_b', '모델 B'), 
                                             st.session_state.get('system_prompt', ''), 
                                             st.session_state.processed_input, 
                                             st.session_state.get('temperature_b', 0.7), 
                                             st.session_state.get('max_tokens_b', 256))
        st.markdown(f"""
        <div style="border:1px solid #ddd; padding:10px; border-radius:5px;">
            <h4 style="margin-top:0;">{st.session_state.get('model_b', '모델 B')}</h4>
            <p>{response_b or '모델 B의 응답이 여기에 표시됩니다.'}</p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.write("아직 사용자 입력이 없습니다.")

# 사이드바
st.sidebar.title("설정 및 입력")

# 탭 생성
tab1, tab2 = st.sidebar.tabs(["채팅 인터페이스", "모델 설정"])

# 채팅 인터페이스 탭
with tab1:
    system_prompt = st.text_area("시스템 프롬프트", value="당신은 도움이 되는 AI입니다.", key="system_prompt")
    user_input = st.text_input("사용자 입력", key="user_input", on_change=process_user_input)

    # 대화 처리
    if st.button("전송"):
        if st.session_state.user_input:
            process_user_input()
        else:
            st.write("사용자 입력을 입력해주세요.")

# 모델 설정 탭
with tab2:
    st.subheader("모델 A 설정")
    model_a = st.selectbox("모델 A 선택", ("gpt-3.5-turbo", "gpt-4o-mini", "ClovaX"), key="model_a")
    temperature_a = st.slider("Temperature (모델 A)", 0.0, 1.0, 0.7, key="temperature_a")
    max_tokens_a = st.slider("Max Tokens (모델 A)", 50, 1024, 256, key="max_tokens_a")

    st.subheader("모델 B 설정")
    model_b = st.selectbox("모델 B 선택", ("gpt-3.5-turbo", "gpt-4o-mini", "ClovaX"), key="model_b")
    temperature_b = st.slider("Temperature (모델 B)", 0.0, 1.0, 0.7, key="temperature_b")
    max_tokens_b = st.slider("Max Tokens (모델 B)", 50, 1024, 256, key="max_tokens_b")