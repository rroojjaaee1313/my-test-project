import streamlit as st
import google.generativeai as genai
import time

# --- 1. 核心設定 ---
st.set_page_config(page_title="樂福 i智慧金牌系統", layout="wide", page_icon="🦁")

@st.cache_resource
def get_model():
    # 從 Secrets 讀取
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。請檢查 Secrets 設定。")
        return None
    
    # 配置 API
    genai.configure(api_key=api_key)
    
    # 【解決 404 的終極寫法】
    # 我們不直接寫死路徑，而是透過搜尋找到目前可用的模型名稱
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先選擇排序：1.5 flash -> 1.5 pro -> pro (舊版)
        target_model = ""
        if 'models/gemini-1.5-flash' in available_models:
            target_model = 'gemini-1.5-flash'
        elif 'models/gemini-1.5-pro' in available_models:
            target_model = 'gemini-1.5-pro'
        elif 'models/gemini-pro' in available_models:
            target_model = 'gemini-pro'
        else:
            target_model = available_models[0].split('/')[-1] if available_models else ""

        if not target_model:
            st.error("您的 API Key 似乎不支援任何生成模型。")
            return None

        # 建立模型實例
        model = genai.GenerativeModel(
            model_name=target_model,
            system_instruction="你現在是樂福團隊的i智慧金牌教練，專精房產開發與聯賣策略。"
        )
        return model
    except Exception as e:
        st.error(f"連線 Google 伺服器失敗：{e}")
        return None

# 初始化模型
model = get_model()

# --- 2. 介面介面 (簡約版，確保功能優先) ---
st.title("🏆 樂福 x i智慧：金牌聯賣戰略系統")

c1, c2 = st.columns(2)
with c1:
    city_dist = st.text_input("📍 案子在哪裡？(例如：台中大里區)")
    c_name = st.text_input("🏠 案名或社區")
with c2:
    c_price = st.text_input("💰 開價 (萬)")
    c_agent = st.text_input("👤 經紀人姓名")

submitted = st.button("🚀 啟動聯賣戰術分析")

# --- 3. 執行邏輯 ---
if submitted:
    if not model:
        st.error("模型尚未準備好，請檢查 API 設定或重新整理。")
    elif not c_agent:
        st.warning("請輸入經紀人姓名。")
    else:
        with st.spinner("🎯 正在產出戰略報告..."):
            try:
                prompt = f"""
                經紀人：{c_agent}
                物件：{city_dist} - {c_name}
                開價：{c_price}萬
                
                請產出：
                1.【聯賣戰略】：如何在永慶聯賣體系中吸引其他店組配件？
                2.【開發金句】：用誠實房價數據說服屋主的重點。
                3.【Line 聯賣推廣文案】：幫我寫一段吸引同業配件的訊息。
                """
                response = model.generate_content(prompt)
                st.success("✅ 教練報告完成！")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"分析過程發生錯誤：{e}")
