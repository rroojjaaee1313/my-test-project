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
        # 使用穩定版完整路徑，避免 v1beta 路由錯誤
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
st.markdown("### 📊 精準坪數比對 | 活案偵測 | 戰術指導")

with st.sidebar:
    st.header("⚙️ 助理管理")
    uploaded_pdf = st.file_uploader("上傳培訓教材 (PDF)", type="pdf")
    if st.button("🗑️ 清空歷史紀錄"):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.success("紀錄已清除")
        st.rerun()
    st.divider()
    st.info("💡 系統已優化：輸入地坪與建坪可獲得更精準的單價分析建議。")

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
    with st.form("love_pro_form"):
        c_name = st.text_input("🏠 案件/社區名稱", placeholder="例如：大附中電梯別墅")
        c_loc = st.text_input("📍 區域/路段", placeholder="例如：大里區東榮路")
        
        # 坪數與價格輸入區
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            c_land = st.number_input("📏 地坪 (坪)", value=30.0, step=0.1)
            c_price = st.number_input("💰 委託價格 (萬)", value=2480, step=10)
        with p_col2:
            c_build = st.number_input("🏢 建坪 (坪)", value=60.0, step=0.1)
            c_agent = st.text_input("👤 承辦人")
            
        c_note = st.text_area("🗒️ 現況備註 (如：屋主心態、帶看狀況)")
        submitted = st.form_submit_button("🚀 啟動全網掃描與精準戰術指導")

# --- 4. 核心情報邏輯 ---
if submitted:
    if not c_name or not c_loc:
        st.error("請填寫基本案件資訊")
    else:
        with col_res:
            with st.spinner("🕵️ 樂福導師正在分析市場數據與坪數價值..."):
                try:
                    # 換算單價
                    unit_price = round(c_price / c_build, 2) if c_build > 0 else 0
                    
                    prompt = f"""
                    你是一位專業的「樂福團隊」房產導師。
                    【培訓教材背景】：{context_text[:1500] if context_text else "專業房仲經驗"}
                    【目標物件】：{c_name} ({c_loc})
                    【詳細條件】：地坪 {c_land} 坪 / 建坪 {c_build} 坪 / 總價 {c_price} 萬 (建坪單價約 {unit_price} 萬)
                    
                    任務內容：
                    1. **精準行情比對**：根據此坪數與單價，分析周邊在售物件的行情是否合理。
                    2. **同業競爭掃描**：分析 591、5168、住商、永慶等平台可能的相似坪數競品。
                    3. **戰術指導**：針對承辦人 {c_agent}，給予具體的「單價優勢」說法或議價建議。
                    
                    注意：請勿自行虛構假網址，僅提供基於數據的專業分析。
                    """
                    
                    response = model.generate_content(prompt)
                    analysis_text = response.text
                    
                    st.success("✅ 樂福導師分析完成")
                    st.markdown(analysis_text)
                    
                    # 語音功能
                    audio_text = f"樂福導師提醒{c_agent}，已根據地坪{c_land}坪與建坪{c_build}坪完成深度行情分析，請查看結果。"
                    tts = gTTS(text=audio_text, lang='zh-tw')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    st.audio(audio_fp, format='audio/mp3')
                    
                    # --- 外部即時搜尋工具 (帶入坪數關鍵字) ---
                    st.divider()
                    st.subheader("🌐 即時官網活案監測 (點擊開啟)")
                    search_q = f"{c_loc}+{c_name}+{c_land}坪+{c_build}坪"
                    
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        st.link_button("🏠 5168 官網搜尋", f"https://house.5168.com.tw/list?keywords={search_q}")
                    with b2:
                        st.link_button("🏢 住商房屋搜尋", f"https://www.hbhousing.com.tw/buy-house/?q={search_q}")
                    with b3:
                        st.link_button("🏗️ 永慶房仲網搜尋", f"https://buy.yungching.com.tw/list?q={search_q}")
                    
                    # 存檔紀錄
                    save_report({
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                        "case": c_name, "agent": c_agent, "analysis": analysis_text
                    })
                    
                except Exception as e:
                    st.error(f"分析失敗: {e}")

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
