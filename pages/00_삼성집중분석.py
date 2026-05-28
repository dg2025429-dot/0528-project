import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ==========================================
# 1. 페이지 기본 설정 (메인 페이지와 동일하게 설정 가능)
# ==========================================
st.set_page_config(page_title="삼성전자 집중 분석", page_icon="📱", layout="wide")

st.title("📱 삼성전자(005930) 집중 분석")
st.markdown("당곡고등학교 데이터 분석 프로젝트 - 단일 종목의 가격 추세와 거래량을 심층적으로 분석합니다.")

# ==========================================
# 2. 분석 설정 영역
# ==========================================
st.sidebar.header("⚙️ 분석 설정")

# 기본 분석 종목 고정
ticker_symbol = "005930.KS"

today = datetime.today().date()
start_date = st.sidebar.date_input("시작일", today - timedelta(days=365*2)) # 기본값을 최근 2년으로 설정
end_date = st.sidebar.date_input("종료일", today)

# ==========================================
# 3. 데이터 로딩 및 전처리 함수
# ==========================================
@st.cache_data
def load_samsung_data(start, end):
    # 삼성전자 데이터 다운로드
    data = yf.download(ticker_symbol, start=start, end=end)
    
    if data.empty:
        return pd.DataFrame()
        
    # yfinance 버전 업데이트로 인한 다중 인덱스(MultiIndex) 발생 시 처리
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
        
    return data

# ==========================================
# 4. 메인 분석 화면
# ==========================================
with st.spinner("삼성전자 주가 데이터를 분석 중입니다..."):
    df = load_samsung_data(start_date, end_date)

if not df.empty:
    df = df.ffill().dropna()

    if not df.empty:
        # 이동평균선 계산 (5일, 20일, 60일)
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()

        # 최근 주가 정보 요약 표시 (가장 마지막 날짜 기준)
        latest_close = df['Close'].iloc[-1]
        past_close = df['Close'].iloc[-2]
        price_change = latest_close - past_close
        pct_change = (price_change / past_close) * 100

        # st.metric을 사용해 핵심 수치를 눈에 띄게 표시
        col1, col2, col3 = st.columns(3)
        col1.metric(label="최근 종가", value=f"{int(latest_close):,} 원", delta=f"{int(price_change):,} 원 ({pct_change:.2f}%)")
        col2.metric(label="기간 내 최고가", value=f"{int(df['High'].max()):,} 원")
        col3.metric(label="기간 내 최저가", value=f"{int(df['Low'].min()):,} 원")

        st.markdown("---")
        st.subheader("📊 차트 분석 (캔들차트 + 거래량)")

        # plotly의 make_subplots를 사용하여 위쪽엔 주가 차트, 아래쪽엔 거래량 차트 배치
        # row_heights=[0.7, 0.3] 으로 주가 차트를 더 크게 설정
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, 
                            row_heights=[0.7, 0.3])

        # [Row 1] 캔들 차트 추가
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='삼성전자'
        ), row=1, col=1)

        # [Row 1] 이동평균선 추가
        fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], mode='lines', line=dict(color='orange', width=1.5), name='5일 이동평균선'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', line=dict(color='blue', width=1.5), name='20일 이동평균선'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], mode='lines', line=dict(color='green', width=1.5), name='60일 이동평균선'), row=1, col=1)

        # [Row 2] 거래량 막대 그래프 추가
        # 주가가 오른 날(빨간색)과 내린 날(파란색)을 구분하면 좋지만, 여기서는 단일 색상으로 기본 설정
        fig.add_trace(go.Bar(
            x=df.index, y=df['Volume'], name='거래량', marker_color='lightgray'
        ), row=2, col=1)

        # 차트 레이아웃(디자인) 설정
        fig.update_layout(
            height=700,
            xaxis_rangeslider_visible=False, # 메인 캔들차트 하단 슬라이더 숨김
            xaxis2_rangeslider_visible=True, # 거래량 차트 하단에만 슬라이더 표시
            hovermode="x unified",
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # 상세 데이터 표
        with st.expander("📝 상세 데이터 표 보기 (클릭하여 펼치기)"):
            st.dataframe(df.sort_index(ascending=False))

    else:
        st.warning("선택하신 기간에 유효한 데이터가 없습니다.")
else:
    st.error("데이터를 가져오는 데 실패했습니다.")
