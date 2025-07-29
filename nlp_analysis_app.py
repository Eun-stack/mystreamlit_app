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
    "conj":"접속된 명사",
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
    "acl" : "형용사절"
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
user_input = st.text_area("분석할 네덜란드어 문장을 입력하세요.", height=200)

# 입력이 있으면 분석
if user_input:
    with st.spinner("문장을 분석 중입니다..."):
        # 텍스트 분석
        doc = nlp(user_input)

        # 품사 태깅 데이터
        pos_data = []
        for idx, sentence in enumerate(doc.sentences, start=1):
            for word in sentence.words:
                pos_data.append([f"{idx}번 문장", word.text, word.lemma, POS_match.get(word.pos, word.pos), word.pos])

        # 의존 구문 분석 데이터
        deprel_data = []
        for idx, sentence in enumerate(doc.sentences, start=1):
            for word in sentence.words:
                head_word = sentence.words[word.head - 1].text if word.head > 0 else 'ROOT'
                deprel_data.append([f"{idx}번 문장", word.text, head_word, deprel_match.get(word.deprel, word.deprel), word.deprel])

        # 명명된 개체 인식(NER) 데이터
        ner_data = []
        for sentence in doc.sentences:
            for ent in sentence.ents:
                ner_data.append([ent.text, NER_match.get(ent.type, ent.type), ent.type])

        # 품사 태깅 표 출력
        if pos_data:
            st.subheader("품사 태깅")
            pos_df = pd.DataFrame(pos_data, columns=["문장", "단어", "표제어", "품사", "품사 코드"])
            st.dataframe(pos_df)

        # 의존 구문 분석 표 출력
        if deprel_data:
            st.subheader("의존 구문 분석")
            deprel_df = pd.DataFrame(deprel_data, columns=["문장", "단어", "헤드 단어", "의존 관계", "의존 관계 코드"])
            st.dataframe(deprel_df)

        # 명명된 개체 인식 표 출력
        if ner_data:
            st.subheader("명명된 개체 인식 (NER)")
            ner_df = pd.DataFrame(ner_data, columns=["엔티티", "라벨", "코드"])
            st.dataframe(ner_df)

        # 의존 구문 트리 시각화 (NetworkX와 matplotlib을 이용한 시각화)
        def plot_dependency_tree(sentence):
            # 의존 관계를 트리 구조로 그리기
            G = nx.DiGraph()
            for word in sentence.words:
                G.add_node(word.id, label=word.text)
                if word.head > 0:
                    G.add_edge(word.head, word.id)
            
            pos = nx.spring_layout(G)  # 레이아웃
            labels = nx.get_node_attributes(G, 'label')

            plt.figure(figsize=(10, 8))
            nx.draw(G, pos, with_labels=True, labels=labels, node_size=2000, node_color='skyblue', font_size=12, font_weight='bold', arrows=True)
            st.pyplot(plt)

        # 첫 번째 문장의 의존 구문 트리 시각화 (만약 문장이 여러 개 있으면 첫 번째 문장만 시각화)
        if doc.sentences:
            plot_dependency_tree(doc.sentences[0])

# 설명 추가
st.markdown("""
### 네덜란드어 문법 학습 팁
- **의존 구문 분석**은 문장에서 각 단어가 다른 단어와 어떻게 연결되는지 이해하는 데 중요한 도구입니다.
- **명명된 개체 인식(NER)**은 문장에서 사람, 장소, 날짜 등 중요한 정보를 추출하는 데 유용합니다.
""")