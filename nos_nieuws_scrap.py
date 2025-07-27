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

st.set_page_config(page_title="NOS nieuws crawler", layout="wide")
st.title("📰 NOS nieuws crawler en trefwoordenextractie")

# --------------------- Artikel titel + tekst ---------------------
def get_article_info(url):
    stop_words = {
        "Deel artikel", "Voorpagina", "Laatste nieuws", "Video's", "Binnenland",
        "Buitenland", "Regionaal nieuws", "Politiek", "Economie", "Koningshuis",
        "Tech", "Cultuur & media", "Cultuur & Media", "Opmerkelijk",
        "In samenwerking met RTV Utrecht", "In samenwerking met NH"
    }

    resp = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    })
    resp.raise_for_status()
    time.sleep(random.uniform(1.0, 2.0))

    soup = BeautifulSoup(resp.text, "html.parser")
    main = soup.select_one("main#content")
    if not main:
        return "geen titel", "geen tekst"

    h1 = main.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else "geen titel"

    # 제목 아래 불필요한 <ul> 제거
    if h1:
        for sibling in h1.find_next_siblings():
            # 본문 시작으로 판단되는 <p>가 나오면 반복 중단
            if sibling.name == "p":
                break
            if sibling.name == "ul":
                sibling.decompose()

    parts = []
    for el in main.find_all(["p", "h2", "li"], recursive=True):
        txt = el.get_text(" ", strip=True)
        if not txt:
            continue
        if title and txt == title:
            continue
        if txt in stop_words:
            break
        if el.name == "h2":
            parts.append(f"\n**{txt}**\n")
        elif el.name == "li":
            parts.append(f"- {txt}")
        else:
            parts.append(txt)

    body = "\n\n".join(parts)
    return title, body

# --------------------- Stopwoorden ---------------------
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

# --------------------- Trefwoordenextractie ---------------------
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

# --------------------- Nieuws crawlen ---------------------
def crawling_news(category_slug, count=2, animation_placeholder=None):
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

        progress = st.progress(0)
        total = min(count, len(articles))

        icons = ["🔄", "🔁"]
        icon_index = 0

        for idx, link in enumerate(articles):
            if len(news_list) >= count:
                break

            url = link.get('href')
            if not url or url in urls_seen:
                continue
            if not url.startswith("http"):
                url = "https://nos.nl" + url
            urls_seen.add(url)

            # 애니메이션 이모지 출력
            if animation_placeholder:
                animation_placeholder.markdown(f"{icons[icon_index % 2]} Bezig met ophalen van nieuws...")
                icon_index += 1

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

                progress.progress(int((len(news_list) / total) * 100))
                time.sleep(random.uniform(2.0, 3.0))

            except:
                continue

        progress.empty()
        if animation_placeholder:
            animation_placeholder.markdown("✅ Crawlen voltooid!")

    except Exception as e:
        st.error(f"Fout bij het crawlen van nieuws: {e}")
        st.write(f"❌ Mislukte URL: {category_url}")

    return news_list

# --------------------- CSV genereren ---------------------
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

# --------------------- UI Categorieën ---------------------
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
selected = st.selectbox("🗂️ Kies een categorie", list(menu_dict.keys()), format_func=lambda x: f"{x}. {menu_dict[x]}")
article_count = st.slider("📰 Aantal artikelen", 1, 10, 2)

if st.button("🚀 Start nieuws crawling"):
    animation_placeholder = st.empty()
    selected_name = menu_dict[selected]
    category_slug = menu_url_map.get(selected_name, "")
    result = crawling_news(category_slug, article_count, animation_placeholder)

    for i, news in enumerate(result, 1):
        st.markdown(f"### {i}. {news['title']}")
        st.markdown(f"🔗 [Artikel link]({news['url']})")
        st.markdown(f"🧠 **Trefwoorden:** {', '.join(news['keywords'])}")
        with st.expander("📄 Toon artikeltekst"):
            st.write(news['body'])

    # CSV 다운로드
    if result and st.checkbox("📄 CSV-bestand genereren?"):
        csv_bytes = generate_csv_bytes(result)
        if csv_bytes:
            st.success("✅ CSV-bestand is aangemaakt.")
            st.download_button(
                label="📥 Download CSV",
                data=csv_bytes,
                file_name=f"nos_nieuws_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ Geen nieuwsgegevens om op te slaan.")
