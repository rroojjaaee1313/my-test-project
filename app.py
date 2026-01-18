import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os, io, json
from datetime import datetime

# --- 1. 系統初始化 ---
st.set_page_config(page_title="樂福情報站", layout="wide", page_icon="🦅")

@st.cache_resource
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets: return None
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

model = init_gemini()

# --- 2. 介面佈局 ---
st.title("🦅 樂福團隊：精準偵察系統")

with st.sidebar:
    st.header("⚙️ 設定")
    if st.button("🗑️ 清除紀錄"):
        if os.path.exists("case_reports.json"): os.remove("case_reports.json")
        st.rerun()

col_in, col_res = st.columns([1, 1.2])

with col_in:
    with st.form("pro_form"):
        c_name = st.text_input("🏠 案名", placeholder="社區名稱")
        c_loc = st.text_input("📍 路段", placeholder="大里區東榮路")
        
        c1, c2 = st.columns(2)
        with c1:
            c_land = st.number_input("📏 地坪", value=30.0)
            c_build_total = st.number_input("🏢 總建", value=65.0)
            c_age = st.number_input("🗓️ 屋齡", value=15)
        with c2:
            c_build_inner = st.number_input("🏠 內淨", value=55.0)
            c_width = st.number_input("↔️ 面寬", value=5.0)
            c_elevator = st.selectbox("🛗 電梯", ["有", "無"])
            
        c_price = st.number_input("💰 開價 (萬)", value=2500)
        c_agent = st.text_input("👤 承辦")
        submitted = st.form_submit_button("🚀 啟動掃描")

# --- 3. 精準分析邏輯 ---
if submitted and model:
    with col_res:
        with st.spinner("分析中..."):
            try:
                # 數據摘要
                inner_pct = round((c_build_inner / c_build_total) * 100, 1)
                unit_p = round(c_price / c_build_total, 2)
                
                prompt = f"""
                你是樂福團隊導師，請精簡分析：
                物件：{c_loc}{c_name} (屋齡{c_age}年/地{c_land}/總建{c_build_total}/內淨{c_build_inner}/{c_elevator}/面寬{c_width}m)
                價格：{c_price}萬 (單價{unit_p}萬)
                
                請回覆：
                1.【市場行情】比對相似坪數/屋齡活案。
                2.【優劣點】室內占比{inner_pct}%與規格分析。
                3.【戰術建議】指導承辦人{c_agent}如何談價。
                不需贅字。
                """
                
                res = model.generate_content(prompt).text
                st.subheader(f"📊 {c_name} 情報報告")
                st.markdown(res)
                
                # 語音
                tts = gTTS(f"樂福導師分析完成，{c_agent}請查收。", lang='zh-tw')
                fp = io.BytesIO(); tts.write_to_fp(fp)
                st.audio(fp, format='audio/mp3')
                
                # 跳轉搜尋
                st.divider()
                st.link_button("🌐 開啟 5168 精準搜尋", f"https://house.5168.com.tw/list?keywords={c_loc}+{c_name}+{c_build_inner}坪")
                
            except Exception as e:
                st.error(f"錯誤: {e}")
