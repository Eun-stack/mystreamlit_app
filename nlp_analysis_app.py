import stanza
import streamlit as st
import pandas as pd

# 한국어 모델 다운로드 및 파이프라인 설정
nlp = stanza.Pipeline('nl')

# 품사 매핑
POS_match = {
    "ADJ"  : "형용사",
    "ADV"  : "부사",
    "ADP"  : "전치사",
    "AUX"  : "조동사",
    "CCONJ": "접속사",
    "DET"  : "정관사",
    "NUM"  : "숫자",
    "NOUN" : "명사",
    "PRON" : "대명사",
    "PROPN" : "고유명사",
    "PUNCT": "구두점",
    "VERB" : "동사"
}

# 의존 구문 분석 매핑
deprel_match = {
    "case" : "격을 나타냄",
    "obl" :"부사",
    "aux": "보조 동사",
    "det":"한정사",
    "advmod":"형용사나 부사가 다른 단어를 수식",
    "nummod":"수사",
    "nmod" :"명사의 명사 수식",
    "nsubj":"주어",
    "compound:prt":"구성요소",
    "fixed":"정관사와 명사가 고정된 구문 패턴을 이루는 경우",
    "root":"핵심 동사",
    "amod":"형용사의 명사 수식",
    "cc" :"등위접속사",
    "conj":"접속된 명사",
    "punct":"구두점",
    "parataxis":"병렬 관계",
    "appos":"동격 관계"
}

# NER (명명된 개체 인식) 매핑
NER_match = {
    "LOC" : "장소",
    "GPE" : "국가, 도시",
    "PERSON" : "사람[의 이름]",
    "ORG" : "단체",
    "DATE" : "일시",
    "TIME" : "시각",
    "MONEY" : "금액",
    "PERCENT" : "백분율",
    "QUANTITY" : "수량",
    "PRODUCT" : "제품이름",
    "FACILITY" : "건물,시설,장소",
    "WORK_OF_ART" :"예술작품",
    "LAW" : "법령",
    "LANGUAGE" : "언어",
    "NORP" : "국적,종교,정치적집단",
    "EVENT" : "행사",
    "ADDRESS" :"주소",
    "EMAIL" : "이메일주소"
}

# Streamlit 페이지 설정
st.set_page_config(page_title="네덜란드어 문장 분석기", layout="wide")

# 페이지 타이틀
st.title("네덜란드어 문장 분석기")

# 사용자가 문장 입력
user_input = st.text_area("분석할 문장을 입력하세요:", height=200)

# 입력이 있으면 분석
if user_input:
    with st.spinner("문장을 분석 중입니다... 잠시만 기다려 주세요."):
        # 텍스트 분석
        doc = nlp(user_input)

        # 품사 태깅을 위한 데이터프레임
        pos_data = []
        for sentence in doc.sentences:
            for word in sentence.words:
                pos_data.append([word.text, POS_match.get(word.pos, word.pos), word.lemma])

        # 의존 구문 분석을 위한 데이터프레임
        deprel_data = []
        for sentence in doc.sentences:
            for word in sentence.words:
                deprel_data.append([word.text, word.head, deprel_match.get(word.deprel, word.deprel)])

        # NER (명명된 개체 인식) 결과를 위한 데이터프레임
        ner_data = []
        for sentence in doc.sentences:
            for ent in sentence.ents:
                ner_data.append([ent.text, NER_match.get(ent.type, ent.type)])

        # 각 분석 결과를 Streamlit에서 표로 출력
        if pos_data:
            st.subheader("품사 태깅")
            pos_df = pd.DataFrame(pos_data, columns=["단어", "품사", "표제어"])
            st.dataframe(pos_df)

        if deprel_data:
            st.subheader("의존 구문 분석")
            deprel_df = pd.DataFrame(deprel_data, columns=["단어", "헤드", "의존 관계"])
            st.dataframe(deprel_df)

        if ner_data:
            st.subheader("명명된 개체 인식 (NER)")
            ner_df = pd.DataFrame(ner_data, columns=["엔티티", "라벨"])
            st.dataframe(ner_df)

# 추가 설명
st.markdown("""
### 표제어:
- 표제어는 단어의 기본형(사전적 형태)을 의미합니다.
- 예: 'running' -> 'run', 'better' -> 'good'
""")
