from urllib.parse import quote
import feedparser
from fredapi import Fred
from google import genai  # 建議改用新版官方 SDK: pip install google-genai
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

# ==========================================
# 1. 頁面配置與側邊欄金鑰設定
# ==========================================
st.set_page_config(
    page_title="總體經濟、金融與 NLP 市場情緒儀表板", layout="wide"
)
st.title("🌐 總體經濟、金融指標與 AI 輿論情緒即時儀表板")

st.sidebar.header("⚙️ 設定與金鑰")

# 1.1 檢查 FRED API Key
if "FRED_API_KEY" in st.secrets:
    fred_key = st.secrets["FRED_API_KEY"]
    st.sidebar.success("已自動讀取 FRED API Key！")
else:
    fred_key = st.sidebar.text_input("請輸入 FRED API Key:", type="password")

# 1.2 檢查 Gemini API Key
gemini_key = None
if "GEMINI_API_KEY" in st.secrets:
    gemini_key = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("已自動讀取 Gemini API Key！")
else:
    gemini_key = st.sidebar.text_input(
        "請輸入 Gemini API Key (情緒分析用):", type="password"
    )

# 1.3 模型選擇器（方便隨時切換測試）
model_choice = st.sidebar.selectbox(
    "選擇 Gemini 模型:",
    ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
    index=0,
)

if st.sidebar.button("🔄 手動刷新數據"):
    st.cache_data.clear()
    st.rerun()


# ==========================================
# 2. 數據抓取函式 (FRED, yfinance, RSS 新聞)
# ==========================================
@st.cache_data(ttl=3600)
def get_fred_data(api_key):
    fred = Fred(api_key=api_key)
    data = {
        "CPI 物價指數": fred.get_series("CPIAUCSL"),
        "10年期美債殖利率": fred.get_series("DGS10"),
        "美國失業率": fred.get_series("UNRATE"),
        "聯邦基金利率": fred.get_series("FEDFUNDS"),
    }
    # ffill 填補月數據與日數據的頻率差異，取近一年交易日
    df = pd.DataFrame(data).ffill().tail(365)
    return df


@st.cache_data(ttl=600)
def get_market_data():
    tickers = {
        "S&P 500": "^GSPC",
        "台灣加權指數": "^TWII",
        "布蘭特原油": "BZ=F",
        "美元/台幣匯率": "TWD=X",
    }
    raw = yf.download(list(tickers.values()), period="1y", progress=False)[
        "Close"
    ]
    raw.rename(columns={v: k for k, v in tickers.items()}, inplace=True)
    # 填補台美股休市日不同造成的空值，避免折線圖斷裂
    return raw.ffill()


@st.cache_data(ttl=1800)
def fetch_google_news(keyword="Federal Reserve Inflation", lang="en-US"):
    safe_keyword = quote(keyword)
    gl = "TW" if lang == "zh-TW" else "US"
    ceid = "TW:zh-Hant" if lang == "zh-TW" else "US:en"
    url = f"https://news.google.com/rss/search?q={safe_keyword}&hl={lang}&gl={gl}&ceid={ceid}"
    feed = feedparser.parse(url)
    # 同時回傳標題與連結，方便使用者點擊查證
    return [
        {"title": entry.title, "link": entry.link}
        for entry in feed.entries[:8]
    ]


# ==========================================
# 3. 頁面渲染邏輯
# ==========================================
if fred_key:
    try:
        macro_df = get_fred_data(fred_key)
        market_df = get_market_data()

        # 第一區塊：核心總經 KPI 卡片
        st.subheader("📊 關鍵總體經濟指標 (FRED)")
        col1, col2, col3, col4 = st.columns(4)

        latest_cpi = macro_df["CPI 物價指數"].dropna().iloc[-1]
        col1.metric("CPI 物價指數", f"{latest_cpi:.1f}")

        latest_rate = macro_df["10年期美債殖利率"].dropna().iloc[-1]
        rate_prev = macro_df["10年期美債殖利率"].dropna().iloc[-2]
        col2.metric(
            "10年美債殖利率",
            f"{latest_rate:.2f}%",
            f"{latest_rate - rate_prev:+.2f}%",
        )

        latest_unemp = macro_df["美國失業率"].dropna().iloc[-1]
        col3.metric("美國失業率", f"{latest_unemp:.1f}%")

        latest_fed = macro_df["聯邦基金利率"].dropna().iloc[-1]
        col4.metric("聯邦基金利率", f"{latest_fed:.2f}%")

        st.write("---")

        # 第二區塊：分頁儀表板
        tab1, tab2, tab3 = st.tabs([
            "📈 金融市場走勢 (yfinance)",
            "🏛️ 總體經濟趨勢 (FRED)",
            "📰 NLP 市場新聞與鷹鴿情緒分析",
        ])

        # 頁籤 1: 金融市場
        with tab1:
            market_choice = st.selectbox(
                "選擇金融市場標的：", market_df.columns
            )
            fig1 = px.line(
                market_df, y=market_choice, title=f"{market_choice} 近一年走勢"
            )
            fig1.update_layout(hovermode="x unified")
            st.plotly_chart(fig1, use_container_width=True)

        # 頁籤 2: 總體經濟
        with tab2:
            macro_choice = st.selectbox("選擇總體經濟指標：", macro_df.columns)
            fig2 = px.line(
                macro_df, y=macro_choice, title=f"{macro_choice} 近一年走勢"
            )
            fig2.update_layout(hovermode="x unified")
            st.plotly_chart(fig2, use_container_width=True)

        # 頁籤 3: NLP 市場新聞與情緒分析
        with tab3:
            st.subheader("📰 即時財經新聞與 LLM 鷹鴿派情緒分析")

            c_kw, c_lang = st.columns([3
