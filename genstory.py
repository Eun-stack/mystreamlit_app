import streamlit as st
import google.generativeai as genai



# Google Gemini API 키 입력란
gemini_api_key = st.text_input("Gemini API Key를 입력하세요", type="password")


model_choice = st.selectbox(
    '사용할 모델을 선택하세요:',
    ('gemini-2.5-flash', 'gemini-2.5-flash')  # 예시로 3가지 모델을 추가
)


# 응답 히스토리 추적
if "history" not in st.session_state:
    st.session_state.history = []  # 히스토리가 없으면 초기화


if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel(model_choice)


# 선택 상자 (Selectbox)
point_of_view = st.selectbox(
    '시점',
    ('1인칭 주인공 시점', '1인칭 관찰자 시점', '3인칭 관찰자 시점', '전지적 작가 시점')
)

st.markdown('''**장르**
현실주의, 로맨스, 과학, 판타지, 추리, 공포, 역사, 디스토피아, 모험
''')

genre = st.text_input("소설의 장르를 입력하세요. :")

st.markdown('''**시간적 배경**
            시대: 고대, 중세, 근대, 현대, 근미래, 미래  
            시대상: 계몽주의, 제국주의, 전쟁, 아포칼립스(화생방, 지구멸망, 좀비...)  
            ''')
background_era = st.text_input("시간적 배경을 입력하세요.: ")

st.markdown('''**공간적 배경**
            범위: 우주, 행성, 국가, 도시, 마을  
            자연환경: 우주, 산, 바다, 도시, 판타지세계, 특정 장소
            ''')
background_place = st.text_input("공간적 배경을 입력하세요.: ")
st.markdown('''**사회적 환경**
            아포칼립스, 독재, 민주주의, 공산주의
            ''')
background_society = st.text_input("사회적 환경을 입력하세요.: ")

st.markdown('''**문체**
            격식 또는 비격식
            서술성 또는 대화성
            서정적
            시적 문체, 회화체, 극적 문체
            ''')
literary_style = st.text_input("문체를 입력하세요.: ")

st.markdown('''**주제**
            사랑, 정체성, 사회문제, 존재, 자유, 선악, 죽음, 인간성, 자연, 운명, 가족, 희생, 희망, 환상
            ''')
main_theme = st.text_input("주제를 입력하세요. : ")

st.markdown('''**주인공 설정**
이름, 나이, 외모, 성격, 가치관, 주변인물
''')

main_character = st.text_input("주인공 설정을 입력하세요. : ")

st.markdown('''**주변인물**
가족, 친구, 적대세력, 우호세력
''')

sub_character = st.text_input("간단한 설명과 함께 주변 인물 정보를 입력하세요.")

# 선택한 정보 출력
st.write(f"""선택 결과: 
        시점: {point_of_view}  
        장르: {genre}  
        시대적 배경: {background_era}  
        공간적 배경: {background_place}  
        사회적 환경: {background_society}  
        문체: {literary_style}  
        주제: {main_theme}  
        주인공: {main_character}  
        주변인물: {sub_character}""")

n = st.number_input("생성하려는 프롤로그의 길이를 자연수로 입력하세요.: ", min_value=1, step=1)

# 프롤로그 생성 요청을 위한 프로프트 구성
prompt = (
    f'주어진 정보를 바탕으로 {n}자 분량의 소설 프롤로그를 작성해줘'
    f"""선택 결과: 
        시점: {point_of_view}  
        장르: {genre}  
        시대적 배경: {background_era}  
        공간적 배경: {background_place}  
        사회적 환경: {background_society}  
        문체: {literary_style}  
        주제: {main_theme}  
        주인공: {main_character}  
        주변인물: {sub_character}"""
)

# 이전 응답 히스토리를 포함한 프롬프트 구성
if st.session_state.history:
    prompt = "\n".join(st.session_state.history) + "\n" + prompt

# 결과 초기화
results = ""

# 프롤로그 생성 버튼
if st.button("🚀 프롤로그 생성하기"):
    response = model.generate_content(prompt)
    results = response.text  # 버튼 클릭 후 결과를 저장
    
    # 새로운 결과를 히스토리에 추가
    st.session_state.history.append(f"프롤로그 생성 요청: {prompt}")
    st.session_state.history.append(f"모델 응답: {results}")

# 출력 결과
if results:  # 결과가 있을 경우에만 출력
    st.markdown(f"**출력 결과:**\n\n {results}")

# 히스토리 보기 (디버깅용)
st.write("### 출력 히스토리")
for entry in st.session_state.history:
    st.write(entry)