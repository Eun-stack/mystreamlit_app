import stanza
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from io import BytesIO

#streamlit run nlp_analysis_app.py


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
    "case" : "격",
    "obl" :"부사",
    "obj" : "목적어",
    "aux": "보조 동사",
    "det":"한정사",
    "advmod":"형용사/부사의 수식",
    "nummod":"수사",
    "nmod" :"명사의 명사 수식",
    "nsubj":"주어",
    "compound:prt":"구성요소",
    "fixed":"정관사 + 명사",
    "root":"핵심 동사",
    "amod":"형용사의 명사 수식",
    "cc" :"등위접속사",
    "conj":"병렬 구조의 두 번째 이후 요소",
    "punct":"구두점",
    "parataxis":"병렬 관계",
    "appos":"동격 관계",
    "xcomp" :"열린 보어",
    "cop" : "연결 동사",
    "flat" : "구성 요소",
    "obl:arg" : "외적 인수",
    "mark" : "절 시작 표지",
    "advcl" : "부사절",
    "csubj" : "절 주어",
    "aux:pass" : "수동태 보조 동사",
    "nmod" : "소유격 명사 수식어",
    "nsujb:pass" : "수동태 주어",
    "acl" : "형용사절",
    "nmod:poss": "소유 명사 수식어",
    "acl:relcl": "관계절",
    "ccomp" : "절 형태 보어"
}

# NER (명명된 개체 인식) 매핑
NER_match = {
    "LOC" : "장소",
    "GPE" : "국가, 도시",
    "PER" : "사람[의 이름]",
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
    "EMAIL" : "이메일주소",
    "MISC" : "기타"

}

# Streamlit 페이지 설정
st.set_page_config(page_title="네덜란드어 문장 분석기", layout="wide")
st.title("네덜란드어 문장 분석기")

# 사용자가 문장 입력
user_input = st.text_area("분석할 네덜란드어 문장을 입력한 후 Ctrl+Enter로 실행하세요. 여러 문장을 한 번에 분석할 수 있지만, 시간이 소요됩니다.", height=200)

# 입력이 있으면 분석
if user_input:
    with st.spinner("문장을 분석 중입니다..."):
        # 텍스트 분석
        doc = nlp(user_input)

        # 문장 단위로 테이블 출력
        for i, sentence in enumerate(doc.sentences, start=1):
            sentence_data = []
            for word in sentence.words:
                head_word = sentence.words[word.head - 1].text if word.head > 0 else 'ROOT'
                sentence_data.append([
                    word.text,
                    word.lemma,
                    POS_match.get(word.pos, word.pos),
                    word.pos,
                    head_word,
                    deprel_match.get(word.deprel, word.deprel),
                    word.deprel
                ])

            if sentence_data:
                st.subheader(f"문장 {i}: {sentence.text}")
                df = pd.DataFrame(
                    sentence_data,
                    columns=["단어", "표제어", "품사", "품사 코드", "헤드 단어", "의존 관계", "의존 관계 코드"]
                )
                st.dataframe(df)
        
         # 명명된 개체 인식 (NER) 부분 데이터 처리
        ner_data = []
        for sentence in doc.sentences:
            for ent in sentence.ents:
                ner_data.append([ent.text, NER_match.get(ent.type, ent.type), ent.type])  # 엔티티, 라벨, 코드

        # 명명된 개체 인식 표 출력
        if ner_data:
            st.subheader("명명된 개체 인식 (NER)")
            ner_df = pd.DataFrame(ner_data, columns=["엔티티", "라벨", "코드"])
            st.dataframe(ner_df)


# 설명 추가
st.markdown("""

            
            

### 언어 분석 모델: stanza
- **의존 구문 분석** : 문장에서 각 성분이 어떤 의존 관계를 이루는지 분석하는 학문
- **명명된 개체 인식(NER)** : 문장에서 사람, 장소, 날짜 등 중요한 정보를 추론하여 분류
    - 헤드 단어(Head Word) : 다른 단어들이 의존하는 중심 단어
""")
