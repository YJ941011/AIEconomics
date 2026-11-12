<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI與經濟分析 - 專題應用與 Streamlit 自動化儀表板部署指南</title>
    <style>
        :root {
            --primary-color: #0f172a;
            --secondary-color: #2563eb;
            --accent-color: #d97706;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-color: #334155;
            --border-color: #e2e8f0;
            --code-bg: #1e293b;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.75;
            color: var(--text-color);
            background-color: var(--bg-color);
            margin: 0;
            padding: 24px;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: var(--card-bg);
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        h1 {
            color: var(--primary-color);
            border-bottom: 3px solid var(--secondary-color);
            padding-bottom: 12px;
            margin-top: 0;
            font-size: 1.8rem;
        }

        h2 {
            color: var(--secondary-color);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
            margin-top: 36px;
            font-size: 1.4rem;
        }

        h3 {
            color: var(--primary-color);
            margin-top: 24px;
            font-size: 1.15rem;
        }

        p, li { font-size: 1rem; }
        ul, ol { padding-left: 24px; }
        li { margin-bottom: 8px; }

        .step-box {
            background-color: #f8fafc;
            border: 1px solid var(--border-color);
            border-left: 4px solid var(--secondary-color);
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }

        .warn-box {
            background-color: #fffbeb;
            border-left: 4px solid var(--accent-color);
            padding: 16px 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }

        pre {
            background-color: var(--code-bg);
            color: #f8fafc;
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: "Courier New", Courier, monospace;
            font-size: 0.9rem;
        }

        code {
            background-color: #f1f5f9;
            color: #0f172a;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9rem;
        }

        pre code {
            background-color: transparent;
            color: inherit;
            padding: 0;
        }

        .table-container { overflow-x: auto; margin: 24px 0; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.95rem; }
        th, td { border: 1px solid var(--border-color); padding: 12px 16px; }
        th { background-color: #f1f5f9; color: var(--primary-color); font-weight: 600; }
        tr:nth-child(even) { background-color: #f8fafc; }

        footer {
            margin-top: 50px;
            text-align: center;
            font-size: 0.9em;
            color: #64748b;
            border-top: 1px solid var(--border-color);
            padding-top: 20px;
        }
    </style>
</head>
<body>

<div class="container">
    <h1>AI與經濟分析 - 課堂教學重點與 API 自動化部署指南</h1>
    <p><strong>授課教師：</strong>Bin-Tzong Chie (池秉聰) 教授 | <strong>課程單元：</strong>總體經濟資料庫 API 串接與 Streamlit 儀表板開發</p>

    <h2>一、 課堂主題：從「靜態下載」跨越到「動態 API 自動化」</h2>
    <p>在過去的分析作業中，大家都是手動到網站下載 CSV 或 Excel 檔案進行整理。本單元的核心目標，是帶領大家學會使用 <strong>API (Application Programming Interface)</strong>，讓程式碼自動跟資料庫溝通，開啓網頁即呈現最新數據。</p>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>資料類別</th>
                    <th>推薦 API 來源</th>
                    <th>是否需 API Key</th>
                    <th>涵蓋數據內容</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>總體經濟</strong></td>
                    <td>FRED API (St. Louis Fed)</td>
                    <td>需申請 (免費 32 位元 Key)</td>
                    <td>美國 CPI、失業率、聯邦基金利率、10年期公債殖利率</td>
                </tr>
                <tr>
                    <td><strong>國際匯率</strong></td>
                    <td>Frankfurter API</td>
                    <td>免 API Key (原生支援 CORS)</td>
                    <td>EUR, JPY, GBP, CAD 等主要貨幣即時與歷史匯率</td>
                </tr>
                <tr>
                    <td><strong>大宗商品/美股</strong></td>
                    <td>Alpha Vantage / Yahoo Finance</td>
                    <td>需申請 (免費 Key)</td>
                    <td>WTI 原油、天然氣、黃金現貨價格與個股數據</td>
                </tr>
                <tr>
                    <td><strong>財經新聞</strong></td>
                    <td>NewsAPI</td>
                    <td>需申請 (免費 Key)</td>
                    <td>聯準會政策動態、CPI 通膨率即時新聞快訊</td>
                </tr>
            </tbody>
        </table>
    </div>

    <h2>二、 部署流程四步驟：GitHub + Streamlit Community Cloud</h2>
    
    <div class="step-box">
        <h3>1. 申請 FRED API Key</h3>
        <ul>
            <li>連線至 <a href="https://fred.stlouisfed.org/docs/api/api_key.html" target="_blank">FRED API Key 申請頁面</a>。</li>
            <li>使用 Google 帳號登入並點擊 Request API Key。</li>
            <li>取得 32 位元的英文與數字混合金鑰（妥善保存，切勿硬編碼於前端）。</li>
        </ul>
    </div>

    <div class="step-box">
        <h3>2. Fork 老師的 GitHub 專案倉庫</h3>
        <ul>
            <li>開啟課程專案，點擊右上角 <strong>Fork</strong> 複製一份副本至個人 GitHub 帳號。</li>
            <li>確認專案結構中的 <code>demo/app.py</code> 及 <code>requirements.txt</code>。</li>
        </ul>
    </div>

    <div class="step-box">
        <h3>3. 部署至 Streamlit Cloud</h3>
        <ul>
            <li>登入 <a href="https://streamlit.io/cloud" target="_blank">Streamlit Community Cloud</a>，授權連結 GitHub 帳號。</li>
            <li>點擊 <strong>Create app</strong>，選擇剛才 Fork 的倉庫，路徑指定為 <code>demo/app.py</code> 並發布。</li>
        </ul>
    </div>

    <div class="step-box">
        <h3>4. 安全性設定 (Secrets 管理 API Key)</h3>
        <p>為避免金鑰洩露，請點擊 Streamlit App 右下角 <code>Settings -> Secrets</code>，輸入以下設定：</p>
        <pre><code># Streamlit Secrets 設定範例
FRED_API_KEY = "你的32位元FRED金鑰"
GEMINI_API_KEY = "你的Google_AI_Studio金鑰"</code></pre>
    </div>

    <h2>三、 進階功能提示詞 (Prompts) 與 Python 程式碼範例</h2>

    <h3>提示詞 1：新增黃金與日本 10 年期國債殖利率</h3>
    <pre><code>我想在目前的 Streamlit 儀表板中新增「黃金現貨價格」與「日本 10 年期國債殖利率」，請協助修改 app.py，結合 yfinance 與 FRED API 抓取資料並維持美觀排版。</code></pre>

    <h3>提示詞 2：計算美債殖利率倒掛與警示燈號</h3>
    <pre><code>請協助修改 Python 程式碼，使用 FRED API 計算「10年期美債殖利率 - 2年期美債殖利率」的利差。若利差小於 0，請在 Streamlit 儀表板上顯示紅色警示燈號，並繪製歷史利差摺線圖。</code></pre>

    <div class="warn-box">
        ⚠️ <strong>課堂資安與 Debug 警示：</strong>
        <ul>
            <li><strong>資安注意事項：</strong> API Key 視同提款機密碼！絕不可以隨意張貼在公開網頁或程式碼中。GitHub 會有自動掃描機制，若洩漏金鑰可能導致帳號遭暫停。</li>
            <li><strong>Gemini SDK 版本問題：</strong> 呼叫 Google AI 寫總評時，若出現模型找不到或額度限制，請將程式碼中的模型名稱修飾為 <code>gemini-2.5-flash</code> 或 <code>gemini-3.8-flash</code>，並確認 <code>requirements.txt</code> 包含 <code>google-genai</code>。</li>
        </ul>
    </div>

    <footer>
        <p>© 2026 淡江大學經濟學系 Bin-Tzong Chie 教授 | AI與經濟分析 課程教學資源庫</p>
    </footer>
</div>

</body>
</html>
