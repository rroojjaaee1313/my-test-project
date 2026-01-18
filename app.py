import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os, io, time

# --- 1. 全台行政區資料庫 (確保各縣市區域獨立) ---
TAIWAN_DATA = {
    "台中市": ["大里區", "北屯區", "西屯區", "南屯區", "太平區", "霧峰區", "烏日區", "豐原區", "中區", "東區", "南區", "西區", "北區", "潭子區", "大雅區", "神岡區", "沙鹿區", "龍井區", "梧棲區", "清水區", "大甲區", "外埔區", "大安區", "后里區", "石岡區", "東勢區", "和平區", "新社區", "大肚區"],
    "台北市": ["中正區", "萬華區", "大同區", "中山區", "松山區", "大安區", "信義區", "內湖區", "南港區", "士林區", "北投區", "文山區"],
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區", "汐止區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區"],
    "桃園市": ["桃園區", "中壢區", "大溪區", "楊梅區", "蘆竹區", "大園區", "龜山區", "八德區", "龍潭區", "平鎮區", "新屋區", "觀音區"],
    "新竹市": ["東區", "北區", "香山區"],
    "新竹縣": ["竹北市", "竹東鎮", "新埔鎮", "關西鎮", "湖口鄉", "新豐鄉", "芎林鄉", "橫山鄉", "北埔鄉", "寶山鄉"],
    "苗栗縣": ["苗栗市", "頭份市", "竹南鎮", "後龍鎮", "通霄鎮", "苑裡鎮"],
    "彰化縣": ["彰化市", "鹿港鎮", "和美鎮", "員林市", "溪湖鎮", "田中鎮", "二林鎮"],
    "南投縣": ["南投市", "埔里鎮", "草屯鎮", "竹山鎮", "集集鎮"],
    "雲林縣": ["斗六市", "斗南鎮", "虎尾鎮", "西螺鎮", "北港鎮"],
    "嘉義市": ["東區", "西區"],
    "嘉義縣": ["太保市", "朴子市", "民雄鄉", "水上鄉", "中埔鄉"],
    "台南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "善化區", "新市區"],
    "高雄市": ["新興區", "苓雅區", "鼓山區", "左營區", "楠梓區", "三民區", "鳳山區", "小港區"],
    "屏東縣": ["屏東市", "潮州鎮", "東港鎮", "恆春鎮"],
    "宜蘭縣": ["宜蘭市", "羅東鎮", "蘇澳鎮", "礁溪鄉"],
    "花蓮縣": ["花蓮市", "吉安鄉", "玉里鎮"],
    "台東縣": ["台東市", "卑南鄉"],
    "基隆市": ["仁愛區", "信義區", "中正區"],
    "澎湖縣": ["馬公市"],
    "金門縣": ["金城鎮"],
    "連江縣": ["南竿鄉"]
}

# --- 2. 系統初始化 ---
st.set_page_config(page_title="樂福情報站", layout="wide", page_icon="🦅")

@st.cache_resource
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets: return None
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel(model_name='models/gemini-1.5-flash')

model = init_gemini()

# --- 3. 介面佈局 ---
st.title("🦅 樂福團隊：全網實戰偵察系統")

col_in, col_res = st.columns([1, 1.2])

with col_in:
    # 這裡不使用 st.form 包裹地址選單，因為連動選單需要即時觸發重新渲染
    st.subheader("📍 物件位置")
    c1_addr, c2_addr = st.columns(2)
    with c1_addr:
        selected_city = st.selectbox("縣市", options=list(TAIWAN_DATA.keys()), index=0)
    with c2_addr:
        # 重要：這裡的 options 會根據 selected_city 即時變動
        selected_district = st.selectbox("區域", options=TAIWAN_DATA[selected_city])
    
    # 其他內容放入 Form 提交
    with st.form("pro_form_final_v10"):
        c3_addr, c4_addr = st.columns([3, 1])
        with c3_addr:
            road_name = st.text_input("路街名稱", placeholder="例如：東榮")
        with c4_addr:
            road_type = st.selectbox("類型", ["路", "街", "大道", "巷"])

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            addr_section = st.text_input("段", placeholder="無")
        with c6:
            addr_lane = st.text_input("巷", placeholder="無")
        with c7:
            addr_alley = st.text_input("弄", placeholder="無")
        with c8:
            addr_num = st.text_input("號", placeholder="必填")

        c_name = st.text_input("案名/社區 (選填)", placeholder="例如：大附中別墅")
        
        st.divider()
        st.subheader("📏 實戰規格 (欄位已清空)")
        c1, c2 = st.columns(2)
        with c1:
            c_land = st.text_input("地坪", placeholder="請輸入數字")
            c_build_total = st.text_input("總建坪", placeholder="請輸入數字")
            c_age = st.text_input("屋齡 (年)", placeholder="請輸入數字")
            c_floor = st.text_input("樓層", placeholder="例如：8/15")
        with c2:
            c_build_inner = st.text_input("室內坪數 (主+附)", placeholder="請輸入數字")
            c_width = st.text_input("面寬 (米)", placeholder="請輸入數字")
            c_elevator = st.selectbox("電梯", ["有", "無"])
            c_road = st.text_input("路寬 (米)", placeholder="請輸入數字")
            
        c_price = st.text_input("開價 (萬)", placeholder="請輸入數字")
        c_agent = st.text_input("承辦人", placeholder="您的姓名")
        submitted = st.form_submit_button("🚀 啟動全網掃描偵察")

# --- 4. 分析邏輯 ---
if submitted and model:
    with col_res:
        with st.spinner("🕵️ 樂福導師正在跨平台比對中..."):
            try:
                time.sleep(1)
                full_addr = f"{selected_city}{selected_district}{road_name}{road_type}"
                if addr_section: full_addr += f"{addr_section}段"
                if addr_lane: full_addr += f"{addr_lane}巷"
                if addr_alley: full_addr += f"{addr_alley}弄"
                full_addr += f"{addr_num}號"
                
                # 數值轉換保護
                def to_f(val): return float(val) if val and val.replace('.','',1).isdigit() else 0
                
                p_land = to_f(c_land)
                p_build = to_f(c_build_total)
                p_inner = to_f(c_build_inner)
                p_price = to_f(c_price)
                unit_p = round(p_price / p_build, 2) if p_build > 0 else 0
                inner_pct = round((p_inner / p_build) * 100, 1) if p_build > 0 else 0
                
                prompt = f"""
                你是樂福導師，請執行分析：
                物件：{full_addr} {c_name}
                規格：樓層{c_floor}/屋齡{c_age}/地{p_land}/總建{p_build}/室內坪數(主+附){p_inner}/{c_elevator}/面寬{c_width}m
                價格：{p_price}萬 (單價{unit_p}萬)
                
                1.【行情】比對該區相似活案。
                2.【評估】室內占比{inner_pct}%與條件優劣。
                3.【戰術】指導{c_agent}開發議價重點。
                * 禁止生成假網址。
                """
                
                res = model.generate_content(prompt).text
                st.subheader(f"📊 {c_name if c_name else road_name} 報告")
                st.markdown(res)
                
                st.divider()
                st.subheader("🌐 全網即時監測")
                search_q = f"{full_addr}+{p_inner}坪"
                r1, r2, r3 = st.columns(3)
                with r1:
                    st.link_button("🏠 5168 全網搜尋", f"https://house.5168.com.tw/list?keywords={search_q}")
                with r2:
                    st.link_button("🏢 永慶房仲網", f"https://buy.yungching.com.tw/list?q={search_q}")
                with r3:
                    st.link_button("📈 樂居實價登錄", f"https://www.leju.com.tw/search/search_result?type=1&q={full_addr}")
                
            except Exception as e:
                st.error(f"分析失敗: {e}")
