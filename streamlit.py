# 필요한 라이브러리 import
import streamlit as st
from dotenv import load_dotenv 
import os
import google.generativeai as genai

load_dotenv()
API_KEY = os.environ.get('GEMINI_API_KEY')

genai.configure(api_key=API_KEY)

st.session_state['novel_genre'] = None
st.session_state['novel_background'] = None
st.session_state['hero'] = None
st.session_state['math_grade'] = None
st.session_state['english_grade'] = None

if 'novel_genre' not in st.session_state :
    st.session_state['novel_genre'] = None
if 'novel_background' not in st.session_state :
   st.session_state['novel_background'] = None
if 'hero' not in st.session_state :
   st.session_state['hero'] = None
if 'math_grade' not in st.session_state :
    st.session_state['math_grade'] = None
if 'english_grade' not in st.session_state :
    st.session_state['english_grade'] = None

st.set_page_config(page_title="소설 프롤로그 생성기", layout="centered")
st.title("📖 AI 소설 프롤로그 생성기")
st.markdown("---")

# Gemini API 키 입력 필드
st.subheader("1. Gemini API 키 입력")
gemini_api_key = st.text_input(
    "여기에 Gemini API 키를 입력하세요:",
    type="password", # API 키는 보안을 위해 비밀번호처럼 가려지게 합니다.
    help="Google AI Studio에서 발급받은 API 키를 입력해주세요."
)
st.markdown("---")

with st.expander("⚙️ 설정 (필수 사항)"):
    novel_genre = st.selectbox(
        "장르 선택:",
        [ "판타지", "무협", "로맨스", "회귀물" ],
        index=0
    )
    st.session_state['novel_genre'] = novel_genre
    
    novel_background = st.selectbox(
        "세계관(배경) 선택:",
        [ "현대", "고대 중국", "서양 왕정" ],
        index=0
    )
    st.session_state['novel_background'] = novel_background

    hero_character = st.selectbox(
        "주인공 성격 선택:",
        [ "냉혹", "포용", "밝음", "배려" ],
        index=0
    )
    st.session_state['hero_character'] = hero_character

    hero_appearance = st.selectbox(
        "주인공 외모 선택:",
        ["미남", "미녀", "추남", "추녀"],
        index=0
    )
    st.session_state['hero_appearance'] = hero_appearance

    hero_relationship = st.selectbox(
        "주인공 상태 선택:",
        [ "유일한 친구로부터 배신받음", "무일푼" ],
        index=0
    )
    st.session_state['hero_relationship'] = hero_relationship

    hero_relationship = st.selectbox(
        "주인공 주변 관계 선택:",
        [ "부모 동거", "형제 존재", "친구 없음" ],
        index=0
    )
    st.session_state['hero_relationship'] = hero_relationship

    hero_ability = st.selectbox(
        "주인공 능력 선택:",
        ["제작 장인", "네크로맨서", "격투 장인", "불운"],
        index=0
    )
    st.session_state['hero_ability'] = hero_ability

model = genai.GenerativeModel('gemini-2.5-flash')
system_prompt = "당신은 초인기 판타지 소설 작가입니다."

chat = model.start_chat(history=[])

response = model.generate_content([
    system_prompt,
    st.session_state.pdf_file,
    prompt
])






# 텍스트 출력
st.write("안녕하세요!")

# 버튼 추가
if st.button("클릭해보세요"):
    st.write("버튼이 눌렸네요!")

# 사이드바 추가
st.sidebar.header("사이드바")
st.sidebar.text("여기는 사이드바 영역입니다.")