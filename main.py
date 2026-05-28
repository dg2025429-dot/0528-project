import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # 캔들 차트 같은 상세 차트를 그리기 위해 추가된 모듈
from datetime import datetime, timedelta

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="한/미 주식 비교 웹앱", page_icon="📈", layout="wide")

st.title("📈 한/미 주요 주식 수익률 비교 분석 (Pro 버전)")
st.markdown("당곡고등학교 데이터 분석 프로젝트 - `yfinance`와 `Streamlit`을 활용한 주식 차트 분석 웹앱입니다.")

# ==========================================
# 2. 사이드바 (사용자 설정 영역)
# ==========================================
st.sidebar.header("⚙️ 분석 설정")

default_tickers = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "현대차": "005380.KS",
    "애플 (AAPL)": "AAPL",
    "마이크로소프트 (MSFT)": "MSFT",
    "엔비디아 (NVDA)": "NVDA",
    "테슬라 (TSLA)": "TSLA"
}

# 기본 주식 다중 선택
selected_names = st.sidebar.multiselect(
    "비교할 주식을 선택하세요:",
    options=list(default_tickers.keys()),
    default=["삼성전자", "애플 (AAPL)"]
)

# 🔥 추가 기능 1: 목록에 없는 종목 직접 입력받기
custom_ticker = st.sidebar.text_input("🔍 직접 종목 추가 (예: AMZN, 035720.KS):")

today = datetime.today().date()
start_date = st.sidebar.date_input("시작일", today - timedelta(days=365))
end_date = st.sidebar.date_input("종료일", today)

# 🔥 추가 기능 3-1: 이동평균선 표시 여부 체크박스
show_ma = st.sidebar.checkbox("상세 차트에 20일 이동평균선 표시", value=True)

# 선택된 종목들을 티커(코드) 리스트로 변환
selected_tickers = [default_tickers[name] for name in selected_names]

# 사용자가 직접 입력한 티커가 있다면 리스트에 추가
if custom_ticker:
    custom_ticker = custom_ticker.upper() # 대문자로 변환
    selected_tickers.append(custom_ticker)
    default_tickers[f"직접입력({custom_ticker})"] = custom_ticker # 표에 예쁘게 나오도록 딕셔너리에도 추가

# ==========================================
# 3. 데이터 로딩 함수
# ==========================================
@st.cache_data
def load_close_data(tickers, start, end):
    """여러 종목의 종가(Close)만 가져오는 함수"""
    if not tickers: return pd.DataFrame()
    data = yf.download(tickers, start=start, end=end)
    if data.empty: return pd.DataFrame()
    
    if 'Close' in data.columns:
        df_close = data['Close']
    else:
        df_close = data
        
    if isinstance(df_close, pd.Series):
        df_close = df_close.to_frame(name=tickers[0])
    return df_close

@st.cache_data
def load_single_ohlc(ticker, start, end):
    """단일 종목의 시가, 고가, 저가, 종가를 모두 가져오는 함수 (캔들 차트용)"""
    data = yf.download(ticker, start=start, end=end)
    return data

# ==========================================
# 4. 메인 화면 (데이터 분석 및 시각화)
# ==========================================
if selected_tickers:
    with st.spinner('주가 데이터를 불러오는 중입니다...'):
        df = load_close_data(selected_tickers, start_date, end_date)

    if not df.empty:
        df = df.ffill().dropna()

        if df.empty:
            st.warning("선택하신 기간에 유효한 주가 데이터가 없습니다.")
        else:
            ticker_to_name = {v: k for k, v in default_tickers.items()}
            df.columns = [ticker_to_name.get(col, col) for col in df.columns]

            # [수익률 비교 차트 - 기존 기능]
            returns_df = (df / df.iloc[0] - 1) * 100
            st.subheader(f"📊 누적 수익률 비교 ({start_date} ~ {end_date})")
            fig_line = px.line(returns_df, x=returns_df.index, y=returns_df.columns, labels={"value": "누적 수익률 (%)", "Date": "날짜", "variable": "종목명"})
            fig_line.update_layout(hovermode="x unified", yaxis_tickformat='.2f')
            st.plotly_chart(fig_line, use_container_width=True)

            st.markdown("---")

            # 🔥 추가 기능 2: 개별 종목 상세 캔들 차트
            st.subheader("🔎 개별 종목 상세 분석 (캔들 차트)")
            st.write("선택한 목록의 **첫 번째 종목**에 대한 상세 차트입니다. 시가, 고가, 저가, 종가의 흐름을 한눈에 파악하세요.")
            
            target_ticker = selected_tickers[0]
            target_name = ticker_to_name.get(target_ticker, target_ticker)
            ohlc_df = load_single_ohlc(target_ticker, start_date, end_date)
            
            if not ohlc_df.empty:
                # yfinance 데이터 형식 보정 (다중 인덱스 제거)
                if isinstance(ohlc_df.columns, pd.MultiIndex):
                    ohlc_df.columns = ohlc_df.columns.droplevel(1)
                
                # 캔들 차트 그리기
                fig_candle = go.Figure()
                fig_candle.add_trace(go.Candlestick(
                    x=ohlc_df.index,
                    open=ohlc_df['Open'],
                    high=ohlc_df['High'],
                    low=ohlc_df['Low'],
                    close=ohlc_df['Close'],
                    name=target_name
                ))
                
                # 🔥 추가 기능 3-2: 20일 이동평균선 계산 및 추가 (Pandas의 rolling 함수 사용)
                if show_ma:
                    ohlc_df['MA20'] = ohlc_df['Close'].rolling(window=20).mean()
                    fig_candle.add_trace(go.Scatter(
                        x=ohlc_df.index,
                        y=ohlc_df['MA20'],
                        mode='lines',
                        line=dict(color='blue', width=2),
                        name='20일 이동평균선'
                    ))
                
                fig_candle.update_layout(
                    title=f"{target_name} 상세 차트",
                    yaxis_title="주가",
                    xaxis_title="날짜",
                    xaxis_rangeslider_visible=False # 하단 슬라이더 숨기기 (깔끔한 UI를 위해)
                )
                st.plotly_chart(fig_candle, use_container_width=True)
                
            # [최근 종가 데이터 표]
            st.subheader("📋 최근 종가 데이터 (원/달러)")
            st.dataframe(df.tail(5).sort_index(ascending=False))

    else:
        st.warning("데이터를 가져오지 못했습니다. 잠시 후 다시 시도해주세요.")
else:
    st.info("왼쪽 사이드바에서 비교할 주식을 하나 이상 선택해주세요.")
