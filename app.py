import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import os
import io
import json
from datetime import datetime

# --- 1. 系統初始化 (修正 404 模型路徑與品牌更新) ---
st.set_page_config(page_title="樂福全能情報中心", layout="wide", page_icon="🦅")

try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # 使用穩定版完整路徑，確保不再出現 404
        model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
    else:
        st.error("❌ 找不到 API 金鑰，請檢查 Streamlit Secrets 設定。")
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
st.title("🦅 樂福團隊：全能 AI 智慧情報中心")

with st.sidebar:
    st.header("⚙️ 助理管理")
    uploaded_pdf = st.file_uploader("上傳培訓教材 (PDF)", type="pdf")
    if st.button("🗑️ 清空所有歷史紀錄"):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.success("紀錄已清除")
        st.rerun()
    st.divider()
    st.info("支援平台：5168、住商、中信、太平洋、台灣房屋、591、永慶、信義")

col_in, col_res = st.columns([1, 1.2])

# PDF 內容處理
context_text = ""
if uploaded_pdf:
    try:
        reader = PdfReader(uploaded_pdf)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                context_text += content + "\n"
        st.sidebar.success("✅ 教材已載入")
    except Exception as e:
        st.sidebar.error(f"PDF 讀取失敗: {e}")

with col_in:
    st.subheader("📝 案件情報回報")
    with st.form("ultimate_form"):
        c_name = st.text_input("🏠 案件/社區名稱", placeholder="例如：大附中別墅")
        c_loc = st.text_input("📍 區域/路段", placeholder="例如：大里區")
        c_price = st.number_input("💰 委託價格 (萬)", value=2000, step=10)
        c_agent = st.text_input("👤 承辦人")
        c_note = st.text_area("🗒️ 現況備註")
        submitted = st.form_submit_button("🔥 啟動全網活案掃描與戰術指導")

# --- 4. 核心分析邏輯 ---
if submitted:
    if not c_name or not c_loc:
        st.error("請填寫基本案件資訊")
    else:
        with col_res:
            with st.spinner("🦅 樂福導師正在掃描各大房仲官網活案中..."):
                try:
                    # 指令：結合樂福導師風格與活案偵測
                    prompt = f"""
                    你是一位專業的「樂福團隊」房地產導師。
                    【培訓教材背景】：{context_text[:1500] if context_text else "專業房仲經驗"}
                    【目標物件】：{c_name} | {c_loc} | 開價 {c_price} 萬
                    
                    請執行任務：
                    1. **活案掃描**：搜尋 5168、住商、中信、太平洋、台灣房屋、591、永慶、信義。
                       - 列出目前【銷售中】物件的 [平台 - 標題 - 價格](網址)。
                       - 嚴禁顯示已成交的實價登錄紀錄。
                    2. **實價分析**：僅提供半年內最新成交區間參考。
                    3. **戰術指導**：針對承辦人 {c_agent}，分析開價競爭力並給予具體戰法建議。
                    """
                    
                    response = model.generate_content(prompt)
                    analysis_text = response.text
                    
                    st.success("✅ 樂福導師分析完成")
                    st.markdown(analysis_text)
                    
                    # 語音功能
                    audio_text = f"樂福導師提醒{c_agent}，關於{c_name}的活案分析已完成，請確認競爭對手狀況。"
                    tts = gTTS(text=audio_text, lang='zh-tw')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                    
                    # 外部工具連結
                    search_query = f"{c_loc} {c_name} 在售 (site:5168.com.tw OR site:hbhousing.com.tw OR site:cthouse.com.tw OR site:pacific.com.tw OR site:twhg.com.tw OR site:591.com.tw)"
                    st.link_button("🌐 直接開啟 Google 監測最新照片", f"https://www.google.com/search?q={search_query}")
                    
                    # 存檔
                    save_report({
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                        "case": c_name, 
                        "agent": c_agent, 
                        "analysis": analysis_text
                    })
                    
                except Exception as e:
                    st.error(f"分析失敗: {e}")

# --- 5. 樂福歷史情報庫 ---
st.divider()
st.subheader("📚 樂福歷史案件情報庫")
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        for h in reversed(history[-10:]):
            with st.expander(f"📌 {h.get('case', '未知')} - {h.get('agent', '未知')} ({h.get('time', '')})"):
                st.markdown(h.get('analysis', '無內容'))
    except: pass
