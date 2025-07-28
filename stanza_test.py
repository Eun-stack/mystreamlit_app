import stanza

# 네덜란드어 파이프라인 생성
nlp = stanza.Pipeline('nl')

# 분석할 네덜란드어 텍스트
text = "Dit is een voorbeeldtekst in het Nederlands."

# 텍스트 분석
doc = nlp(text)

# 분석 결과 출력
for sentence in doc.sentences:
    for word in sentence.words:
        print(f"단어: {word.text}, 품사: {word.pos}, 기본형: {word.lemma}, 의존 관계: {word.deprel}")
