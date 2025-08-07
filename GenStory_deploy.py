# 필요한 라이브러리 import
import streamlit as st
import google.generativeai as genai
from transformers import BertTokenizer, BertModel
import torch
import os


# 텍스트 파일 저장 함수
def save_text_to_file(text, file_name, save_path):
    # 저장할 디렉터리가 존재하지 않으면 생성
    os.makedirs(save_path, exist_ok=True)
    
    # 파일 경로 생성
    file_path = os.path.join(save_path, file_name)
    
    # 파일이 존재하면 덮어쓰고, 존재하지 않으면 새로 생성
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(text)
    
    return file_path


# 페이지 설정
st.set_page_config(page_title="소설 프롤로그 생성기", layout="centered")

# 사이드바 메뉴
st.sidebar.title("📚 메뉴")
menu = st.sidebar.radio("이동할 화면을 선택하세요", ["초기 세팅", "히스토리 확인"])

# Gemini API Key 입력
gemini_api_key = st.sidebar.text_input(
    "🔑 Gemini API Key", 
    type="password", 
    help="Google AI Studio에서 발급받은 API 키를 입력해주세요."
)
model_choice = st.sidebar.selectbox(
    '🧠 사용할 모델:',
    ('gemini-1.5-flash', 'gemini-2.5-flash')
)

# 모델 초기화 (초기 세팅 외부에서 사용할 수 있도록 수정)
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel(model_choice)
    system_prompt = "당신은 초인기 소설 작가입니다."
else:
    model = None


# 세션 상태 초기화
if True:
    defaults = {
        'history': [],
        'novel_genre': [],
        'background_time': [],
        'background_space': [],
        'background_social': [],
        'literary_style': [],
        'theme': [],
        'main_character_background': [],
        'main_character_appearance': [],
        'main_character_ability': [],
        'main_character_superpower': [],
        'main_character_personality': [],
        'main_character_relationship': []
    }

    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

# BERT 임베딩 생성 함수
def get_bert_embedding(text):
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True)
    with torch.no_grad():
        outputs = bert_model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()  # 텍스트의 평균 벡터



# =============================
# 화면 1: 초기 세팅 및 생성 기능
# =============================
if menu == "초기 세팅":
    st.title("📖 AI 소설 프롤로그 생성기")
    st.markdown("---")

    # 메타데이터 입력
    with st.expander("메타데이터"):
        st.session_state['perspective'] = st.selectbox(
            "시점 선택",
            ["1인칭 주인공 시점", "1인칭 관찰자 시점", "3인칭 관찰자 시점", "전지적 작가 시점"],
            index=0
        )

        st.session_state['novel_genre'] = st.multiselect(
            "장르 선택 (다중 선택 가능):",
            ["현실주의", "로맨스", "과학", "판타지", "추리", "공포", "역사", "디스토피아", "모험", "게임", "전쟁", "오컬트"],
            default=st.session_state['novel_genre']
        )

        st.session_state['literary_style'] = st.multiselect(
            "문체 (다중 선택 가능):",
            ["격식", "비격식", "서술성", "대화성", "서정적", "시적", "회화적", "극적"],
            default=st.session_state['literary_style']
        )

        st.session_state['theme'] = st.multiselect(
            "주제 (다중 선택 가능):",
            ["사랑", "정체성", "사회비판", "존재", "자유", "선악", "죽음", "인간성", "자연", "운명", "가족", "희생", "희망", "환상", "기억", "기술찬양"],
            default=st.session_state['theme']
        )

    # 세계관 설정
    with st.expander("세계관"):
        st.session_state['background_time'] = st.multiselect(
            "시간적 배경 (다중 선택 가능)",
            ["고대 이집트", "고대 그리스", "고대 로마", "중세유럽", "르네상스 시대", "조선시대", "대항해 시대", 
             "근대", "제1차 세계대전", "제2차 세계대전", "현대", "미래", "가상 현실"],
            default=st.session_state['background_time']
        )

        st.session_state['background_space'] = st.multiselect(
            "공간적 배경 (다중 선택 가능)",
            ["우주", "행성", "국가", "도시", "마을", "산", "해안", "심해", "하늘", "지하", "사막", "숲", 
             "극지방", "고대 유적지", "판타지세계"],
            default=st.session_state['background_space']
        )

        st.session_state['background_social'] = st.multiselect(
            "사회적 환경 (다중 선택 가능)",
            ["독재", "민주주의", "공산주의", "계몽주의", "제국주의", "전쟁", "자본주의", "공동체주의", 
             "유토피아", "디스토피아", "반과학주의", "종교", "환경", "아포칼립스", "인류멸망"],
            default=st.session_state['background_social']
        )

    # 주인공 설정
    with st.expander("주인공 설정"):
        name = st.text_input("이름을 입력하세요")
        age = st.number_input("나이를 입력하세요", min_value=0, max_value=100)
        job = st.text_input("직업을 입력하세요")
        gender = st.selectbox("성별을 선택하세요", ["남성", "여성","선택하지 않음"])

        st.session_state['main_character_background'] = st.multiselect(
            "주인공 배경 (다중 선택 가능)",
            ["부모없음", "조부모", "학교폭력", "가정폭력", "연인과헤어짐", "부유함", "평범함", 
             "고아원", "이민", "빈곤", "귀족", "평안한 가족", "범죄"],
            default=st.session_state['main_character_background']
        )

        st.session_state['main_character_appearance'] = st.multiselect(
            "외모 (다중 선택 가능)",
            ["장발", "단발", "금발", "흑발", "장신", "단신", "안경", "노인", "장년", "청년", 
             "청소년", "미성년", "유아", "영아"],
            default=st.session_state['main_character_appearance']
        )

        st.session_state['main_character_ability'] = st.multiselect(
            "능력 (다중 선택 가능)",
            ["힘이 셈", "힘이 약함", "머리가 좋음", "머리가 나쁨", "손재주가 좋음", "손재주가 나쁨", 
             "빠름", "느림", "기억력이 좋음", "잘 잊어버림", "말재주가 좋음", "말재주가 나쁨", 
             "기계를 잘 다룸", "기계치"],
            default=st.session_state['main_character_ability']
        )

        st.session_state['main_character_superpower'] = st.multiselect(
            "초능력 (다중 선택 가능)",
            ["물", "불", "번개", "어둠", "바람", "땅", "빛", "부활", "초스피드", "초감각", "힘", 
             "정신조작", "소환수", "순간이동", "검술", "기", "에너지조작", "비행"],
            default=st.session_state['main_character_superpower']
        )

        st.session_state['main_character_personality'] = st.multiselect(
            "성격 (다중 선택 가능)",
            ["소심한", "대담한", "말이 많은", "말이 적은", "적극적인", "소극적인", "낙천적인", "비판적인", 
             "자기중심적인", "이타적인", "온화한", "고집이 센", "완벽주의의", "의존적인", "상냥한", 
             "두려움이 많은", "모험적인", "포용하는", "둔한", "민감한", "냉혹한", "밝은", "배려하는"],
            default=st.session_state['main_character_personality']
        )

        st.session_state['main_character_relationship'] = st.multiselect(
            "주변 관계 (다중 선택 가능)",
            ["부모", "형제", "친구", "악당", "조력자", "스승", "제자", "배우자", "연인"],
            default=st.session_state['main_character_relationship']
        )
    user_prompt_to_llm = f"""당신은 초인기 소설 작가입니다.
                다음 정보를 기반으로 2500자 이내의 소설 {len(st.session_state['history'])+1}화를 작성해주세요.
            

                1. 시점: {st.session_state['perspective']}
                2. 장르: {", ".join(st.session_state['novel_genre'])}
                3. 문체: {", ".join(st.session_state['literary_style'])}
                4. 주제: {", ".join(st.session_state['theme'])}
                5. 시간적 배경: {", ".join(st.session_state['background_time'])}
                6. 공간적 배경: {", ".join(st.session_state['background_space'])}
                7. 사회적 환경: {", ".join(st.session_state['background_social'])}
                8. 주인공 이름: {name}, 나이: {age}, 성별: {gender}, 직업: {job}
                9. 주인공 배경: {", ".join(st.session_state['main_character_background'])}
                10. 주인공 외모: {", ".join(st.session_state['main_character_appearance'])}
                11. 주인공 능력: {", ".join(st.session_state['main_character_ability'])}
                12. 주인공 초능력: {", ".join(st.session_state['main_character_superpower'])}
                13. 주인공 성격: {", ".join(st.session_state['main_character_personality'])}
                14. 주인공 주변 관계: {", ".join(st.session_state['main_character_relationship'])}
                """

    # 프롤로그 생성 버튼
    if st.button(f"소설 {len(st.session_state['history'])+1}화 생성하기 ✨"):
        if not gemini_api_key:
            st.error("⚠️ Gemini API 키가 설정되지 않아 소설을 생성할 수 없습니다.")
        else:
            with st.spinner("소설 생성 중입니다... 잠시만 기다려주세요."):
                try:
                    # 모든 이전 회차 내용을 결합
                    previous_content = "\n\n".join(st.session_state['history']) if st.session_state['history'] else ""
                    
                    # 새로운 프롬프트 생성
                    full_prompt_for_this_turn = f"""
                    당신은 초인기 소설 작가입니다.

                    다음 정보를 바탕으로 **바로 직전의 내용에 이어서** 소설 {len(st.session_state['history'])+1}화를 작성해주세요.
                    이전 회차의 내용을 참고하여 스토리가 자연스럽게 이어지도록 해주세요.

                    {previous_content}

                    다음은 소설의 기본 설정입니다.
                    1. 시점: {st.session_state['perspective']}
                    2. 장르: {", ".join(st.session_state['novel_genre'])}
                    3. 문체: {", ".join(st.session_state['literary_style'])}
                    4. 주제: {", ".join(st.session_state['theme'])}
                    5. 시간적 배경: {", ".join(st.session_state['background_time'])}
                    6. 공간적 배경: {", ".join(st.session_state['background_space'])}
                    7. 사회적 환경: {", ".join(st.session_state['background_social'])}
                    8. 주인공 이름: {name}, 나이: {age}, 성별: {gender}, 직업: {job}
                    9. 주인공 배경: {", ".join(st.session_state['main_character_background'])}
                    10. 주인공 외모: {", ".join(st.session_state['main_character_appearance'])}
                    11. 주인공 능력: {", ".join(st.session_state['main_character_ability'])}
                    12. 주인공 초능력: {", ".join(st.session_state['main_character_superpower'])}
                    13. 주인공 성격: {", ".join(st.session_state['main_character_personality'])}
                    14. 주인공 주변 관계: {", ".join(st.session_state['main_character_relationship'])}
                    """
                    
                    # 모델에 프롬프트 요청
                    response = model.generate_content([system_prompt, full_prompt_for_this_turn])
                    result_text = response.text

                    # 생성된 소설을 세션 상태에 추가
                    st.session_state['history'].append(result_text)

                    # 텍스트 파일로 저장
                    save_path = "./MygreatNovel"
                    file_name = f"chapter_00{len(st.session_state['history'])}.txt"
                    try:
                        file_path = save_text_to_file(result_text, file_name, save_path)
                        st.success(f"소설 {len(st.session_state['history'])}화가 {file_path}에 저장되었습니다.")
                    except Exception as e:
                        st.error(f"⚠️ 파일 저장 중 오류가 발생했습니다: {e}")

                    # 생성된 소설 결과 출력
                    st.markdown("---")
                    st.subheader(f"📘 생성된 소설 ({len(st.session_state['history'])}화)")
                    st.write(result_text)

                except Exception as e:
                    st.error(f"⚠️ 소설 생성 중 오류가 발생했습니다: {e}")


        
# =============================
# 화면 2: 히스토리 확인
# =============================
elif menu == "히스토리 확인":
    st.title("📜 생성된 히스토리")

    if not st.session_state['history']:
        st.info("아직 생성된 내용이 없습니다.")
    else:
        st.markdown("### 📂 생성된 회차 목록")
        for idx, entry in enumerate(st.session_state['history'], start=1):
            if st.button(f"{idx:02d}화 보기"):
                st.markdown(f"#### ✨ {idx:02d}화")
                st.write(entry)

