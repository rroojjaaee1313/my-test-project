import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os, io, time

# --- 1. 全台行政區資料庫 ---
TAIWAN_DISTRICTS = {
    "台中市": ["大里區", "北屯區", "西屯區", "南屯區", "太平區", "霧峰區", "烏日區", "豐原區", "中區", "東區", "南區", "西區", "北區", "潭子區", "大雅區", "神岡區", "沙鹿區", "龍井區", "梧棲區", "清水區", "大甲區", "外埔區", "大安區", "后里區", "石岡區", "東勢區", "和平區", "新社區", "大肚區"],
    "台北市": ["中正區", "萬華區", "大同區", "中山區", "松山區", "大安區", "信義區", "內湖區", "南港區", "士林區", "北投區", "文山區"],
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區", "汐止區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區"],
    "桃園市": ["桃園區", "中壢區", "大溪區", "楊梅區", "蘆竹區", "大園區", "龜山區", "八德區", "龍潭區", "平鎮區", "新屋區", "觀音區"],
    "台南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "玉井區", "麻豆區", "佳里區", "新營區", "善化區"],
    "高雄市": ["新興區", "前金區", "苓雅區", "鹽埕區", "鼓山區", "前鎮區", "三民區", "楠梓區", "小港區", "左營區", "鳳山區", "大寮區", "岡山區"],
    "其他縣市": ["基隆市", "新竹市", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", "台東縣", "澎湖縣", "金門縣", "連江縣"]
}

# --- 2. 系統初始化 (修正 404) ---
st.set_page_config(page_title="樂福情報站", layout="wide", page_icon="🦅")

@st.cache_resource
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets: return None
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    try:
        # 強制使用正確路徑
        return genai.GenerativeModel(model_name='models/gemini-1.5-flash')
    except:
        return None

model = init_gemini()

# --- 3. 介面佈局 ---
st.title("🦅 樂福團隊：精準偵察系統")

col_in, col_res = st.columns([1, 1.2])

with col_in:
    with st.form("pro_form_final_v6"):
        st.subheader("📍 物件位置")
        # 第一列：縣市/區域
        c1_addr, c2_addr = st.columns(2)
        with c1_addr:
            city = st.selectbox("縣市", options=list(TAIWAN_DISTRICTS.keys()), index=0)
        with c2_addr:
            district = st.selectbox("區域", options=TAIWAN_DISTRICTS[city])
        
        # 第二列：路/街名 + 類型
        c3_addr, c4_addr = st.columns([3, 1])
        with c3_addr:
            road_name = st.text_input("路街名稱", placeholder="例如：東榮")
        with c4_addr:
            road_type = st.selectbox("類型", ["路", "街", "大道"])

        # 第三列：段/巷/弄/號
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
        st.subheader("📏 實戰規格 (請輸入數字)")
        c1, c2 = st.columns(2)
        with c1:
            # 所有的預設值都設為 0.0 或 0，清空原本的範例數字
            c_land = st.number_input("地坪", value=0.0, step=0.1)
            c_build_total = st.number_input("總建坪", value=0.0, step=0.1)
            c_age = st.number_input("屋齡 (年)", value=0)
        with c2:
            c_build_inner = st.number_input("室內坪數 (主+附)", value=0.0, step=0.1)
            c_width = st.number_input("面寬 (米)", value=0.0, step=0.1)
            c_elevator = st.selectbox("電梯", ["有", "無"])
            
        c_price = st.number_input("開價 (萬)", value=0, step=50)
        c_agent = st.text_input("承辦人")
        submitted = st.form_submit_button("🚀 啟動精準分析")

# --- 4. 分析邏輯 ---
if submitted and model:
    with col_res:
        with st.spinner("🕵️ 樂福導師正在計算中..."):
            try:
                time.sleep(1.2) # 抗壓緩衝
                
                # 組合完整地址
                full_addr = f"{city}{district}{road_name}{road_type}"
                if addr_section: full_addr += f"{addr_section}段"
                if addr_lane: full_addr += f"{addr_lane}巷"
                if addr_alley: full_addr += f"{addr_alley}弄"
                full_addr += f"{addr_num}號"
                
                inner_pct = round((c_build_inner / c_build_total) * 100, 1) if c_build_total > 0 else 0
                unit_p = round(c_price / c_build_total, 2) if c_build_total > 0 else 0
                
                prompt = f"""
                你是樂福導師，精簡回覆：
                物件：{full_addr} {c_name} (屋齡{c_age}/地{c_land}/總建{c_build_total}/室內坪數{c_build_inner}/{c_elevator}/面寬{c_width}m)
                價格：{c_price}萬 (單價{unit_p}萬)
                
                1.【行情】比對同區相似活案。
                2.【評估】室內占比{inner_pct}%之優勢。
                3.【戰術】指導{c_agent}談價。
                * 禁止假網址。
                """
                
                res = model.generate_content(prompt).text
                st.subheader(f"📊 {c_name if c_name else road_name} 報告")
                st.markdown(res)
                
                # 語音
                tts = gTTS(f"報告已完成。", lang='zh-tw')
                fp = io.BytesIO(); tts.write_to_fp(fp)
                st.audio(fp, format='audio/mp3')
                
                st.divider()
                st.subheader("🌐 即時官網搜尋")
                search_q = f"{full_addr}+{c_build_inner}坪"
                st.link_button("🏠 5168 官網搜尋照片", f"https://house.5168.com.tw/list?keywords={search_q}")
                
            except Exception as e:
                st.error(f"分析失敗: {e}")
