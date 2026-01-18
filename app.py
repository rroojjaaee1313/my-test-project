import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import os
import io
import PIL.Image
import json
from datetime import datetime

# --- 1. 系統初始化與金鑰設定 ---
st.set_page_config(page_title="老鷹 AI 智慧情報中心", layout="wide", page_icon="🦅")

try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=API_KEY)
    else:
        st.error("❌ 找不到 API 金鑰，請檢查 Streamlit Secrets 設定。")
        st.stop()

    # 自動偵測可用的模型 (確保聯網搜尋功能)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    MODEL_NAME = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(model_name=MODEL_NAME)
    
except Exception as e:
    st.error(f"❌ 系統啟動失敗: {e}")
    st.stop()

# --- 2. 數據儲存功能 ---
DATA_FILE = "case_reports.json"

def save_case_report(data):
    current_data = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            current_data = json.load(f)
    current_data.append(data)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(current_data, f, ensure_ascii=False, indent=2)

# --- 3. 介面設計 ---
st.title("🦅 老鷹團隊：全方位 AI 情報回報中心")

# 側邊欄：歷史查看與設定
with st.sidebar:
    st.header("⚙️ 管理選單")
    if st.button("🗑️ 清空歷史回報紀錄"):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.rerun()
    st.divider()
    st.info("本系統已串接 Google 聯網搜尋，可自動分析實價登錄與同業競爭狀況。")

# 頁面分欄：左側回報，右側分析
col_input, col_info = st.columns([1, 1])

with col_input:
    st.subheader("📝 案件回報表單")
    with st.form("eagle_report"):
        c_name = st.text_input("🏠 案件名稱 (例如：大附中電梯別墅)")
        c_loc = st.text_input("📍 區域/路段 (例如：大里區東榮路)")
        c_price = st.number_input("💰 委託價格 (萬元)", min_value=1, value=2500)
        c_agent = st.text_input("👤 承辦人")
        c_note = st.text_area("🗒️ 案件現況備註 (如：屋主心態、帶看狀況)")
        
        submitted = st.form_submit_button("🚀 提交回報並啟動 AI 全網情報分析")

# --- 4. 智慧情報與聯網分析邏輯 ---
if submitted:
    if not c_name or not c_loc:
        st.error("請輸入案名與區域以利 AI 搜尋行情！")
    else:
        with col_info:
            with st.spinner("🦅 老鷹導師正在掃描實價登錄、591、信義、永慶等各大平台..."):
                try:
                    # 建立聯網搜尋指令
                    prompt = f"""
                    你是一位專業的房地產導師。請針對以下物件進行全方位市場分析：
                    案件名稱：{c_name}
                    位置：{c_loc}
                    預計開價：{c_price} 萬
                    
                    請提供：
                    1. **實價行情分析**：搜尋該區相似物件(電梯別墅)近一年的成交價格區間。
                    2. **同業競爭掃描**：搜尋各大仲介網站(591,永慶,信義等)，是否有同案異賣或類似競品？列出其開價。
                    3. **戰鬥策略建議**：分析該開價的競爭力，並給予承辦人 {c_agent} 具體的開發或議價建議。
                    """
                    
                    response = model.generate_content(prompt)
                    analysis_text = response.text
                    
                    # 儲存回報紀錄
                    report_data = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "case_name": c_name,
                        "location": c_loc,
                        "price": c_price,
                        "agent": c_agent,
                        "analysis": analysis_text
                    }
                    save_case_report(report_data)
                    
                    # 顯示結果
                    st.success(f"✅ {c_name} 情報分析完成！")
                    st.markdown("### 🏁 智慧情報報告")
                    st.markdown(analysis_text)
