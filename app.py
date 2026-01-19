import streamlit as st
import google.generativeai as genai
import time
import urllib.parse
from google.api_core import exceptions

# --- 1. 全台行政區資料庫 (保持原有架構) ---
TAIWAN_DATA = {
    "台中市": ["大里區", "北屯區", "西屯區", "南屯區", "太平區", "霧峰區", "烏日區", "豐原區", "中區", "東區", "南區", "西區", "北區", "潭子區", "大雅區", "神岡區", "沙鹿區", "龍井區", "梧棲區", "清水區", "大甲區", "外埔區", "大安區", "后里區", "石岡區", "東勢區", "和平區", "新社區", "大肚區"],
    "台北市": ["中正區", "萬華區", "大同區", "中山區", "松山區", "大安區", "信義區", "內湖區", "南港區", "士林區", "北投區", "文山區"],
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區", "汐止區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區"],
    "桃園市": ["桃園區", "中壢區", "大溪區", "楊梅區", "蘆竹區", "大園區", "龜山區", "八德區", "龍潭區", "平鎮區", "新屋區", "觀音區"],
    "高雄市": ["新興區", "苓雅區", "鼓山區", "左營區", "楠梓區", "三民區", "鳳山區", "小港區"],
    "台南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "善化區", "新市區"]
}

# --- 2. 核心初始化 (結合樂福教練 + i智慧經紀人) ---
st.set_page_config(page_title="樂福 i智慧金牌系統", layout="wide", page_icon="🦁")

@st.cache_resource
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ 找不到 API 金鑰。")
        return None
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # --- 混合人設指令 ---
    instruction = """
    你現在是「樂福團隊」旗下的【i智慧金牌教練】。
    你結合了「永慶i智慧系統」的精準數據觀與「樂福金牌教練」的實戰開發戰力。
    
    你的回覆風格：
    1. 科技導向：會提到「系統配案」、「大數據分析」、「聯賣動能」。
    2. 誠實專業：強調實價登錄的解讀，不誇大，但能從數據中找出說服屋主的破綻。
    3. 實戰節奏：針對經紀人提供的物件，直接給予開發與銷售的 SOP。
    4. 團隊感：稱呼使用者為「專業經紀人」或「夥伴」。
    
    分析架構必須包含：
    - 【i智慧系統偵查報告】：數據面的優劣分析。
    - 【教練開發攻心計】：針對屋主的心理開發術。
    - 【精準銷售地圖】：哪些特質的客群會買這間。
    - 【金牌激勵金句】：結尾一段正能量鼓勵。
    """
    
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=instruction
        )
        return model
    except Exception as e:
        st.error(f"系統啟動失敗：{e}")
        return None

model = init_gemini()

# --- 3. 介面設計 ---
st.title("🦁 樂福 x i智慧：金牌經紀人作戰系統")
st.success("結合 i智慧系統數據力 + 樂福教練開發力，助你成交不間斷！")

ca, cb = st.columns(2)
with ca:
    sel_city = st.selectbox("📍 縣市", options=list(TAIWAN_DATA.keys()))
with cb:
    sel_dist = st.selectbox("📍 區域", options=TAIWAN_DATA[sel_city])

with st.form("i_wisdom_coach_form"):
    c1, c2 = st.columns([3, 1])
    with c1: road_name = st.text_input("路街名稱", placeholder="例如：西屯路、忠孝東路")
    with c2: road_type = st.selectbox("類型", ["路", "街", "大道", "巷"])
    
    f1, f2, f3, f4 = st.columns(4)
    with f1: addr_sec = st.text_input("段")
    with f2: addr_num = st.text_input("號")
    with f3: c_floor = st.text_input("樓層")
    with f4: c_name = st.text_input("社區案名")
    
    st.divider()
    st.subheader("📊 物件規格與數據")
    s1, s2, s3, s4 = st.columns(4)
    with s1: c_land = st.text_input("地坪")
    with s2: c_build = st.text_input("總建坪")
    with s3: c_age = st.text_input("屋齡")
    with s4: c_price = st.text_input("開價(萬)")
    
    c_agent = st.text_input("執行經紀人姓名", placeholder="請輸入姓名")
    
    submitted = st.form_submit_button("🚀 啟動 i智慧大數據與教練分析")

# --- 4. 運作邏輯 ---
if submitted:
    if not model:
        st.error("系統尚未連接 API。")
    elif not c_agent or not road_name:
        st.warning("請填寫經紀人姓名與完整路名以進行系統偵查。")
    else:
        with st.spinner(f"📡 正在連線 i智慧系統並請教金牌教練中..."):
            try:
                full_addr = f"{sel_city}{sel_dist}{road_name}{road_type}{addr_sec}段{addr_num}號{c_floor}"
                
                prompt = f"""
                執行經紀人：{c_agent}
                分析物件：{full_addr} ({c_name})
                物件數據：屋齡{c_age}年 / 總建{c_build}坪 / 地坪{c_land}坪 / 開價{c_price}萬。

                請以【i智慧金牌教練】身分，產出以下分析：
                1. 以 i智慧系統視角，評估此物件在該區「實價登錄」中的競爭落點。
                2. 給予經紀人「開發端」的建議：如何與屋主談「誠實房價」並取得專任。
                3. 提供 3 個針對此物件的「i智慧配案」精準買方畫像。
                4. 設計 3 組具備永慶風格且能吸引眼球的銷售標題。
                """
                
                # 自動重試
                response = None
                for i in range(3):
                    try:
                        response = model.generate_content(prompt)
                        break
                    except exceptions.ResourceExhausted:
                        time.sleep(3)
                        continue
                
                if response:
                    st.markdown(f"### 📋 {c_agent} 專屬作戰報告")
                    st.markdown(response.text)
                    
                    st.divider()
                    st.subheader("🛠️ i智慧延伸偵察工具")
                    q_query = urllib.parse.quote(f"{sel_city}{sel_dist}{road_name}")
                    r1, r2, r3 = st.columns(3)
                    with r1: st.link_button("📊 查成交實價", f"https://www.leju.com.tw/search/search_result?type=1&q={q_query}")
                    with r2: st.link_button("🏘️ 查永慶/同業競爭案", f"https://house.5168.com.tw/list?keywords={q_query}")
                    with r3: st.link_button("🗺️ 地圖導航偵查", f"https://www.google.com/maps/search/{q_query}")

            except Exception as e:
                st.error(f"系統異常：{e}")
