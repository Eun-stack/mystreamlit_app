import streamlit as st
import requests
import json
import os # os 모듈 임포트
from dotenv import load_dotenv # dotenv 라이브러리 임포트

# .env 파일에서 환경 변수 로드
load_dotenv()

# Streamlit 앱의 기본 설정
st.set_page_config(page_title="AI 소설 프롤로그 생성기", layout="centered")

# 세션 상태 초기화 (앱이 다시 로드될 때 값 유지)
# multiselect를 위해 기본값을 리스트로 설정
if 'novel_genre' not in st.session_state:
    st.session_state['novel_genre'] = ["판타지"]
if 'novel_background' not in st.session_state:
    st.session_state['novel_background'] = ["현대"]
if 'hero_character' not in st.session_state:
    st.session_state['hero_character'] = ["냉혹"]
if 'hero_appearance' not in st.session_state:
    st.session_state['hero_appearance'] = ["미남"]
if 'hero_state' not in st.session_state: # 주인공 상태
    st.session_state['hero_state'] = ["유일한 친구로부터 배신받음"]
if 'hero_surrounding_relationship' not in st.session_state: # 주인공 주변 관계
    st.session_state['hero_surrounding_relationship'] = ["형제 존재"]
if 'hero_ability' not in st.session_state:
    st.session_state['hero_ability'] = ["제작 장인"]

# 앱 제목 및 설명
st.title("📖 AI 소설 프롤로그 생성기")
st.markdown("---")
st.write("이 앱은 Gemini API를 사용하여 사용자가 제공한 정보를 바탕으로 소설 프롤로그를 생성합니다.")

# Gemini API 키를 환경 변수에서 직접 로드
gemini_api_key = os.getenv('GEMINI_API_KEY')

# API 키가 설정되지 않았을 경우 경고 메시지 표시
if not gemini_api_key:
    st.warning("⚠️ **경고:** `GEMINI_API_KEY` 환경 변수가 설정되지 않았습니다. `.env` 파일에 키를 추가하거나 시스템 환경 변수로 설정해주세요.")
st.markdown("---")

# 2. 소설 프롤로그 정보 설정 섹션 (Expander 사용)
st.subheader("2. 소설 프롤로그 정보 설정")
with st.expander("⚙️ 설정 (필수 사항)", expanded=True): # 기본적으로 펼쳐진 상태로 설정
    st.session_state['novel_genre'] = st.multiselect( # multiselect로 변경
        "장르 선택 (다중 선택 가능):",
        ["판타지", "무협", "로맨스", "회귀물"],
        default=st.session_state['novel_genre'] # default 파라미터 사용
    )

    st.session_state['novel_background'] = st.multiselect( # multiselect로 변경
        "세계관(배경) 선택 (다중 선택 가능):",
        ["현대", "고대 중국", "서양 왕정"],
        default=st.session_state['novel_background'] # default 파라メーター 사용
    )

    st.session_state['hero_character'] = st.multiselect( # multiselect로 변경
        "주인공 성격 선택 (다중 선택 가능):",
        ["냉혹", "포용", "밝음", "배려"],
        default=st.session_state['hero_character'] # default 파라미터 사용
    )

    st.session_state['hero_appearance'] = st.multiselect( # multiselect로 변경
        "주인공 외모 선택 (다중 선택 가능):",
        ["미남", "미녀", "추남", "추녀"],
        default=st.session_state['hero_appearance'] # default 파라미터 사용
    )

    st.session_state['hero_state'] = st.multiselect( # multiselect로 변경
        "주인공 상태 선택 (다중 선택 가능):",
        ["유일한 친구로부터 배신받음", "무일푼", "가족과 불화", "사회적 성공"],
        default=st.session_state['hero_state'] # default 파라미터 사용
    )

    st.session_state['hero_surrounding_relationship'] = st.multiselect( # multiselect로 변경
        "주인공 주변 관계 선택 (다중 선택 가능):",
        ["부모 동거", "형제 존재", "친구 없음", "연인 존재"],
        default=st.session_state['hero_surrounding_relationship'] # default 파라미터 사용
    )

    st.session_state['hero_ability'] = st.multiselect( # multiselect로 변경
        "주인공 능력 선택 (다중 선택 가능):",
        ["제작 장인", "네크로맨서", "격투 장인", "불운", "마법사"],
        default=st.session_state['hero_ability'] # default 파라미터 사용
    )
st.markdown("---")

# Gemini API 호출 함수 정의
def call_gemini_api(prompt_text: str, api_key: str) -> str:
    """
    Gemini API를 호출하여 텍스트를 생성하는 함수.
    """
    if not api_key:
        return "오류: Gemini API 키가 입력되지 않았습니다."

    # Gemini API 엔드포인트 URL 및 모델 설정 (예시: gemini-2.5-flash-preview-05-20)
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        result = response.json()

        if result and result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
            return generated_text
        else:
            return f"오류: API 응답에서 생성된 텍스트를 찾을 수 없습니다. 응답: {json.dumps(result, indent=2)}"

    except requests.exceptions.RequestException as e:
        return f"API 호출 중 네트워크 또는 HTTP 오류가 발생했습니다: {e}"
    except json.JSONDecodeError:
        return "오류: API 응답을 JSON으로 디코딩하는 데 실패했습니다. 응답 형식을 확인하세요."
    except Exception as e:
        return f"예상치 못한 오류가 발생했습니다: {e}"

# 3. 소설 생성 버튼 및 결과 표시 섹션
if st.button("소설 프롤로그 생성하기 ✨"):
    if not gemini_api_key:
        st.error("⚠️ Gemini API 키가 설정되지 않아 프롤로그를 생성할 수 없습니다.")
    else:
        # 선택된 설정들을 바탕으로 프롬프트 구성
        # multiselect의 결과는 리스트이므로, join을 사용하여 문자열로 변환
        user_prompt_to_llm = f"""내가 정보를 줄건데, 정보를 토대로 3500자 내 소설 프롤로그 1화 작성해줘

1. 장르 : {", ".join(st.session_state['novel_genre'])}
2. 세계관(배경) : {", ".join(st.session_state['novel_background'])}
3. 주인공 성격 : {", ".join(st.session_state['hero_character'])}
4. 주인공 외모 : {", ".join(st.session_state['hero_appearance'])}
5. 주인공 상태 : {", ".join(st.session_state['hero_state'])}
6. 주인공 주변 관계 : {", ".join(st.session_state['hero_surrounding_relationship'])}
7. 주인공 능력 : {", ".join(st.session_state['hero_ability'])}
"""
        # 로딩 스피너 표시
        with st.spinner("프롤로그를 생성 중입니다... 잠시만 기다려주세요."):
            generated_prologue = call_gemini_api(user_prompt_to_llm, gemini_api_key)
            st.markdown("---")
            st.subheader("3. 생성된 소설 프롤로그")
            st.write(generated_prologue)

# 앱 하단 정보
st.markdown("---")