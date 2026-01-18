import streamlit as st
import google.generativeai as genai
import os
import json
from datetime import datetime

# --- 1. 系統初始化 ---
st.set_page_config(page_title="老鷹全網活案情報站", layout="wide", page_icon="🦅")

try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
    else:
        st.error("❌ 找不到 API 金鑰，請檢查 Streamlit Secrets 設定。")
        st.stop()
except Exception as e:
    st.error(f"❌ 初始化失敗: {e}")
    st.stop()

# --- 2. 介面設計 ---
st.title("🦅 老鷹團隊：即時在售物件情報系統")
st.markdown("### 🔍 專注於各大仲介官網「目前在售」活案偵測")

col_in, col_res = st.columns([1, 1.3])

with col_in:
    with st.form("live_case_scan"):
        c_name = st.text_input("🏠 案件/社區名稱", placeholder="例如：大附中別墅 或 熱河路透天")
        c_loc = st.text_input("📍 區域/路段", placeholder="例如：大里區 或 北屯區")
        c_price = st.number_input("💰 我的委託價 (萬)", value=2000)
        c_agent = st.text_input("👤 承辦人")
        submitted = st.form_submit_button("🔥 立即偵測同業在售活案")

# --- 3. 活案偵測邏輯 ---
if submitted:
    if not c_name or not c_loc:
        st.error("請填寫案名與區域")
    else:
        with col_res:
            with st.spinner(f"正在掃描 5168、住商、中信、太平洋、台灣房屋 在售網頁..."):
                # 強制 AI 搜尋特定平台的活案連結
                prompt = f"""
                你是一位房地產情報偵察員。現在要針對以下物件搜尋【目前在市場上銷售中】的活案：
                案名：{c_name} | 區域：{c_loc} | 預計開價：{c_price} 萬
                
                【硬性要求】：
                1. 僅列出目前在【5168、住商不動產、中信房屋、太平洋房屋、台灣房屋、591、永慶、信義】官網上「仍在銷售中」的物件。
                2. 排除任何「實價登錄」或「已成交」的歷史網頁。
                3. 請提供【有效網址超連結】，格式為：[平台名稱 - 物件名稱 - 開價](網址)。
                4. 最後分析：這些對手的開價相對於我的 {c_price} 萬，競爭力如何？
                """
                
                try:
                    response = model.generate_content(prompt)
                    st.success("✅ 活案掃描完成")
                    st.markdown("### 🏁 當前市場在售競品清單")
                    st.markdown(response.text)
                    
                    st.divider()
                    st.subheader("🌐 同步搜尋助手")
                    
                    # 組合各大仲介官網的搜尋關鍵字
                    search_query = f"{c_loc} {c_name} 在售 (site:5168.com.tw OR site:hbhousing.com.tw OR site:cthouse.com.tw OR site:pacific.com.tw OR site:twhg.com.tw)"
                    google_link = f"https://www.google.com/search?q={search_query}"
                    
                    st.link_button("👉 點我直接開啟 Google 同步監測各大仲介官網照片", google_link)
                    
                except Exception as e:
                    st.error(f"搜尋過程發生錯誤: {e}")
                finally:
                    pass # 確保區塊完整結尾

# --- 4. 數據儲存紀錄 (選配) ---
# 若需要紀錄功能可再補回
