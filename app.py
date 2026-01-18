import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import os
import io
import json
from datetime import datetime

# --- 1. 系統初始化 (解決 404 與品牌設定) ---
st.set_page_config(page_title="樂福全能情報中心", layout="wide", page_icon="🦅")

try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # 使用穩定版完整路徑
        model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
    else:
        st.error("❌ 找不到 API 金鑰，請檢查 Streamlit Secrets 設定。")
        st.stop()
except Exception as e:
    st.error(f"❌ 初始化失敗: {e}")
    st.stop()

# --- 2. 數據儲存功能 ---
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
st.markdown("### 🔍 活案掃描 | 戰術指導 | 情報共享")

with st.sidebar:
    st.header("⚙️ 助理管理")
    uploaded_pdf = st.file_uploader("上傳培訓教材 (PDF)", type="pdf")
    if st.button("🗑️ 清空歷史紀錄"):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.success("紀錄已清除")
        st.rerun()
    st.divider()
    st.info("💡 系統已優化：AI 僅提供市場分析，真實網址請使用右側「即時搜尋按鈕」。")

col_in, col_res = st.columns([1, 1.3])

# PDF 教材處理
context_text = ""
if uploaded_pdf:
    try:
        reader = PdfReader(uploaded_pdf)
        for page in reader.pages:
            content = page.extract_text()
            if content: context_text += content + "\n"
        st.sidebar.success("✅ 樂福教材已載入")
    except Exception as e:
        st.sidebar.error(f"PDF 讀取失敗: {e}")

with col_in:
    st.subheader("📝 案件情報回報")
    with st.form("love_ultimate_form"):
        c_name = st.text_input("🏠 案件/社區名稱", placeholder="例如：大附中別墅")
        c_loc = st.text_input("📍 區域/路段", placeholder="例如：大里區東榮路")
        c_price = st.number_input("💰 委託價格 (萬)", value=2480, step=10)
        c_agent = st.text_input("👤 承辦同仁")
        c_note = st.text_area("🗒️ 現況備註 (如：屋主心態、帶看狀況)")
        submitted = st.form_submit_button("🚀 啟動全網掃描與戰術指導")

# --- 4. 核心情報邏輯 ---
if submitted:
    if not c_name or not c_loc:
        st.error("請填寫基本案件資訊")
    else:
        with col_res:
            with st.spinner("🕵️ 樂福導師正在分析市場活案中..."):
                try:
                    # 指令優化：不強迫生成單一連結，改為分析市場
                    prompt = f"""
                    你是一位專業的「樂福團隊」房地產導師。
                    【培訓教材背景】：{context_text[:1500] if context_text else "專業房仲經驗"}
                    【目標物件】：{c_name} | {c_loc} | 開價 {c_price} 萬
                    
                    任務內容：
                    1. **市場行情分析**：分析該區目前在售物件的行情區間，並對比此開價的競爭力。
                    2. **同業競爭概況**：分析 591、5168、住商、中信、太平洋、台灣房屋等平台可能的相似競品。
                    3. **導師戰術指導**：針對承辦人 {c_agent}，給予具體的攻堅策略或議價建議。
                    
                    注意：請勿自行虛構帶有 xxxxx 的假網址，僅提供專業分析。
                    """
                    
                    response = model.generate_content(prompt)
                    analysis_text = response.text
                    
                    st.success("✅ 樂福導師分析完成")
                    st.markdown(analysis_text)
                    
                    # 語音功能
                    audio_text = f"樂福導師提醒{c_agent}，關於{c_name}的分析已完成。請參考下方的各平台即時搜尋連結查看活案照片。"
                    tts = gTTS(text=audio_text, lang='zh-tw')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                    
                    # --- 核心改進：提供 100% 有效的官網搜尋連結 ---
                    st.divider()
                    st.subheader("🌐 即時官網活案監測 (點擊開啟)")
                    
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        st.link_button("🏠 5168 官網搜尋", f"https://house.5168.com.tw/list?keywords={c_loc}+{c_name}")
                        st.link_button("🏗️ 永慶房仲網搜尋", f"https://buy.yungching.com.tw/list?q={c_loc}+{c_name}")
                    with b2:
                        st.link_button("🏢 住商房屋搜尋", f"https://www.hbhousing.com.tw/buy-house/?q={c_loc}+{c_name}")
                        st.link_button("🇹🇼 台灣房屋搜尋", f"https://www.twhg.com.tw/object_list.php?search_word={c_loc}+{c_name}")
                    with b3:
                        st.link_button("🔍 Google 全網監測", f"https://www.google.com/search?q={c_loc}+{c_name}+在售+site:591.com.tw+OR+site:cthouse.com.tw")
                    
                    # 存檔
                    save_report({
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                        "case": c_name, "agent": c_agent, "analysis": analysis_text
                    })
                    
                except Exception as e:
                    st.error(f"分析過程發生錯誤: {e}")

# --- 5. 樂福歷史情報庫 ---
st.divider()
st.subheader("📚 樂福歷史案件情報庫 (團隊共享)")
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        for h in reversed(history[-10:]):
            with st.expander(f"📌 {h.get('case', '未知')} - {h.get('agent', '未知')} ({h.get('time', '')})"):
                st.markdown(h.get('analysis', '無內容'))
    except: pass
