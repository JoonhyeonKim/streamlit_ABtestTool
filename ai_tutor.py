import streamlit as st
import pyaudio
import wave
import numpy as np
from openai import OpenAI
import os
import tempfile
import time

# OpenAI API 키 설정
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 오디오 설정
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5  # 녹음 시간

st.title("AI 튜터 - 음성 대화 시스템")

# 세션 상태 초기화
if "conversation" not in st.session_state:
    st.session_state.conversation = []

# 녹음 함수
def record_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    st.write("녹음 중...")
    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    st.write("녹음 완료")

    stream.stop_stream()
    stream.close()
    p.terminate()

    return frames

# AI 응답 생성 함수
def generate_ai_response(conversation_history, system_prompt):
    messages = [{"role": "system", "content": system_prompt}] + conversation_history
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return response.choices[0].message.content

# 시스템 프롬프트 입력
assistant_prompt = st.text_area("AI 어시스턴트의 시스템 프롬프트를 입력하세요:", value="당신은 도움이 되는 AI 어시스턴트입니다.")
user_prompt = st.text_area("AI 사용자의 시스템 프롬프트를 입력하세요:", value="당신은 AI 어시스턴트와 대화하는 초등학생입니다. 이전 대화를 바탕으로 적절한 질문이나 응답을 해주세요.")

# 대화 턴 수 설정
max_turns = st.number_input("대화 턴 수를 설정하세요:", min_value=1, max_value=10, value=5)

# 음성 인식 버튼
if st.button("대화 시작"):
    frames = record_audio()

    # WAV 파일로 저장
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        wf = wave.open(temp_wav.name, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # OpenAI API를 사용하여 음성을 텍스트로 변환
        with open(temp_wav.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )

    user_input = transcript.text
    st.write(f"사용자 (음성 인식): {user_input}")
    st.session_state.conversation.append({"role": "user", "content": user_input})

    # 대화 진행
    for i in range(max_turns):
        # AI 1 (어시스턴트) 응답 생성
        ai_response = generate_ai_response(st.session_state.conversation, assistant_prompt)
        st.write(f"AI 어시스턴트: {ai_response}")
        st.session_state.conversation.append({"role": "assistant", "content": ai_response})

        # AI 2 (사용자 역할) 응답 생성
        user_response = generate_ai_response(st.session_state.conversation, user_prompt)
        st.write(f"AI 사용자: {user_response}")
        st.session_state.conversation.append({"role": "user", "content": user_response})

        time.sleep(2)

    # 임시 파일 삭제
    os.unlink(temp_wav.name)

# 대화 기록 표시
st.subheader("대화 기록")
for message in st.session_state.conversation:
    if message["role"] == "user":
        st.text_area("사용자:", value=message["content"], height=100, disabled=True)
    else:
        st.text_area("AI:", value=message["content"], height=100, disabled=True)