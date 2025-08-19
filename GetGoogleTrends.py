from fastapi import FastAPI, Query
from pytrends.request import TrendReq
import random
import time
import pandas as pd

app = FastAPI()

Lang = {
    "미국 영어": "en-US",
    "한국어": "ko",
}

timeframe_options = {
    "1시간": "now 1-H",
    "4시간": "now 4-H",
    "1일": "now 1-d",
    "7일": "now 7-d",
    "1개월": "today 1-m",
    "3개월": "today 3-m",
    "12개월": "today 12-m",
    "5년": "today 5-y",
    "전체": "all"
}

def wait_random(min_sec=6, max_sec=10):
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def retry_request(func, max_retries=3, retry_wait=10):
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries:
                time.sleep(retry_wait)
            else:
                raise e

@app.get("/trends")
def get_trends(
    keywords: str = Query(..., description="검색어 여러개 쉼표로 구분"),
    lang: str = Query("한국어", description="언어: '한국어' 또는 '미국 영어'"),
    timeframe_key: str = Query("12개월", description="시간 범위 옵션")
):
    keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
    if not keyword_list:
        return {"error": "검색어를 입력하세요."}

    timeframe = timeframe_options.get(timeframe_key, "today 12-m")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/115.0.0.0 Safari/537.36'
    }

    pytrends = TrendReq(hl=Lang.get(lang, "ko"), tz=540, requests_args={'headers': headers})

    wait_random(6, 10)
    retry_request(lambda: pytrends.build_payload(keyword_list, cat=0, timeframe=timeframe, geo='KR', gprop=''))

    interest_over_time = retry_request(lambda: pytrends.interest_over_time())
    interest_by_region = retry_request(lambda: pytrends.interest_by_region())
    related_topics = retry_request(lambda: pytrends.related_topics())
    related_queries = retry_request(lambda: pytrends.related_queries())

    # 데이터프레임 → JSON 직렬화 (딕셔너리 변환)
    def df_to_dict(df):
        if df is None or df.empty:
            return None
        return df.reset_index().to_dict(orient='records')

    # 관련 주제, 관련 검색어는 중첩 dict → 리스트로 변환
    def related_to_list(d, key='top'):
        if not d:
            return None
        result = {}
        for kw in keyword_list:
            df = d.get(kw, {}).get(key)
            if df is not None and not df.empty:
                result[kw] = df.reset_index().to_dict(orient='records')
            else:
                result[kw] = None
        return result

    return {
        "interest_over_time": df_to_dict(interest_over_time),
        "interest_by_region": df_to_dict(interest_by_region),
        "related_topics": related_to_list(related_topics, 'top'),
        "related_queries": related_to_list(related_queries, 'top')
    }
