import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os, io, time

# --- 1. 全台行政區資料庫 (精簡版) ---
TAIWAN_DISTRICTS = {
    "台中市": ["大里區", "北屯區", "西屯區", "南屯區", "太平區", "霧峰區", "烏日區", "豐原區", "北區", "南區", "西區", "東區", "中區", "潭子區", "大雅區", "神岡區", "沙鹿區", "龍井區"],
    "台北市": ["中正區", "中山區", "大安區", "信義區", "內湖區", "士林區", "北投區", "文山區"],
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "林口區", "淡水區", "汐止區"],
    "桃園市": ["桃園區", "中壢區", "蘆竹區", "龜山區", "八德區", "平鎮區"],
    "台南市": ["東區", "安平區", "永康區", "歸仁區", "善化區", "新市區"],
    "高雄市": ["苓雅區", "左營區", "三民區", "楠梓區", "鳳山區", "鼓山區"],
    "其他縣市": ["新竹市", "彰化縣", "南投縣", "雲林縣", "嘉義市", "屏東縣", "宜蘭縣"]
}

# --- 2. 系統初始化 (強化抗壓與快取) ---
st.set_page_config(page_title="樂福情報站", layout="wide", page_icon="🦅")

@st.cache_resource
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets: return None
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 固定使用 gemini-1.5-flash
    return genai.GenerativeModel('gemini-1.5-flash')

model = init_gemini()

# --- 3. 介面佈局 ---
st.title("🦅 樂福團隊：精準偵察系統")

col_in, col_res = st.columns([1, 1.2])

with col_in:
    with st.form("pro_form_final"):
        st.subheader("📍 物件位置")
        c1_addr, c2_addr = st.columns(2)
        with c1_addr:
            city = st.selectbox("縣市", options=list(TAIWAN_DISTRICTS.keys()), index=0)
        with c2_addr:
            district = st.selectbox("區域", options=TAIWAN_DISTRICTS[city])
        
        road_name = st.text_input("路段名稱", placeholder="如：東榮路二段")
        c_name = st.text_input("案名/社區", placeholder="大附中別墅")
        
        st.divider()
        st.subheader("📏 實戰規格")
        c1, c2 = st.columns(2)
        with c1:
            c_land = st.number_input("地坪", value=30.0, step=0.1)
            c_build_total = st.number_input("總建坪", value=65.0, step=0.1)
            c_age = st.number_input("屋齡 (年)", value=15)
        with c2:
            # 正名：室內坪數 (主+附)
            c_build_inner = st.number_input("室內坪數 (主+附)", value=55.0, step=0.1)
            c_width = st.number_input("面寬 (米)", value=5.0, step=0.1)
            c_elevator = st.selectbox("電梯", ["有", "無"])
            
        c_price = st.number_input("開價 (萬)", value=2500, step=50)
        c_agent = st.text_input("承辦人")
        submitted = st.form_submit_button("🚀 啟動精準分析")

# --- 4. 分析邏輯 (加入頻率保護) ---
if submitted and model:
    with col_res:
        with st.spinner("🕵️ 樂福導師正在計算..."):
            try:
                # 解決 429 錯誤：主動加入 1 秒延遲緩衝
                time.sleep(1) 
                
                inner_pct = round((c_build_inner / c_build_total) * 100, 1)
                full_loc = f"{city}{district}{road_name}"
                unit_p = round(c_price / c_build_total, 2)
                
                prompt = f"""
                你是樂福導師，精簡回覆：
                物件：{full_loc} {c_name} (屋齡{c_age}/地{c_land}/總建{c_build_total}/室內坪數{c_build_inner}/{c_elevator}/面寬{c_width}m)
                價格：{c_price}萬 (單價{unit_p}萬)
                
                內容：
                1.【行情】對比同區相似活案。
                2.【評估】室內(主+附)占比{inner_pct}%之優勢分析。
                3.【戰術】指導{c_agent}談價與開發重點。
                * 禁止生成帶有 xxxx 的假網址。
                """
                
                res = model.generate_content(prompt).text
                st.subheader(f"📊 {c_name} 報告")
                st.markdown(res)
                
                # 語音
                tts = gTTS(f"分析完成，{c_agent}請查收。", lang='zh-tw')
                fp = io.BytesIO(); tts.write_to_fp(fp)
                st.audio(fp, format='audio/mp3')
                
                # 解決假網址：提供 100% 真實跳轉按鈕
                st.divider()
                st.subheader("🌐 點擊查看真實照片")
                search_q = f"{city}{district}+{road_name}+{c_build_inner}坪"
                st.link_button("🏠 開啟 5168 官網即時搜尋", f"https://house.5168.com.tw/list?keywords={search_q}")
                
            except Exception as e:
                if "429" in str(e):
                    st.error("⚠️ 偵測到點擊過快！免費版 API 有頻率限制，請等 15 秒後再試一次。")
                else:
                    st.error(f"分析失敗: {e}")
