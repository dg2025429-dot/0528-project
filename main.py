import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="한/미 주식 비교 웹앱", page_icon="📈", layout="wide")

st.title("📈 한/미 주요 주식 수익률 비교 분석")
st.markdown("당곡고등학교 데이터 분석 프로젝트 - `yfinance`와 `Streamlit`을 활용한 주식 차트 분석 웹앱입니다.")

# ==========================================
# 2. 사이드바 (사용자 설정 영역)
# ==========================================
st.sidebar.header("⚙️ 분석 설정")

# 기본 제공할 주요 주식 티커 (한국 주식은 코스피 .KS 또는 코스닥 .KQ가 붙습니다)
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

# 사용자가 비교할 주식을 다중 선택할 수 있도록 구성
selected_names = st.sidebar.multiselect(
    "비교할 주식을 선택하세요:",
    options=list(default_tickers.keys()),
    default=["삼성전자", "애플 (AAPL)", "엔비디아 (NVDA)"]
)

# 분석할 날짜 구간 선택 (기본값: 최근 1년)
today = datetime.today().date()
start_date = st.sidebar.date_input("시작일", today - timedelta(days=365))
end_date = st.sidebar.date_input("종료일", today)

# 선택한 회사 이름을 실제 yfinance 티커 기호로 변환
selected_tickers = [default_tickers[name] for name in selected_names]

# ==========================================
# 3. 데이터 로딩 함수
# ==========================================
@st.cache_data # 데이터를 캐싱하여 조건을 바꾸지 않는 한 매번 다시 다운로드하지 않도록 최적화
def load_data(tickers, start, end):
    if not tickers:
        return pd.DataFrame()
    
    # yfinance를 통해 데이터 다운로드 (Close: 종가 기준)
    data = yf.download(tickers, start=start, end=end)
    
    if data.empty:
        return pd.DataFrame()
        
    # 'Close' 가격만 추출
    if 'Close' in data.columns:
        df_close = data['Close']
    else:
        df_close = data
        
    # 종목을 하나만 선택했을 경우 Series 형태로 반환되므로 DataFrame으로 변환
    if isinstance(df_close, pd.Series):
        df_close = df_close.to_frame(name=tickers[0])
        
    return df_close

# ==========================================
# 4. 메인 화면 (데이터 분석 및 시각화)
# ==========================================
if selected_tickers:
    # 데이터를 불러오는 동안 스피너(로딩 애니메이션) 표시
    with st.spinner('주가 데이터를 불러오는 중입니다...'):
        df = load_data(selected_tickers, start_date, end_date)

    if not df.empty:
        # 결측치 처리 (휴장일 등의 이유로 빈 데이터를 이전 날짜 데이터로 채움)
        df = df.ffill().dropna()

        # 🔥 에러 해결 부분: 결측치 처리 후 데이터가 다 지워져서 0줄이 되었는지 한 번 더 확인합니다!
        if df.empty:
            st.warning("선택하신 기간에 유효한 주가 데이터가 없습니다. 주말이나 휴일인지 확인하고 시작일/종료일을 더 길게 설정해주세요.")
        else:
            # 데이터프레임의 컬럼명(티커)을 알아보기 쉬운 회사 이름으로 변경
            ticker_to_name = {v: k for k, v in default_tickers.items()}
            # yfinance 반환 시 다중 인덱스 등이 생길 수 있으므로 매핑 적용
            df.columns = [ticker_to_name.get(col, col) for col in df.columns]

            # 수익률 계산: (현재 가격 / 시작일 가격 - 1) * 100
            returns_df = (df / df.iloc[0] - 1) * 100

            # --- 차트 그리기 ---
            st.subheader(f"📊 누적 수익률 비교 ({start_date} ~ {end_date})")
            st.write("선택한 기간 동안 각 주식을 시작일에 샀을 경우의 누적 수익률(%)입니다.")
            
            # Plotly를 이용한 반응형 꺾은선형 차트
            fig = px.line(
                returns_df,
                x=returns_df.index,
                y=returns_df.columns,
                labels={"value": "누적 수익률 (%)", "Date": "날짜", "variable": "종목명"}
            )
            # 마우스를 올렸을 때 모든 종목의 수치를 세로선과 함께 한 번에 보여주도록 설정
            fig.update_layout(hovermode="x unified", yaxis_tickformat='.2f')
            st.plotly_chart(fig, use_container_width=True)

            # --- 데이터 표 보여주기 ---
            st.subheader("📋 최근 종가 데이터 (원/달러)")
            # 최신 날짜가 위로 오도록 역순 정렬하여 최근 5일 치만 출력
            st.dataframe(df.tail(5).sort_index(ascending=False))

    else:
        st.warning("데이터를 가져오지 못했습니다. 날짜 구간을 변경하거나 잠시 후 다시 시도해주세요.")
else:
    st.info("왼쪽 사이드바에서 비교할 주식을 하나 이상 선택해주세요.")
