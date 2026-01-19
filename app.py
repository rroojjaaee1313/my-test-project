import streamlit as st
import google.generativeai as genai
import time
import urllib.parse

# --- 1. 核心初始化 (強制避開 v1beta 錯誤路徑) ---
st.set_page_config(page_title="樂福 i智慧金牌系統", layout="wide", page_icon="🦁")

@st.cache_resource
def init_gemini():
    # 確保從 Secrets 讀取
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。請檢查 Streamlit 的 Secrets 設定。")
        return None
    
    # 配置 API
    genai.configure(api_key=api_key)
    
    try:
        # 【解決 404 的關鍵】: 
        # 不要使用 models/ 前綴，也不要指定任何 api_version。
        # 直接指定 'gemini-1.5-flash' 作為模型名稱。
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction="你現在是樂福團隊的i智慧金牌教練，專精房產開發與聯賣策略。"
        )
        
        # 進行一個微型的連線測試，確保模型真的可用
        model.generate_content("test")
        return model
    except Exception as e:
        # 如果還是 404，嘗試備用方案：使用 'gemini-pro'
        try:
            return genai.GenerativeModel(model_name='gemini-pro')
        except:
            st.error(f"API 呼叫失敗，請確認 API 金鑰是否為最新的 PRO 權限。錯誤細節：{e}")
            return None

model = init_gemini()

# --- 2. 介面設計 (保持原有專業排版) ---
st.title("🦁 樂福 x i智慧：金牌聯賣戰略系統")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        sel_city = st.selectbox("📍 選擇縣市", ["台中市", "台北市", "新北市"])
        c_name = st.text_input("案名/社區")
    with col2:
        sel_dist = st.text_input("📍 區域 (例如：大里區)")
        c_agent = st.text_input("執行經紀人姓名")

    st.divider()
    s1, s2, s3 = st.columns(3)
    with s1: c_build = st.text_input("總建坪")
    with s2: c_age = st.text_input("屋齡")
    with s3: c_price = st.text_input("開價(萬)")

    submitted = st.button("🚀 啟動聯賣戰略分析")

# --- 3. 核心運作邏輯 ---
if submitted:
    if not model:
        st.error("系統模型載入失敗，請檢查 API Key 設定。")
    else:
        with st.spinner("🎯 正在同步聯賣數據與教練戰術..."):
            try:
                # 建立戰略 Prompt
                prompt = f"""
                經紀人：{c_agent}
                物件：{sel_city}{sel_dist} - {c_name}
                數據：屋齡{c_age}年 / 總建{c_build}坪 / 開價{c_price}萬。
                
                請產出：
                1.【聯賣攻略】：如何在永慶聯賣體系中吸引其他店組配件？
                2.【開發金句】：用誠實房價數據說服屋主的重點。
                3.【Line 聯賣推廣文案】：包含吸睛標題與物件重點。
                """
                
                response = model.generate_content(prompt)
                st.markdown(response.text)
                
                st.success("✅ 教練戰略已傳達！")
                
            except Exception as e:
                st.error(f"發生錯誤：{e}")
                st.info("💡 提示：若持續出現 404，請登入 Google AI Studio 檢查您的 API Key 是否已啟用 Gemini 1.5 系列的存取權。")
