import streamlit as st
import google.generativeai as genai
import time
import urllib.parse

# --- 1. 全台行政區資料庫 (實戰連動版) ---
TAIWAN_DATA = {
    "台中市": ["大里區", "北屯區", "西屯區", "南屯區", "太平區", "霧峰區", "烏日區", "豐原區", "中區", "東區", "南區", "西區", "北區", "潭子區", "大雅區", "神岡區", "沙鹿區", "龍井區", "梧棲區", "清水區", "大甲區", "外埔區", "大安區", "后里區", "石岡區", "東勢區", "和平區", "新社區", "大肚區"],
    "台北市": ["中正區", "萬華區", "大同區", "中山區", "松山區", "大安區", "信義區", "內湖區", "南港區", "士林區", "北投區", "文山區"],
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區", "汐止區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區"],
    "桃園市": ["桃園區", "中壢區", "大溪區", "楊梅區", "蘆竹區", "大園區", "龜山區", "八德區", "龍潭區", "平鎮區", "新屋區", "觀音區"],
    "高雄市": ["新興區", "苓雅區", "鼓山區", "左營區", "楠梓區", "三民區", "鳳山區", "小港區"],
    "台南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "善化區", "新市區"],
    "其他縣市": ["基隆市", "新竹市", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", "台東縣", "澎湖縣", "金門縣", "連江縣"]
}

# --- 2. 核心初始化 (強制穩定正式版路徑) ---
st.set_page_config(page_title="樂福情報站 PRO", layout="wide", page_icon="🦅")

@st.cache_resource
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ 找不到 API 金鑰，請檢查 Secrets 設定。")
        return None
    
    # [核心修復] 直接強制配置版本與路徑
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    try:
        # 使用正式版模型名稱，SDK 會自動選擇穩定路由
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"模型啟動異常: {e}")
        return None

model = init_gemini()

# --- 3. 介面佈局 (經紀人實戰視角) ---
st.title("🦅 樂福團隊：專業經紀人偵察系統")

# 行政區連動：放在 form 外才能即時更新區域
ca, cb = st.columns(2)
with ca:
    sel_city = st.selectbox("📍 選擇縣市", options=list(TAIWAN_DATA.keys()), index=0)
with cb:
    sel_dist = st.selectbox("📍 選擇區域", options=TAIWAN_DATA[sel_city])

with st.form("broker_pro_v1"):
    c3, c4 = st.columns([3, 1])
    with c3: road_name = st.text_input("路街名稱", placeholder="例如：熱河、東榮")
    with c4: road_type = st.selectbox("類型", ["路", "街", "大道", "巷"])

    f1, f2, f3, f4 = st.columns(4)
    with f1: addr_sec = st.text_input("段")
    with f2: addr_lane = st.text_input("巷")
    with f3: addr_alley = st.text_input("弄")
    with f4: addr_num = st.text_input("號", placeholder="必填")

    c_floor = st.text_input("樓層 (地址一部分)", placeholder="例如：15樓、3樓之2")
    c_name = st.text_input("案名/社區 (選填)", placeholder="例如：大附中別墅")
    
    st.divider()
    st.subheader("📏 物件實戰規格 (欄位已清空，無預設 0)")
    s1, s2 = st.columns(2)
    with s1:
        # 使用 text_input 讓初始狀態完全空白，不用刪除預設的 0
        c_land = st.text_input("地坪", placeholder="直接輸入數字")
        c_build = st.text_input("總建坪", placeholder="直接輸入數字")
        c_age = st.text_input("屋齡 (年)", placeholder="直接輸入數字")
    with s2:
        c_inner = st.text_input("室內坪數 (主+附)", placeholder="直接輸入數字")
        c_width = st.text_input("面寬 (米)", placeholder="直接輸入數字")
        c_elevator = st.selectbox("電梯", ["有", "無"])
        c_road = st.text_input("路寬 (米)", placeholder="直接輸入數字")
        
    c_price = st.text_input("開價 (萬)", placeholder="直接輸入金額")
    c_agent = st.text_input("承辦經紀人", placeholder="您的姓名")
    
    submitted = st.form_submit_button("🚀 啟動專業偵察分析報告")

# --- 4. 經紀人專業分析邏輯 ---
if submitted and model:
    with st.spinner(f"🕵️ 導師正在為 {c_agent} 進行實戰分析..."):
        try:
            time.sleep(1.2) # 抗壓保護
            full_addr = f"{sel_city}{sel_dist}{road_name}{road_type}{addr_sec}段{addr_lane}巷{addr_num}號{c_floor}"
            
            # 專業經紀人 Prompt：切換到開發與收泡維度
            prompt = f"""
            你現在是「樂福團隊」的資深店長。請針對經紀人 {c_agent} 提供的物件進行專業戰術分析：
            地址：{full_addr} ({c_name})
            規格：屋齡{c_age}年/地坪{c_land}/建坪{c_build}/室內{c_inner}坪/開價{c_price}萬。
            
            請從專業房仲經營維度提供以下實戰建議：
            1.【開發端與議價建議】：目前此規格與開價，如何與屋主進行「收泡」議價或開發委託？
            2.【銷售亮點包裝】：針對此物件規格，經紀人在派報或網路廣告上應如何包裝亮點吸引買方？哪些缺陷需預備話術？
            3.【精準客戶配對】：建議經紀人針對哪類型的客戶進行開發（首購、收租、換屋）？
            
            回應風格：專業、強幹、具備指導感。
            """
            
            res = model.generate_content(prompt).text
            st.subheader(f"📊 {full_addr} 專業偵察報告")
            st.markdown(res)
            
            st.divider()
            
            # 搜尋連結優化
            q_photo = urllib.parse.quote(f"{sel_city}{sel_dist}{road_name} {c_inner}坪")
            st.subheader("🌐 專業偵察工具 (搜尋同門牌活案)")
            r1, r2, r3 = st.columns(3)
            with r1: st.link_button("🏠 5168 搜尋活案照片", f"https://house.5168.com.tw/list?keywords={q_photo}")
            with r2: st.link_button("🏗️ 591 查競爭個案", f"https://newhouse.591.com.tw/list?keywords={q_photo}")
            with r3: st.link_button("📈 樂居查成交行情", f"https://www.leju.com.tw/search/search_result?type=1&q={urllib.parse.quote(road_name)}")
                
        except Exception as e:
            st.error(f"分析失敗，請確認 API 金鑰是否有效。原因：{e}")
