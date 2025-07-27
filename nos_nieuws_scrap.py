import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from collections import Counter
import csv
import time
import re
import random
import io

st.set_page_config(page_title="NOS 뉴스 크롤러", layout="wide")
st.title("📰 NOS 뉴스 크롤링 및 키워드 추출")

# --------------------- 기사 제목 + 본문 한 번에 추출 ---------------------
def get_article_info(url):
    stop_words = {
        "Deel artikel", "Voorpagina", "Laatste nieuws", "Video's", "Binnenland",
        "Buitenland", "Regionaal nieuws", "Politiek", "Economie", "Koningshuis",
        "Tech", "Cultuur & media", "Cultuur & Media", "Opmerkelijk",
        "In samenwerking met RTV Utrecht", "In samenwerking met NH"
    }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        }
        resp = requests.get(url, headers=headers)
        time.sleep(random.uniform(1.0, 2.0))  # 본문 요청 후 잠깐 대기
        soup = BeautifulSoup(resp.text, "html.parser")

        main = soup.select_one("main#content")
        if not main:
            return "제목 없음", "본문 없음"

        # 제목 추출
        h1 = main.find("h1")
        title = h1.get_text(" ", strip=True) if h1 else "제목 없음"

        # 본문 추출
        parts = []
        for el in main.find_all(["p", "h2", "li"], recursive=True):
            txt = el.get_text(" ", strip=True)
            if not txt:
                continue
            if txt in stop_words:
                break
            if title and txt == title:
                continue
            if el.name == "h2":
                parts.append(f"\n**{txt}**\n")
            elif el.name == "li":
                parts.append(f"- {txt}")
            else:
                parts.append(txt)

        body = "\n\n".join(parts)
        return title, body

    except Exception as e:
        return "제목 없음", str(e)

# --------------------- 불용어 ---------------------
dutch_stopwords = {
    "de", "en", "van", "ik", "te", "dat", "die", "in", "een", "hij", "het", "niet",
    "zijn", "is", "was", "op", "aan", "met", "als", "voor", "had", "er", "maar",
    "om", "hem", "dan", "zou", "of", "wat", "mijn", "men", "dit", "zo", "door",
    "over", "ze", "zich", "bij", "ook", "tot", "je", "mij", "uit", "der", "daar",
    "haar", "naar", "heb", "hoe", "heeft", "hebben", "deze", "u", "want", "nog",
    "zal", "me", "zij", "nu", "ge", "geen", "omdat", "iets", "worden", "toch",
    "al", "waren", "veel", "meer", "doen", "toen", "moet", "ben", "zonder", "kan",
    "hun", "dus", "alles", "onder", "ja", "werd", "wezen", "zelf", "tegen",
    "komen", "goed", "hier", "wie", "waarom"
}

# --------------------- 키워드 추출 ---------------------
def extract_keywords(text, top_n=10):
    words = re.findall(r'\b[a-zA-Z]{10,}\b', text)
    capitalized_words = [w.capitalize() for w in words]
    filtered_words = [w for w in capitalized_words if w.lower() not in dutch_stopwords]
    freq = Counter(filtered_words)

    unique_keywords = []
    for word, _ in freq.most_common():
        if word not in unique_keywords:
            unique_keywords.append(word)
        if len(unique_keywords) >= top_n:
            break

    return [(kw, freq[kw]) for kw in unique_keywords], filtered_words

# --------------------- 뉴스 크롤링 ---------------------
def crawling_news(category_slug, count=2):
    base_url = "https://nos.nl/"
    category_url = base_url + category_slug
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    }

    news_list = []
    try:
        resp = requests.get(category_url, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        articles = soup.select("a[href*='/artikel']")
        urls_seen = set()

        # 진행 상황 바
        progress = st.progress(0)
        total = min(count, len(articles))

        for idx, link in enumerate(articles):
            if len(news_list) >= count:
                break

            url = link.get('href')
            if not url or url in urls_seen:
                continue
            if not url.startswith("http"):
                url = "https://nos.nl" + url
            urls_seen.add(url)

            try:
                title, body = get_article_info(url)
                keywords, long_words = extract_keywords(body)

                news_list.append({
                    'title': title,
                    'url': url,
                    'body': body,
                    'keywords': [kw for kw, _ in keywords],
                    'lange_woorden': long_words
                })

                # 진행률 업데이트
                progress.progress(int((len(news_list) / total) * 100))

                # 기사 하나 처리 후 대기
                time.sleep(random.uniform(2.0, 3.0))

            except:
                continue

        progress.empty()  # 진행 상황 바 제거

    except Exception as e:
        st.error(f"뉴스 크롤링 오류: {e}")
        st.write(f"❌ 실패한 URL: {category_url}")

    return news_list

# --------------------- CSV 생성 ---------------------
def generate_csv_bytes(result):
    if not result:
        return None
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['index', 'title', 'url', 'keywords', 'lange_woorden'])
    writer.writeheader()
    for idx, news in enumerate(result, 1):
        writer.writerow({
            'index': idx,
            'title': news['title'],
            'url': news['url'],
            'keywords': ', '.join(news['keywords']),
            'lange_woorden': ', '.join(news['lange_woorden'])
        })
    return output.getvalue().encode('utf-8-sig')

# --------------------- UI 카테고리 ---------------------
menu_dict = { 
    1: "Laatste nieuws",
    2: "Video's",
    3: "Binnenland",
    4: "Buitenland",
    5: "Regionaal nieuws",
    6: "Politiek",
    7: "Economie",
    8: "Koningshuis",
    9: "Tech",
    10: "Cultuur & media",
    11: "Opmerkelijk"
}

menu_url_map = {
    "Laatste nieuws": "nieuws/laatste",
    "Video's": "nieuws/laatste/videos",
    "Binnenland": "nieuws/binnenland",
    "Buitenland": "nieuws/buitenland",
    "Regionaal nieuws": "nieuws/regio",
    "Politiek": "nieuws/politiek",
    "Economie": "nieuws/economie",
    "Koningshuis": "nieuws/koningshuis",
    "Tech": "nieuws/tech",
    "Cultuur & media": "nieuws/cultuur-en-media",
    "Opmerkelijk": "nieuws/opmerkelijk"
}

# --------------------- UI ---------------------
selected = st.selectbox("🗂️ Kies een 카테고리", list(menu_dict.keys()), format_func=lambda x: f"{x}. {menu_dict[x]}")
article_count = st.slider("📰 기사 수 선택", 1, 10, 2)

if st.button("🚀 뉴스 크롤링 시작"):
    st.info("🔄 뉴스를 수집하는 중입니다... 잠시만 기다려주세요.")
    selected_name = menu_dict[selected]
    category_slug = menu_url_map.get(selected_name, "")
    result = crawling_news(category_slug, article_count)

    for i, news in enumerate(result, 1):
        st.markdown(f"### {i}. {news['title']}")
        st.markdown(f"🔗 [기사 링크]({news['url']})")
        st.markdown(f"🧠 **키워드:** {', '.join(news['keywords'])}")
        with st.expander("📄 본문 펼치기"):
            st.write(news['body'])

    if result and st.checkbox("📄 CSV 파일을 생성하시겠습니까?"):
        csv_bytes = generate_csv_bytes(result)
        if csv_bytes:
            st.success("✅ CSV 파일이 생성되었습니다.")
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv_bytes,
                file_name=f"nos_nieuws_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ 저장할 뉴스 데이터가 없습니다.")
