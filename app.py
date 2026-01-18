import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os, io, time

# --- 1. 全台行政區資料庫 ---
TAIWAN_DATA = {
    "台中市": ["大里區", "北屯區", "西屯區", "南屯區", "太平區", "霧峰區", "烏日區", "豐原區", "中區", "東區", "南區", "西區", "北區", "潭子區", "大雅區", "神岡區", "沙鹿區", "龍井區", "梧棲區", "清水區", "大甲區", "外埔區", "大安區", "后里區", "石岡區", "東勢區", "和平區", "新社區", "大肚區"],
    "台北市": ["中正區", "萬華區", "大同區", "中山區", "松山區", "大安區", "信義區", "內湖區", "南港區", "士林區", "北投區", "文山區"],
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區", "汐止區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區"],
    "桃園市": ["桃園區", "中壢區", "大溪區", "楊梅區", "蘆竹區", "大園區", "龜山區", "八德區", "龍潭區", "平鎮區", "新屋區", "觀音區"],
    "新竹市": ["東區", "北區", "香山區"],
    "高雄市": ["新興區", "苓雅區", "鼓山區", "左營區", "楠梓區", "三民區", "鳳山區", "小港區"],
    "台南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "善化區", "新市區"],
    "其他縣市": ["基隆市", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", "台東縣", "澎湖縣", "金門縣", "連江縣"]
}

# --- 2. 系統初始化 (修正 404 模型路徑) ---
st.set_page_config(page_title="樂福情報站", layout="wide", page_icon="🦅")

@st.cache_resource
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ 找不到 API 金鑰，請檢查 Secrets 設定。")
        return None
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    try:
        # 強制使用 models/ 前綴並指向穩定版路徑
        return genai.GenerativeModel(model_name='models/gemini-1.5-flash')
    except:
        return None

model = init_gemini()

# --- 3. 介面佈局 ---
st.title("🦅 樂福團隊：全網實戰偵察系統")

# 連動選單 (必須在 form 外才能即時重新載入區域)
st.subheader("📍 物件位置")
c1_addr, c2_addr = st.columns(2)
with c1_addr:
    sel_city = st.selectbox("縣市", options=list(TAIWAN_DATA.keys()), index=0)
with c2_addr:
    sel_dist = st.selectbox("區域", options=TAIWAN_DATA[sel_city])

# 核心資訊表單
with st.form("pro_form_final_v16"):
    c3_addr, c4_addr = st.columns([3, 1])
    with c3_addr:
        road_name = st.text_input("路街名稱", placeholder="例如：熱河、東榮")
    with c4_addr:
        road_type = st.selectbox("類型", ["路", "街", "大道", "巷"])

    f1, f2, f3, f4 = st.columns(4)
    with f1: addr_sec = st.text_input("段", placeholder="段")
    with f2: addr_lane = st.text_input("巷", placeholder="巷")
    with f3: addr_alley = st.text_input("弄", placeholder="弄")
    with f4: addr_num = st.text_input("號", placeholder="號碼")

    # 地址含樓層
    c_floor = st.text_input("樓層 (住址部分)", placeholder="例如：15樓、3樓之2")
    c_name = st.text_input("案名/社區 (選填)", placeholder="例如：大附中別墅")
    
    st.divider()
    st.subheader("📏 實戰規格 (欄位已清空，無預設 0)")
    s1, s2 = st.columns(2)
    with s1:
        # 使用 text_input 讓初始畫面保持純淨空白
        c_land = st.text_input("地坪", placeholder="請輸入坪數")
        c_build = st.text_input("總建坪", placeholder="請輸入坪數")
        c_age = st.text_input("屋齡", placeholder="請輸入年分")
    with s2:
        c_inner = st.text_input("室內坪數 (主+附)", placeholder="請輸入坪數")
        c_width = st.text_input("面寬 (米)", placeholder="請輸入數字")
        c_elevator = st.selectbox("電梯", ["有", "無"])
        
    c_price = st.text_input("開價 (萬)", placeholder="請輸入價格")
    c_agent = st.text_input("承辦人", placeholder="您的姓名")
    
    submitted = st.form_submit_button("🚀 啟動全網掃描偵察")

# --- 4. 分析邏輯 ---
if submitted and model:
    with st.spinner("🕵️ 樂福導師正在偵察中..."):
        try:
            time.sleep(1) # 流量緩衝
            
            # 組合地址 (含樓層)
            full_addr = f"{sel_city}{sel_dist}{road_name}{road_type}"
            if addr_sec: full_addr += f"{addr_sec}段"
            if addr_lane: full_addr += f"{addr_lane}巷"
            if addr_alley: full_addr += f"{addr_alley}弄"
            full_addr += f"{addr_num}號{c_floor}"
            
            prompt = f"""
            你是樂福導師，執行全網實戰分析：
            地址：{full_addr} ({c_name})
            規格：屋齡{c_age}/地{c_land}/總建{c_build}/室內(主+附){c_inner}/{c_elevator}/面寬{c_width}m
            開價：{c_price}萬
            任務：分析行情競爭力、樓層價值與室內占比、指導承辦人{c_agent}談價。
            * 禁止生成假網址。
            """
            
            res = model.generate_content(prompt).text
            st.subheader(f"📊 {full_addr} 報告")
            st.markdown(res)
            
            st.divider()
            st.subheader("🌐 全網即時搜尋 (自動過濾樓層)")
            search_q = f"{full_addr}+{c_inner}坪"
            r1, r2, r3 = st.columns(3)
            with r1: st.link_button("🏠 5168 全網搜尋", f"https://house.5168.com.tw/list?keywords={search_q}")
            with r2: st.link_button("🏗️ 591 房屋交易", f"https://newhouse.591.com.tw/list?keywords={search_q}")
            with r3: st.link_button("📈 樂居實價登錄", f"https://www.leju.com.tw/search/search_result?type=1&q={full_addr}")
                
        except Exception as e:
            st.error(f"分析失敗: {e}")
