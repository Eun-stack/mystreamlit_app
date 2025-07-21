# streamlit run ex06.py
# 폴더 위치 이동: cd 08-streamlit
# run을 정지하지 않아도 코드를 저장한 후 브라우저 창을 새로고침하면 적용됨

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(
    page_title="판매 데이터 분석 대시보드",
    page_icon="📊",
    layout="wide"
)

@st.cache_data # 바뀌지 않은 내용은 그대로 사용하겠다
def generate_sample_data():
    """샘플 판매 데이터 생성"""
    np.random.seed(42)
    
    # 날짜 범위
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    dates = pd.date_range(start_date, end_date, freq='D')
    
    # 제품 카테고리
    categories = ['전자제품', '의류', '가구', '도서', '스포츠']
    regions = ['서울', '부산', '대구', '인천', '광주']
    
    data = []
    for date in dates:
        for category in categories:
            for region in regions:
                sales = np.random.normal(1000, 300)
                quantity = np.random.poisson(50)
                data.append({
                    'date': date,
                    'category': category,
                    'region': region,
                    'sales': max(0, sales),
                    'quantity': quantity
                })
    
    return pd.DataFrame(data)

def main():
    st.title("📊 판매 데이터 분석 대시보드")
    
    # 사이드바
    st.sidebar.title("필터 옵션")
    
    # 데이터 로드
    df = generate_sample_data()
    
    # 날짜 필터
    date_range = st.sidebar.date_input(
        "기간 선택",
        value=[df['date'].min(), df['date'].max()],
        min_value=df['date'].min(),
        max_value=df['date'].max()
    )
    
    # 카테고리 필터
    categories = st.sidebar.multiselect(
        "카테고리 선택",
        options=df['category'].unique(),
        default=df['category'].unique()
    )
    
    # 지역 필터
    regions = st.sidebar.multiselect(
        "지역 선택",
        options=df['region'].unique(),
        default=df['region'].unique()
    )
    
    # 데이터 필터링
    if len(date_range) == 2:
        filtered_df = df[
            (df['date'] >= pd.Timestamp(date_range[0])) &
            (df['date'] <= pd.Timestamp(date_range[1])) &
            (df['category'].isin(categories)) &
            (df['region'].isin(regions))
        ]
    else:
        filtered_df = df[
            (df['category'].isin(categories)) &
            (df['region'].isin(regions))
        ]
    
    # 주요 지표
    st.subheader("📈 주요 지표")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sales = filtered_df['sales'].sum()
        st.metric("총 매출", f"₩{total_sales:,.0f}")
    
    with col2:
        total_quantity = filtered_df['quantity'].sum()
        st.metric("총 판매량", f"{total_quantity:,}")
    
    with col3:
        avg_sales = filtered_df['sales'].mean()
        st.metric("평균 일일 매출", f"₩{avg_sales:,.0f}")
    
    with col4:
        unique_days = filtered_df['date'].nunique()
        st.metric("분석 기간", f"{unique_days}일")
    
    # 차트 섹션
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 카테고리별 매출")
        category_sales = filtered_df.groupby('category')['sales'].sum().reset_index()
        fig_pie = px.pie(category_sales, values='sales', names='category', 
                        title="카테고리별 매출 비율")
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("🌍 지역별 매출")
        region_sales = filtered_df.groupby('region')['sales'].sum().reset_index()
        fig_bar = px.bar(region_sales, x='region', y='sales', 
                        title="지역별 총 매출")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # 시계열 차트
    st.subheader("📈 시간별 매출 추이")
    
    daily_sales = filtered_df.groupby('date')['sales'].sum().reset_index()
    fig_line = px.line(daily_sales, x='date', y='sales', 
                      title="일별 매출 추이")
    st.plotly_chart(fig_line, use_container_width=True)
    
    # 상세 데이터 테이블
    with st.expander("📋 상세 데이터 보기"):
        st.dataframe(filtered_df.sort_values('date', ascending=False), 
                    use_container_width=True)
        
        # 데이터 다운로드
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="필터링된 데이터 다운로드",
            data=csv,
            file_name=f'sales_data_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv'
        )
    
    # 분석 리포트
    st.subheader("📝 분석 리포트")
    
    # 최고 실적 카테고리
    best_category = category_sales.loc[category_sales['sales'].idxmax(), 'category']
    best_region = region_sales.loc[region_sales['sales'].idxmax(), 'region']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**최고 실적 카테고리:** {best_category}")
        st.info(f"**최고 실적 지역:** {best_region}")
    
    with col2:
        peak_day = daily_sales.loc[daily_sales['sales'].idxmax(), 'date']
        st.info(f"**최고 매출일:** {peak_day.strftime('%Y-%m-%d')}")
        st.info(f"**분석 기간 평균 일일 매출:** ₩{daily_sales['sales'].mean():,.0f}")

if __name__ == "__main__":
    main()
