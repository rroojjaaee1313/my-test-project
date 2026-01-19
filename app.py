import streamlit as st
import google.generativeai as genai
import time
import urllib.parse

# --- 1. 初始化與 404 錯誤修復 ---
st.set_page_config(page_title="樂福 i智慧金牌系統", layout="wide", page_icon="🦁")

@st.cache_resource
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ 找不到 API 金鑰。請在 Streamlit Secrets 設定 GEMINI_API_KEY")
        return None
    
    # 【關鍵修復】配置 API 金鑰
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 建立系統指令
    instruction = """
    你現在是「樂福團隊」的【i智慧金牌教練】。
    你精通永慶聯賣系統與大數據分析。
    你的任務：產出精準的房產戰略，並協助經紀人撰寫高質感的「聯賣推廣訊息」。
    語氣：專業、激勵、充滿系統化的洞察力。
    """
    
    try:
        # 【關鍵修復】直接使用模型名稱字串，不加 'models/' 前綴，這能避開 v1beta 的路徑錯誤
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash', 
            system_instruction=instruction
        )
        return model
    except Exception as e:
        st.error(f"系統啟動失敗，請聯繫開發人員。錯誤：{e}")
        return None

model = init_gemini()

# --- 2. 行政區資料 (簡化顯示) ---
TAIWAN_DATA = {"台中市": ["大里區", "北屯區", "西屯區", "南屯區", "太平區"], "台北市": ["中正區", "大安區", "信義區"], "新北市": ["板橋區", "中和區", "永和區"]} # 這裡可自行補全

# --- 3. 介面設計 ---
st.title("🦁 樂福 x i智慧：金牌聯賣戰略系統")

# 輸入區域
with st.container():
    c1, c2, c3 = st.columns([2,2,2])
    with c1: sel_city = st.selectbox("📍 縣市", options=list(TAIWAN_DATA.keys()))
    with c2: sel_dist = st.selectbox("📍 區域", options=TAIWAN_DATA.get(sel_city, ["請選擇"]))
    with c3: c_name = st.text_input("案名/社區", placeholder="例如：大附中別墅")

    r1, r2, r3, r4 = st.columns(4)
    with r1: c_build = st.text_input("總建坪")
    with r2: c_age = st.text_input("屋齡")
    with r3: c_price = st.text_input("開價(萬)")
    with r4: c_agent = st.text_input("經紀人姓名")

    submitted = st.button("🚀 啟動金牌戰略分析")

# --- 4. 核心邏輯與聯賣文案生成 ---
if submitted:
    if model:
        with st.spinner("🎯 正在與聯賣系統同步並請教金牌教練..."):
            try:
                # 準備 Prompt
                prompt = f"""
                執行人：{c_agent}
                物件：{sel_city}{sel_dist} - {c_name}
                數據：屋齡{c_age}年 / 總建{c_build}坪 / 開價{c_price}萬。

                請提供：
                1.【聯賣戰略】：這間房子在聯賣體系中要如何跟友店合作最快成交？
                2.【開發建議】：如何用數據說服屋主？
                3.【Line 聯賣群組推廣文案】：請寫一段極具吸引力、讓友店看了想配件的簡短文案，包含社區亮點與您的聯絡資訊。
                """
                
                # 呼叫 API
                response = model.generate_content(prompt)
                
                if response:
                    st.success("✅ 分析報告與聯賣文案已生成！")
                    st.markdown(response.text)
                    
                    # 互動功能
                    st.divider()
                    st.subheader("📋 聯賣一鍵行動")
                    st.info("您可以直接複製上方的【Line 聯賣群組推廣文案】發送到您的聯賣群組！")
                    
            except Exception as e:
                st.error(f"偵測到 API 設定問題：{e}")
                st.info("💡 提示：這通常是因為 API Key 沒有設定好，或是 Google 伺服器暫時繁忙。")
