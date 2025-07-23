import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw

st.set_page_config(layout="wide")
st.title("📄 PDF 뷰어 및 문구 검색")

uploaded_file = st.sidebar.file_uploader("📁 PDF 파일 업로드", type=['pdf'])

if uploaded_file:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_pages = doc.page_count
    st.sidebar.write(f"총 페이지 수: {total_pages}")

    # 페이지 선택 방법 1: 드롭다운
    page_options = [f"{i+1} 페이지" for i in range(total_pages)]
    selected_page_label = st.sidebar.selectbox("드롭다운으로 페이지 선택", page_options)
    page_to_show = int(selected_page_label.split()[0]) - 1

    # 페이지 선택 방법 2: 직접 입력
    manual_page = st.sidebar.number_input("직접 페이지 번호 입력 (1~총 페이지)", min_value=1, max_value=total_pages, value=page_to_show + 1)
    page_to_show = manual_page - 1  # 둘 중 어떤 게 마지막으로 입력됐는지는 반영 안 함 (동기화하려면 더 복잡해짐)

    # 검색어 입력
    search_text = st.sidebar.text_input("🔍 찾을 문구를 입력하세요")
    st.sidebar.caption("'근저당권', '임대인', '채무자', '소유권' 등")

    def transform_point(mat, x, y):
        a, b, c, d, e, f = mat.a, mat.b, mat.c, mat.d, mat.e, mat.f
        x_new = a * x + c * y + e
        y_new = b * x + d * y + f
        return x_new, y_new

    def get_page_image_with_highlight(page_num, highlights=None, zoom=1.5):
        page = doc.load_page(page_num)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        if highlights:
            draw = ImageDraw.Draw(img)
            for rect in highlights:
                x0, y0 = transform_point(mat, rect.x0, rect.y0)
                x1, y1 = transform_point(mat, rect.x1, rect.y1)
                box = [x0, y0, x1, y1]
                draw.rectangle(box, outline="red", width=3)
        return img

    highlights = []
    found_pages = []

    if search_text:
        for i in range(total_pages):
            page = doc.load_page(i)
            text_instances = page.search_for(search_text)
            if text_instances:
                found_pages.append(i)
                if i == page_to_show:
                    highlights = text_instances

        if found_pages:
            st.sidebar.success(f"✅ 문구 발견: {', '.join(str(p+1) for p in found_pages)}페이지")
        else:
            st.sidebar.error("❌ 문구를 찾을 수 없습니다.")

    img = get_page_image_with_highlight(page_to_show, highlights, zoom=1.5)
    st.image(img, width=800)
