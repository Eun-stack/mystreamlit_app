import os
from dotenv import load_dotenv
import streamlit as st
from PyPDF2 import PdfReader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 환경변수 & Gemini API 설정
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("GEMINI_API_KEY 환경변수를 설정해주세요 (.env)")
    st.stop()

genai.configure(api_key=API_KEY)

# 2. PDF 텍스트 추출 함수 (디버깅 코드 포함)
def extract_text_from_pdf(file) -> str:
    pdf = PdfReader(file)
    texts = []
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            texts.append(text)
        else:
            st.warning(f"⚠️ {i+1}페이지에서 텍스트를 추출할 수 없습니다.")
    full_text = "\n".join(texts)

    # ✅ 디버깅: 텍스트 추출 성공 여부 출력
    if full_text.strip():
        st.success(f"✅ 텍스트 추출 완료 (총 {len(full_text)}자)")
        st.expander("📄 추출된 텍스트 미리보기").write(full_text[:1000])  # 앞부분만 표시
    else:
        st.error("❌ 텍스트를 추출하지 못했습니다. PDF가 이미지 기반이거나 내용이 비어있을 수 있습니다.")
    return full_text

# 3. 임베딩 & FAISS 생성 함수
def create_faiss_index(text, embedding_model):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)

    # ✅ 디버깅: 분할된 청크 개수 확인
    st.info(f"🔍 분할된 텍스트 조각 수: {len(chunks)}")

    db = FAISS.from_texts(chunks, embedding_model)
    return db

# 4. Gemini 텍스트 생성 함수
def generate_text_with_gemini(prompt: str, token_limit=300) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")
    generation_config = genai.GenerationConfig(max_output_tokens=token_limit)
    response = model.generate_content(
        prompt,
        generation_config=generation_config
    )
    return response.text

# 5. 스토리라인 생성
def generate_storylines(db):
    context_docs = db.similarity_search("스토리라인 추천", k=5)
    combined_context = "\n".join([doc.page_content for doc in context_docs])

    prompt = (
        f"다음은 PDF에서 발췌한 내용입니다:\n{combined_context}\n\n"
        f"위 내용을 참고하여 자연스러운 스토리라인 5가지를 추천해줘. "
        f"각 스토리라인은 최대 3문장, 문장당 50자를 넘지 않아야 해."
    )
    
    # 디버그용: 프롬프트 화면 출력
    st.text_area("▶ Gemini API로 보내는 프롬프트 (디버그)", prompt, height=300)
    
    return generate_text_with_gemini(prompt, token_limit=1000)

# 6. 전체 스토리 생성
def generate_full_story(db, selected_storyline, token_limit):
    context_docs = db.similarity_search(selected_storyline, k=10)
    if not context_docs:
        st.warning("🔍 관련 문서를 찾을 수 없습니다. 스토리라인을 바꿔보세요.")
        return "⚠️ 관련 문서 없음"

    combined_context = "\n".join([doc.page_content for doc in context_docs])

    # ✅ 디버깅: 검색된 context 일부 확인
    st.expander("🔍 검색된 문맥 미리보기").write(combined_context[:1000])

    prompt = (
        f"다음은 PDF에서 추출한 관련 내용입니다:\n{combined_context}\n\n"
        f"선택된 스토리라인: {selected_storyline}\n\n"
        f"위 내용을 참고하여, 선택된 스토리라인을 기반으로 {token_limit} 토큰 분량의 전체 스토리를 작성해줘. "
        f"스토리는 발단, 전개, 위기, 절정, 결말의 5단계로 구성하고, 각 단계를 동등한 비율로 나누어 작성해줘. "
        f"최대한 {token_limit} 토큰 분량만큼의 단어 수를 사용해줘 "
        f"전체 스토리는 한국어로 작성해."
    )
    return generate_text_with_gemini(prompt, token_limit=token_limit)

# --- Streamlit UI 시작 ---
st.title("📚 AI로 소설 쓰기 (Gemini API 사용)")

# 세션 초기화
if "db" not in st.session_state:
    st.session_state.db = None
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "storylines" not in st.session_state:
    st.session_state.storylines = ""

uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

if uploaded_file is not None and st.session_state.db is None:
    with st.spinner("PDF 텍스트 추출 중..."):
        text = extract_text_from_pdf(uploaded_file)
        st.session_state.pdf_text = text

    if text.strip():
        with st.spinner("임베딩 및 검색 DB 구축 중..."):
            embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            db = create_faiss_index(text, embedding_model)
            st.session_state.db = db
            st.success("✅ PDF 분석 및 인덱스 구축 완료!")

if st.session_state.db:
    st.info("PDF가 성공적으로 업로드 및 분석되었습니다.")

    if st.button("스토리라인 추천 생성"):
        with st.spinner("스토리라인 추천 생성 중..."):
            storylines = generate_storylines(st.session_state.db)
            st.session_state.storylines = storylines

    if st.session_state.storylines:
        st.markdown("### 추천 스토리라인 5개")
        st.markdown(st.session_state.storylines)

        st.markdown("---")
        st.markdown("### ✍️ 전체 소설 작성")

        storyline_list = [line for line in st.session_state.storylines.strip().split('\n') if line.strip()]
        selected_storyline = st.selectbox("전체 스토리를 작성할 스토리라인을 선택해주세요.", storyline_list)

        story_token_limit = st.slider("전체 스토리의 최대 토큰 수 (1000 ~ 10000)", min_value=1000, max_value=10000, value=2000, step=100)

        if st.button("전체 소설 작성 시작"):
            with st.spinner("전체 소설 생성 중..."):
                full_story = generate_full_story(st.session_state.db, selected_storyline, story_token_limit)
                st.session_state.messages.append({"role": "assistant", "content": full_story})
                st.rerun()

    if st.button("이어하기"):
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            last_text = st.session_state.messages[-1]["content"]
            continue_prompt = last_text + "\n\n앞선 결과의 뒷 부분을 추가로 만들어주세요."
            with st.spinner("이어하기 생성 중..."):
                continuation = generate_text_with_gemini(continue_prompt, token_limit=story_token_limit)
                st.session_state.messages[-1]["content"] += continuation
        else:
            st.warning("이어할 AI 출력 결과가 없습니다.")

    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        if role == "assistant":
            st.markdown(f"**AI:** {content}")
        else:
            st.markdown(f"**사용자:** {content}")

    user_input = st.text_input("AI에게 수정 요청이나 질문을 해보세요")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        recent_msgs = st.session_state.messages[-6:]
        chat_context = ""
        for m in recent_msgs:
            prefix = "사용자" if m["role"] == "user" else "AI"
            chat_context += f"{prefix}: {m['content']}\n"
        prompt = (
            f"다음은 사용자의 요청과 AI의 이전 대화입니다:\n{chat_context}\n"
            f"사용자의 마지막 요청에 대해 친절하고 명확하게 답변해주세요."
        )
        reply = generate_text_with_gemini(prompt, token_limit=500)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
else:
    st.info(
        """PDF 파일을 업로드하면 AI가 내용을 분석하고 소설 각 구간별로 창작해드립니다.\n
        - 이미지 기반 PDF는 분석할 수 없습니다.\n
        - Word나 한글 파일을 PDF로 저장 후 업로드해 주세요.\n
        - 배경, 등장인물, 전개 등이 포함된 내용일수록 좋은 결과가 생성됩니다.
        """
    )

if st.button("대화 및 데이터 초기화"):
    st.session_state.messages = []
    st.session_state.db = None
    st.session_state.pdf_text = ""
    st.session_state.storylines = ""
    st.rerun()
