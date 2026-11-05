import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from fredapi import Fred
from google import genai  # 新增：導入新版 Google GenAI SDK

# 頁面基本配置
st.set_page_config(page_title="總體經濟與金融即時儀表板", layout="wide")
st.title("🌐 全球總體經濟與金融指標即時儀表板")

# 側邊欄：設定與金鑰
st.sidebar.header("⚙️ 設定與金鑰")

# 1. FRED API Key 設定
if "FRED_API_KEY" in st.secrets:
    fred_key = st.secrets["FRED_API_KEY"]
    st.sidebar.success("已自動讀取 FRED API Key！")
else:
    fred_key = st.sidebar.text_input("請輸入你的 FRED API Key:", type="password")

# 2. Gemini API Key 設定 (新增)
if "GEMINI_API_KEY" in st.secrets:
    gemini_key = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("已自動讀取 Gemini API Key！")
else:
    gemini_key = st.sidebar.text_input("請輸入你的 Gemini API Key:", type="password")

if st.sidebar.button("手動刷新數據"):
    st.cache_data.clear()

# 1. 抓取 FRED 數據 (設快取 1 小時)
@st.cache_data(ttl=3600)
def get_fred_data(api_key):
    fred = Fred(api_key=api_key)
    data = {
        "CPI 物價指數": fred.get_series("CPIAUCSL"),
        "10年期美債殖利率": fred.get_series("DGS10"),
        "2年期美債殖利率": fred.get_series("DGS2"),
        "美國失業率": fred.get_series("UNRATE"),
        "聯邦基金利率": fred.get_series("FEDFUNDS"),
        "日本10年期國債殖利率": fred.get_series("IRLTLT01JPM156N")
    }
    df = pd.DataFrame(data).ffill().tail(365)
    df["10Y-2Y 美債利差"] = df["10年期美債殖利率"] - df["2年期美債殖利率"]
    return df

# 2. 抓取 Market 數據 (設快取 10 分鐘)
@st.cache_data(ttl=600)
def get_market_data():
    tickers = {
        "S&P 500": "^GSPC",
        "台灣加權指數": "^TWII",
        "布蘭特原油": "BZ=F",
        "美元/台幣匯率": "TWD=X",
        "黃金現貨價格": "GC=F"
    }
    raw_df = yf.download(list(tickers.values()), period="1y")
    
    if isinstance(raw_df.columns, pd.MultiIndex):
        df = raw_df["Close"]
    else:
        df = raw_df[["Close"]] if "Close" in raw_df.columns else raw_df
        
    df = df.rename(columns={v: k for k, v in tickers.items()})
    return df

# 頁面渲染邏輯
if fred_key:
    try:
        macro_df = get_fred_data(fred_key)
        market_df = get_market_data()

        # 取得最新利差數據以判斷是否倒掛
        latest_spread = macro_df["10Y-2Y 美債利差"].dropna().iloc[-1]

        # 頂部即時警示燈號
        if latest_spread < 0:
            st.warning(f"🚨 **【經濟衰退警示】美國 10 年期與 2 年期公債殖利率出現倒掛！目前利差為 {latest_spread:.2f}% (小於 0)**")
        else:
            st.success(f"🟢 **目前 10Y-2Y 美債利差為 {latest_spread:.2f}%（殖利率曲線正常，未倒掛）**")

        # 第一區塊：核心 KPI 卡片 (6 欄)
        st.subheader("📊 關鍵總體經濟指標 (FRED)")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        latest_cpi = macro_df["CPI 物價指數"].dropna().iloc[-1]
        col1.metric("CPI 物價指數", f"{latest_cpi:.1f}")
        
        latest_rate10 = macro_df["10年期美債殖利率"].dropna().iloc[-1]
        rate10_prev = macro_df["10年期美債殖利率"].dropna().iloc[-2]
        col2.metric("10年美債殖利率", f"{latest_rate10:.2f}%", f"{latest_rate10 - rate10_prev:+.2f}%")

        latest_rate2 = macro_df["2年期美債殖利率"].dropna().iloc[-1]
        rate2_prev = macro_df["2年期美債殖利率"].dropna().iloc[-2]
        col3.metric("2年美債殖利率", f"{latest_rate2:.2f}%", f"{latest_rate2 - rate2_prev:+.2f}%")

        col4.metric("10Y-2Y 利差", f"{latest_spread:.2f}%", f"{latest_spread - (macro_df['10Y-2Y 美債利差'].dropna().iloc[-2]):+.2f}%")
        
        latest_unemp = macro_df["美國失業率"].dropna().iloc[-1]
        col5.metric("美國失業率", f"{latest_unemp:.1f}%")
        
        latest_fed = macro_df["聯邦基金利率"].dropna().iloc[-1]
        col6.metric("聯邦基金利率", f"{latest_fed:.2f}%")

        # 第二區塊：互動式圖表
        st.write("---")
        st.subheader("📈 市場走勢與總體指標折線圖")
        
        tab1, tab2 = st.tabs(["金融市場走勢 (yfinance)", "總體經濟趨勢 (FRED)"])
        
        with tab1:
            market_choice = st.selectbox("選擇金融市場標的：", market_df.columns, key="market_select")
            fig1 = px.line(market_df, y=market_choice, title=f"{market_choice} 近一年走勢")
            st.plotly_chart(fig1, use_container_width=True)
            
        with tab2:
            macro_choice = st.selectbox("選擇總體經濟指標：", macro_df.columns, key="macro_select")
            fig2 = px.line(macro_df, y=macro_choice, title=f"{macro_choice} 近一年走勢")
            if macro_choice == "10Y-2Y 美債利差":
                fig2.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="零軸 (倒掛分界)", annotation_position="bottom right")
            st.plotly_chart(fig2, use_container_width=True)

        # 第三區塊：AI 總體經濟摘要 (新增)
        st.write("---")
        st.subheader("🤖 AI 智能總體經濟短評")
        
        if st.button("產生 AI 總體經濟摘要"):
            if not gemini_key:
                st.error("請先在左側欄位輸入您的 Gemini API Key，或設定於 Streamlit Secrets 中！")
            else:
                with st.spinner("Gemini 正在分析當前全球總經數據並撰寫短評..."):
                    try:
                        # 收集最新數據作為上下文
                        latest_jp = macro_df["日本10年期國債殖利率"].dropna().iloc[-1]
                        
                        prompt = f"""
                        你是一位專業的華爾街總體經濟分析師。請根據以下最新的總體經濟數據，撰寫一份約 200 字的精簡市場短評。
                        內容需包含：當前通膨與就業狀況、利率環境、美債殖利率曲線（是否倒掛）對市場的隱含意義。
                        
                        數據背景：
                        - CPI 物價指數: {latest_cpi:.1f}
                        - 10年期美債殖利率: {latest_rate10:.2f}%
                        - 2年期美債殖利率: {latest_rate2:.2f}%
                        - 10Y-2Y 美債利差: {latest_spread:.2f}% {'(發生倒掛)' if latest_spread < 0 else '(未倒掛)'}
                        - 美國失業率: {latest_unemp:.1f}%
                        - 聯邦基金利率: {latest_fed:.2f}%
                        - 日本10年期國債殖利率: {latest_jp:.2f}%
                        """
                        
                        # 使用最新 google-genai SDK 呼叫 Gemini
                        client = genai.Client(api_key=gemini_key)
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt,
                        )
                        
                        st.info(response.text)
                        
                    except Exception as ai_e:
                        st.error(f"AI 摘要產生失敗，請檢查 Gemini API Key 是否正確。錯誤訊息: {ai_e}")

    except Exception as e:
        st.error(f"數據讀取失敗，請確認 FRED API Key 是否正確。錯誤訊息: {e}")
else:
    st.info("👈 請在左側輸入您的 FRED API Key 以開啟儀表板。")
