import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import re

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="기타 코드 운지법 가이드",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e0e7ff;
        border-left: 4px solid #6366f1;
    }
    .assistant-message {
        background-color: #f0fdf4;
        border-left: 4px solid #10b981;
    }
    .chord-diagram {
        font-family: 'Courier New', monospace;
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1.5rem;
        border-radius: 0.5rem;
        font-size: 0.9rem;
        overflow-x: auto;
        white-space: pre;
    }
    .info-box {
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .sidebar-chord {
        background-color: #f8fafc;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid #e2e8f0;
    }
    .sidebar-chord:hover {
        background-color: #e0e7ff;
        border-color: #6366f1;
    }
    .finger-legend {
        background-color: #fef3c7;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Azure OpenAI 클라이언트 초기화
@st.cache_resource
def init_azure_client():
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2024-02-15-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

client = init_azure_client()
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")

# 시스템 프롬프트
SYSTEM_PROMPT = """당신은 기타 교육 전문 AI입니다. 사용자가 코드명을 입력하면 다음을 제공합니다:

1. **ASCII 코드 다이어그램**: 프렛보드 형태로 운지법 시각화
2. **운지법 설명**: 어떤 손가락으로 어떤 줄의 몇 번째 프렛을 누르는지 상세 설명
3. **연주 팁**: 코드 전환 방법, 주의사항, 변형 코드 등

코드 다이어그램 형식:
```
코드명: C Major
e|---0---
B|---1---
G|---0---
D|---2---
A|---3---
E|---x---

● = 검지 (1)
● = 중지 (2)
● = 약지 (3)
● = 소지 (4)
x = 뮤트 (누르지 않음)
0 = 개방현
```

**중요**: 
- 정확한 프렛 번호 제공
- 일반적으로 사용되는 포지션 우선
- 바레코드의 경우 명시적으로 설명
- 6줄(E) → 1줄(e) 순서로 표기

다양한 코드를 지원합니다:
- 메이저/마이너 (C, Cm, D, Dm 등)
- 세븐스 (G7, Am7, Cmaj7 등)
- 파워코드 (C5, D5 등)
- 디미니시/증화음 (Cdim, Caug 등)
- 서스펜디드 (Csus2, Csus4 등)"""

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 사이드바
with st.sidebar:
    st.markdown("### 🎸 기타 코드 가이드")
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("**빠른 코드 검색**")
    st.markdown("아래 버튼을 클릭하거나<br>직접 코드명을 입력하세요!", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("**기본 코드**")
    basic_chords = ["C", "D", "E", "F", "G", "A", "Am", "Dm", "Em"]
    
    cols = st.columns(3)
    for idx, chord in enumerate(basic_chords):
        with cols[idx % 3]:
            if st.button(chord, use_container_width=True, key=f"basic_{chord}"):
                st.session_state.selected_chord = chord
    
    st.markdown("---")
    st.markdown("**세븐스 코드**")
    seventh_chords = ["C7", "G7", "D7", "A7", "E7", "Am7"]
    
    cols2 = st.columns(3)
    for idx, chord in enumerate(seventh_chords):
        with cols2[idx % 3]:
            if st.button(chord, use_container_width=True, key=f"seventh_{chord}"):
                st.session_state.selected_chord = chord
    
    st.markdown("---")
    st.markdown("**기타 코드**")
    other_chords = ["Cmaj7", "Fmaj7", "Bm", "F#m", "Cadd9"]
    
    cols3 = st.columns(3)
    for idx, chord in enumerate(other_chords):
        with cols3[idx % 3]:
            if st.button(chord, use_container_width=True, key=f"other_{chord}"):
                st.session_state.selected_chord = chord
    
    st.markdown("---")
    
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # 손가락 번호 안내
    st.markdown("""
    <div class="finger-legend">
        <strong>🖐️ 손가락 번호</strong><br>
        1️⃣ 검지 (Index)<br>
        2️⃣ 중지 (Middle)<br>
        3️⃣ 약지 (Ring)<br>
        4️⃣ 소지 (Pinky)<br>
        T 엄지 (Thumb)
    </div>
    """, unsafe_allow_html=True)

# 메인 영역
st.markdown('<div class="main-header">🎸 기타 코드 운지법 가이드</div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    <strong>💡 사용 방법</strong><br>
    • 아래 입력창에 코드명을 입력하세요 (예: C, Am, G7, Fmaj7)<br>
    • 왼쪽 사이드바의 버튼을 클릭해도 됩니다<br>
    • 여러 코드를 연속으로 물어볼 수 있습니다
</div>
""", unsafe_allow_html=True)

# 채팅 기록 표시
for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    
    if role == "user":
        st.markdown(f'<div class="chat-message user-message"><strong>🎵 질문:</strong><br>{content}</div>', 
                   unsafe_allow_html=True)
    else:
        # 코드 다이어그램 부분 추출 및 스타일링
        if "```" in content:
            parts = content.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 0:  # 일반 텍스트
                    st.markdown(f'<div class="chat-message assistant-message"><strong>🎸 답변:</strong><br>{part}</div>', 
                               unsafe_allow_html=True)
                else:  # 코드 블록
                    st.markdown(f'<div class="chord-diagram">{part}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message"><strong>🎸 답변:</strong><br>{content}</div>', 
                       unsafe_allow_html=True)

# 사이드바 버튼으로 선택된 코드 처리
if "selected_chord" in st.session_state:
    user_input = f"{st.session_state.selected_chord} 코드 알려줘"
    del st.session_state.selected_chord
else:
    user_input = None

# 채팅 입력
if prompt := st.chat_input("코드명을 입력하세요 (예: C, Am, G7, Fmaj7)..."):
    user_input = prompt

# 메시지 처리
if user_input:
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # UI 업데이트
    st.markdown(f'<div class="chat-message user-message"><strong>🎵 질문:</strong><br>{user_input}</div>', 
               unsafe_allow_html=True)
    
    # AI 응답 생성
    with st.spinner("코드 다이어그램을 생성하고 있습니다..."):
        try:
            # API 호출
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(st.session_state.messages)
            
            response = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.3,  # 정확성을 위해 낮은 온도
                max_tokens=2000,
                top_p=0.9
            )
            
            assistant_message = response.choices[0].message.content
            
            # 어시스턴트 메시지 추가
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            
            # 응답 표시 (코드 블록 스타일링)
            if "```" in assistant_message:
                parts = assistant_message.split("```")
                for i, part in enumerate(parts):
                    if i % 2 == 0:  # 일반 텍스트
                        if part.strip():
                            st.markdown(f'<div class="chat-message assistant-message"><strong>🎸 답변:</strong><br>{part}</div>', 
                                       unsafe_allow_html=True)
                    else:  # 코드 블록
                        st.markdown(f'<div class="chord-diagram">{part}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message"><strong>🎸 답변:</strong><br>{assistant_message}</div>', 
                           unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")
            st.info("Azure OpenAI 설정을 확인해주세요:\n1. .env 파일의 API 키\n2. Endpoint URL\n3. Deployment Name")

# 초기 안내 메시지
if len(st.session_state.messages) == 0:
    st.markdown("---")
    st.markdown("""
    ### 🎵 어떤 코드를 알아보고 싶으신가요?
    
    **예시:**
    - "C 코드 알려줘"
    - "Am7 운지법 보여줘"
    - "바레코드 F 어떻게 잡아?"
    - "G7과 Gmaj7 차이점 알려줘"
    - "초보자가 배우기 쉬운 코드 추천해줘"
    
    **추천 학습 순서:**
    1. 기본 오픈 코드: C, G, D, Em, Am
    2. 세븐스 코드: G7, C7, D7
    3. 바레 코드: F, Bm, F#m
    
    왼쪽 사이드바에서 바로 선택할 수도 있습니다! 🎸
    """)
    
    # 샘플 다이어그램 표시
    st.markdown("### 📊 코드 다이어그램 예시")
    st.markdown("""
    <div class="chord-diagram">
C Major 코드:

e|---0---  (1번줄 - 개방현)
B|---1---  (2번줄 - 1프렛, 검지)
G|---0---  (3번줄 - 개방현)
D|---2---  (4번줄 - 2프렛, 중지)
A|---3---  (5번줄 - 3프렛, 약지)
E|---x---  (6번줄 - 뮤트)

손가락 위치:
- 검지(1): 2번줄 1프렛
- 중지(2): 4번줄 2프렛
- 약지(3): 5번줄 3프렛
    </div>
    """, unsafe_allow_html=True)

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.9rem;">
    <p>🎸 기타 연습 팁: 매일 조금씩, 천천히 정확하게!</p>
    <p>💪 코드 전환이 어렵다면 메트로놈을 느린 템포로 설정하고 연습하세요</p>
</div>
""", unsafe_allow_html=True)