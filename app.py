import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import os
import io
import json
from datetime import datetime

# --- 1. 系統初始化 ---
st.set_page_config(page_title="老鷹全能情報中心", layout="wide", page_icon="🦅")

try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
    else:
        st.error("❌ 找不到 API 金鑰，請檢查 Streamlit Secrets。")
        st.stop()
except Exception as e:
    st.error(f"❌ 初始化失敗: {e}")
    st.stop()

# --- 2. 數據儲存邏輯 ---
DATA_FILE = "case_reports.json"
def save_report(data):
    current_data = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except: pass
    current_data.append(data)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(current_data, f, ensure_ascii=False, indent=2)

# --- 3. 介面佈局 ---
st.title("🦅 老鷹團隊：全能 AI 智慧情報中心")

with st.sidebar:
    st.header("⚙️ 助理管理")
    uploaded_pdf = st.file_uploader("上傳培訓教材 (PDF)", type="pdf")
    if st.button("🗑️ 清空所有歷史紀錄"):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.rerun()
    st.divider()
    st.info("支援平台：5168、住商、中信、太平洋、台灣房屋、591、永慶、信義")

col_in, col_res = st.columns([1, 1.2])

# PDF 內容處理
context_text = ""
if uploaded_pdf:
    reader = PdfReader(uploaded_pdf)
    for page in reader.pages:
        context_text += page.extract_text() + "\n"
    st.sidebar.success("✅ 教材已載入")

with col_in:
    st.subheader("📝 案件情報回報")
    with st.form("ultimate_form"):
        c_name = st.text_input("🏠 案件/社區名稱")
        c_loc = st.text_input("📍 區域/路段")
        c_price = st.number_input("💰 委託價格 (萬)", value=2000)
        c_agent = st.text_input("👤 承辦人")
        c_note = st.text_area("🗒️ 現況備註")
        submitted = st.form_submit_button("🔥 啟動全網活案掃描與戰術指導")

# --- 4. 核心分析邏輯 ---
if submitted:
    if not c_name or not c_loc:
        st.error("請填寫基本案件資訊")
    else:
        with col_res:
            with st.spinner("🦅 正在掃描各家仲介官網活案中..."):
                try:
                    # 合體版指令：結合教材與活案偵測
                    prompt = f"""
                    你是一位專業的老鷹團隊導師。
                    【培訓教材背景】：{context_text[:2000]}
                    【目標物件】：{c_name} | {c_loc} | 開價 {c_price} 萬
                    
                    請執行任務：
                    1. **活案掃描**：搜尋 5168、住商、中信、太平洋、台灣房屋、591、永慶、信義。
                       - 列出目前【銷售中】的物件名稱與價格。
                       - 必須提供【有效超連結】，格式：[平台 - 標題 - 價格](網址)
                    2. **實價分析**：僅提供最新(半年內)成交區間供參考。
                    3. **導師建議**：根據教材風格，給予承辦人 {c_agent} 開發或議價的戰術指導。
                    """
                    
                    response = model.generate_content(prompt)
                    analysis_text = response.text
                    
                    st.success("✅ 深度分析完成")
                    st.markdown(analysis_text)
                    
                    # 語音功能
                    audio_text = f"導師提醒{c_agent}，關於{c_name}的活案分析已完成，請查收。"
                    tts = gTTS(text=audio_text, lang='zh-tw')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                    
                    # 搜尋補助工具
                    search_query = f"{c_loc} {c_name} 在售 (site:5168.com.tw OR site:hbhousing.com.tw OR site:cthouse.com.tw OR site:pacific.com.tw OR site:twhg.com.tw)"
                    st.link_button("🌐 前往 Google 同步監測各大官網照片", f"https://www.google.com/search?q={search_query}")
                    
                    # 存檔
                    save_report({"time": str(datetime.now()), "case": c_name, "agent": c_agent, "analysis": analysis_text})
                    
                except Exception as e:
                    st.error(f"分析失敗: {e}")

# --- 5. 團隊歷史情報庫 ---
st.divider()
st.subheader("📚 團隊歷史案件情報庫")
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        for h in reversed(history[-10:]):
            with st.expander(f"📌 {h['case']} - {h['agent']}"):
                st.markdown(h['analysis'])
    except: pass
