import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import os
import io
import json
from datetime import datetime

# --- 1. 系統初始化 (修正 404 模型路徑與自動偵測) ---
st.set_page_config(page_title="老鷹全能情報中心", layout="wide", page_icon="🦅")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ 找不到 API 金鑰，請檢查 Streamlit Secrets 設定。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 自動偵測可用模型邏輯，避免 404 錯誤
@st.cache_resource
def get_best_model():
    try:
        # 優先嘗試完整路徑名稱
        target_model = 'models/gemini-1.5-flash'
        # 測試模型是否可用
        m = genai.get_model(target_model)
        return genai.GenerativeModel(model_name=target_model)
    except:
        try:
            # 若失敗，列出所有支援 generateContent 的模型並選取第一個
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            return genai.GenerativeModel(model_name=models[0])
        except Exception as e:
            st.error(f"❌ 無法連接至任何 Gemini 模型: {e}")
            return None

model = get_best_model()

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
    if st.button("🗑️ 清空歷史紀錄"):
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
            if content: context_text += content + "\n"
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
    if not model:
        st.error("模型尚未就緒，請檢查 API 設定。")
    elif not c_name or not c_loc:
        st.error("請填寫基本案件資訊")
    else:
        with col_res:
            with st.spinner("🦅 老鷹導師正在掃描各大房仲官網活案中..."):
                try:
                    prompt = f"""
                    你是一位專業的老鷹團隊房產導師。
                    背景教材：{context_text[:1500] if context_text else "專業房地產銷售經驗"}
                    
                    任務：針對【{c_loc} {c_name}】，開價 {c_price} 萬進行分析：
                    1. **活案掃描**：搜尋 5168、住商、中信、太平洋、台灣房屋、591。
                       - 列出目前【銷售中】物件的 [平台 - 標題 - 價格](網址)。
                       - 嚴禁顯示已成交的實價登錄。
                    2. **競爭力建議**：針對承辦人 {c_agent}，分析此開價與對手的強弱，給予具體戰術。
                    """
                    response = model.generate_content(prompt)
                    st.success("✅ 分析完成")
                    st.markdown(response.text)
                    
                    # 語音
                    audio_text = f"導師提醒{c_agent}，關於{c_name}的分析已完成。"
                    tts = gTTS(text=audio_text, lang='zh-tw')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                    
                    # 搜尋補助連結
                    search_query = f"{c_loc} {c_name} 在售 (site:5168.com.tw OR site:hbhousing.com.tw OR site:cthouse.com.tw OR site:pacific.com.tw OR site:twhg.com.tw)"
                    st.link_button("🌐 開啟 Google 即時監測", f"https://www.google.com/search?q={search_query}")
                    
                    save_report({"time": datetime.now().strftime("%Y-%m-%d %H:%M"), "case": c_name, "agent": c_agent, "analysis": response.text})
                except Exception as e:
                    st.error(f"分析失敗: {e}")

# --- 5. 歷史庫 ---
st.divider()
st.subheader("📚 團隊歷史案件情報庫")
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        history = json.load(f)
    for h in reversed(history[-10:]):
        with st.expander(f"📌 {h.get('case')} - {h.get('agent')} ({h.get('time')})"):
            st.markdown(h.get('analysis'))
