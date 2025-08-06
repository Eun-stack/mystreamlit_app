import stanza
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import google.generativeai as genai

def is_stanza_model_downloaded(lang_code='nl'):
    """
    Stanza 언어 모델이 다운로드되어 있는지 확인합니다.
    """
    home = os.path.expanduser("~")
    model_path = os.path.join(home, 'stanza_resources', lang_code)
    return os.path.isdir(model_path) and bool(os.listdir(model_path))

# Streamlit 앱 시작
st.title("🇳🇱 Stanza 네덜란드어 모델 확인 및 다운로드")

if is_stanza_model_downloaded('nl'):
    st.success("✅ 네덜란드어 모델이 이미 다운로드되어 있습니다.")
else:
    st.warning("⚠️ 네덜란드어 모델이 없습니다. 다운로드가 필요합니다.")
    
    if st.button("📥 모델 다운로드"):
        with st.spinner("네덜란드어 모델을 다운로드 중입니다..."):
            stanza.download('nl')
        st.success("✅ 다운로드 완료! 앱을 새로고침하세요.")

# 네덜란드어 모델 초기화 (캐싱)
@st.cache_resource
def load_model():
    return stanza.Pipeline('nl', processors='tokenize,mwt,pos,lemma,depparse,ner')

nlp = load_model()

# 품사 매핑
POS_match = {
    "ADJ"  : "형용사", "ADV"  : "부사", "ADP"  : "전치사", "AUX"  : "조동사",
    "CCONJ": "접속사", "DET"  : "정관사", "NUM"  : "숫자", "NOUN" : "명사",
    "PRON" : "대명사", "PROPN" : "고유명사", "PUNCT": "구두점", "VERB" : "동사"
}

# 의존 관계 매핑
deprel_match = {
    "nsubj": "주어", "obj": "목적어", "obl": "부사어", "root": "중심 동사", "amod": "형용사 수식",
    "advmod": "부사 수식", "case": "격 표시", "compound": "복합어", "det": "한정사",
    "nmod": "명사 수식", "conj": "접속", "cc": "접속사", "xcomp": "보어", "mark": "절 표지",
    "cop": "연결 동사", "appos": "동격", "punct": "구두점", "parataxis": "병렬", "acl": "형용사절",
    "acl:relcl":"명사 수식",
    "expl:pv": "가주어",
    "obl:arg": "필수 부사구",
    "nmod:poss":"소유격 명사 수식어",
    "aux": "보조 동사",
    "flat" : "구성 요소",
    "compound:prt":"분리전철",
    "nummod":"수사의 명사 수식",
    "nsubj:pass" : "수동태 명사 주어",
    "aux:pass" : "수동태 조동사"
}

# 30가지 색상 리스트 준비 (matplotlib tab20 + 추가 10가지)
base_colors = plt.get_cmap('tab20').colors  # 20가지
extra_colors = [
    (0.9, 0.1, 0.1), (0.1, 0.9, 0.1), (0.1, 0.1, 0.9),
    (0.9, 0.5, 0.1), (0.5, 0.1, 0.9), (0.1, 0.9, 0.5),
    (0.6, 0.2, 0.2), (0.2, 0.6, 0.2), (0.2, 0.2, 0.6),
    (0.8, 0.3, 0.4)
]
colors_30 = list(base_colors) + extra_colors

def get_color_by_distance(dist, colors=colors_30):
    """
    간격 차이에 따라 색상 반환 (1 이상 30 이하)
    """
    if dist < 1:
        dist = 1
    if dist > len(colors):
        dist = len(colors)
    return colors[dist - 1]

# 페이지 설정
st.set_page_config(page_title="네덜란드어 의존 구문 분석기", layout="wide")
st.title("🇳🇱 네덜란드어 의존 구문 분석기")

# 사용자 입력
user_input = st.text_area("분석할 네덜란드어 문장을 입력한 후 Ctrl+Enter로 분석을 시작하세요.", height=150)

# 분석 처리
if user_input:
    with st.spinner("분석 중..."):
        doc = nlp(user_input)

        for i, sentence in enumerate(doc.sentences, start=1):
            sentence_data = []
            arcs = []
            word_list = [word.text for word in sentence.words]

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

                if word.head > 0:
                    arcs.append((word.head - 1, word.id - 1))  # (head idx, dependent idx)

            # 결과 표
            if sentence_data:
                st.subheader(f"📝 문장 {i}: {sentence.text}")
                df = pd.DataFrame(
                    sentence_data,
                    columns=["단어", "표제어", "품사", "품사 코드", "헤드 단어", "의존 관계", "의존 관계 코드"]
                )
                
                # 인덱스를 1부터 시작하도록 수정
                df.index = df.index + 1  # 인덱스 값에 1을 더하여 1부터 시작하게 설정
                
                st.dataframe(df)

            # 시각화
            if arcs:
                st.markdown("🎯 **의존 구문 시각화**")

                fig, ax = plt.subplots(figsize=(len(word_list) * 2.0, 3))

                # 단어 개수가 15개를 초과하면 시각화 높이를 2배로 설정
                if len(word_list) > 15:
                    fig, ax = plt.subplots(figsize=(len(word_list) * 2.0, 6))  # 높이를 2배로 설정

                positions = list(range(len(word_list)))

                # 단어 라벨
                ax.set_xticks(positions)
                ax.set_xticklabels(word_list, fontsize=14)
                ax.set_yticks([])
                ax.set_ylim(0, max(4, max(abs(dep - head) for head, dep in arcs) + 1))  # y축 범위 자동조절
                ax.set_xlim(-1, len(word_list))

                # 곡선 그리기 (간격에 따라 색상 지정)
                for head, dep in arcs:
                    x_vals = np.linspace(min(head, dep), max(head, dep), 500)
                    amplitude = abs(dep - head)
                    if amplitude == 0:
                        amplitude = 1

                    height = amplitude * np.abs(np.sin(np.pi * (x_vals - min(head, dep)) / (max(head, dep) - min(head, dep))))

                    
                    # root 여부 확인
                    if sentence.words[head].deprel == "root":
                        color = 'red'
                    else:
                        color = get_color_by_distance(amplitude)

                    if head < dep:
                        linestyle = '--'   # 왼쪽 -> 오른쪽 : 실선
                    else:
                        linestyle = '-'  # 오른쪽 -> 왼쪽 : 점선

                    ax.plot(x_vals, height, color=color, linestyle=linestyle, linewidth=2)

                ax.set_title("Dependency Structure", fontsize=16)
                st.pyplot(fig)

                st.markdown("""
                **범례**  
                - 실선 : 왼쪽   → 오른쪽  
                - 점선 : 오른쪽 → 왼쪽  
                - ROOT에 의존한 단어는 빨간색 선
                """)


# --- Gemini 번역 기능 추가 ---
st.markdown("---")
st.header("✨ 네덜란드어 문장 번역 (Gemini Pro)")

# API 키 입력
gemini_api_key = st.text_input("Gemini API Key를 입력하세요", type="password")

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        # 번역할 문장 입력
        dutch_text_for_translation = st.text_area("번역할 네덜란드어 문장을 입력하세요", height=100)
        
        if st.button("🚀 번역하기"):
            if not dutch_text_for_translation:
                st.warning("번역할 문장을 입력해주세요.")
            else:
                with st.spinner("Gemini가 번역 중입니다..."):
                    prompt = f"다음 네덜란드어 문장을 자연스러운 한국어로 번역해줘. 문맥을 고려하여 정확하게 번역해줘. 오역은 하지 말아줘.\n네덜란드어: {dutch_text_for_translation}\n한국어:"
                    
                    try:
                        response = model.generate_content(prompt)
                        translated_text = response.text
                        st.success("✅ 번역 완료!")
                        st.markdown(f"**번역 결과:**\n\n> {translated_text}")
                    except Exception as e:
                        st.error(f"번역 중 오류가 발생했습니다: {e}")
                        st.info("API 키가 올바른지 확인하거나, 입력 문장이 부적절한지 확인해주세요.")
    except Exception as e:
        st.error(f"API 키 설정에 오류가 있습니다: {e}")
        st.info("올바른 Gemini API 키를 입력했는지 확인해주세요.")
else:
    st.info("번역 기능을 사용하려면 Gemini API 키를 입력하세요.")