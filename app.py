import streamlit as st
import google.generativeai as genai

# --- 1. 全台完整行政區資料庫 (絕不刪減) ---
TAIWAN_DATA = {
    "台中市": ["中區", "東區", "南區", "西區", "北區", "北屯區", "西屯區", "南屯區", "太平區", "大里區", "霧峰區", "烏日區", "豐原區", "后里區", "石岡區", "東勢區", "新社區", "潭子區", "大雅區", "神岡區", "大肚區", "沙鹿區", "龍井區", "梧棲區", "清水區", "大甲區", "外埔區", "大安區", "和平區"],
    "台北市": ["中正區", "大同區", "中山區", "松山區", "大安區", "萬華區", "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區"],
    "新北市": ["板橋區", "三重區", "中和區", "永和區", "新莊區", "新店區", "樹林區", "鶯歌區", "三峽區", "淡水區", "汐止區", "土城區", "蘆洲區", "五股區", "泰山區", "林口區", "深坑區", "石碇區", "坪林區", "三芝區", "石門區", "八里區", "平溪區", "雙溪區", "貢寮區", "金山區", "萬里區", "烏來區"],
    "桃園市": ["桃園區", "中壢區", "大溪區", "楊梅區", "蘆竹區", "大園區", "龜山區", "八德區", "龍潭區", "平鎮區", "新屋區", "觀音區", "復興區"],
    "台南市": ["中西區", "東區", "南區", "北區", "安平區", "安南區", "永康區", "歸仁區", "新化區", "左鎮區", "玉井區", "楠西區", "南化區", "仁德區", "關廟區", "龍崎區", "官田區", "麻豆區", "佳里區", "西港區", "七股區", "將軍區", "學甲區", "北門區", "新營區", "後壁區", "白河區", "東山區", "六甲區", "下營區", "柳營區", "鹽水區", "善化區", "大內區", "山上區", "新市區", "安定區"],
    "高雄市": ["新興區", "前金區", "苓雅區", "鹽埕區", "鼓山區", "旗津區", "前鎮區", "三民區", "楠梓區", "小港區", "左營區", "仁武區", "大社區", "岡山區", "路竹區", "阿蓮區", "田寮區", "燕巢區", "橋頭區", "梓官區", "彌陀區", "永安區", "湖內區", "鳳山區", "大寮區", "林園區", "鳥松區", "大樹區", "旗山區", "美濃區", "六龜區", "內門區", "杉林區", "甲仙區", "桃源區", "那瑪夏區", "茂林區", "茄萣區"],
    "基隆市": ["仁愛區", "信義區", "中正區", "中山區", "安樂區", "暖暖區", "七堵區"],
    "新竹市": ["東區", "北區", "香山區"],
    "新竹縣": ["竹北市", "竹東鎮", "新埔鎮", "關西鎮", "湖口鄉", "新豐鄉", "芎林鄉", "橫山鄉", "北埔鄉", "寶山鄉", "峨眉鄉", "尖石鄉", "五峰鄉"],
    "苗栗縣": ["苗栗市", "頭份市", "竹南鎮", "後龍鎮", "通霄鎮", "苑裡鎮", "卓蘭鎮", "造橋鄉", "西湖鄉", "頭屋鄉", "公館鄉", "銅鑼鄉", "三義鄉", "大湖鄉", "獅潭鄉", "三灣鄉", "南庄鄉", "泰安鄉"],
    "彰化縣": ["彰化市", "員林市", "鹿港鎮", "和美鎮", "北斗鎮", "溪湖鎮", "田中鎮", "二林鎮", "線西鄉", "伸港鄉", "福興鄉", "秀水鄉", "花壇鄉", "芬園鄉", "大村鄉", "埔鹽鄉", "埔心鄉", "永靖鄉", "社頭鄉", "二水鄉", "田尾鄉", "埤頭鄉", "芳苑鄉", "大城鄉", "竹塘鄉", "溪州鄉"],
    "南投縣": ["南投市", "埔里鎮", "草屯鎮", "竹山鎮", "集集鎮", "名間鄉", "鹿谷鄉", "中寮鄉", "魚池鄉", "國姓鄉", "水里鄉", "信義鄉", "仁愛鄉"],
    "雲林縣": ["斗六市", "斗南鎮", "虎尾鎮", "西螺鎮", "土庫鎮", "北港鎮", "古坑鄉", "大埤鄉", "莿桐鄉", "林內鄉", "二崙鄉", "崙背鄉", "麥寮鄉", "東勢鄉", "褒忠鄉", "台西鄉", "元長鄉", "四湖鄉", "口湖鄉", "水林鄉"],
    "嘉義市": ["東區", "西區"],
    "嘉義縣": ["太保市", "朴子市", "布袋鎮", "大林鎮", "民雄鄉", "溪口鄉", "新港鄉", "六腳鄉", "東石鄉", "義竹鄉", "鹿草鄉", "水上鄉", "中埔鄉", "竹崎鄉", "梅山鄉", "番路鄉", "大埔鄉", "阿里山鄉"],
    "屏東縣": ["屏東市", "潮州鎮", "東港鎮", "恆春鎮", "萬丹鄉", "長治鄉", "麟洛鄉", "九如鄉", "里港鄉", "高樹鄉", "鹽埔鄉", "內埔鄉", "竹田鄉", "萬巒鄉", "枋寮鄉", "新埤鄉", "枋山鄉", "車城鄉", "滿州鄉", "琉球鄉", "三地門鄉", "霧臺鄉", "瑪家鄉", "泰武鄉", "來義鄉", "春日鄉", "獅子鄉", "牡丹鄉"],
    "宜蘭縣": ["宜蘭市", "羅東鎮", "蘇澳鎮", "頭城鎮", "礁溪鄉", "壯圍鄉", "員山鄉", "冬山鄉", "五結鄉", "三星鄉", "大同鄉", "南澳鄉"],
    "花蓮縣": ["花蓮市", "鳳林鎮", "玉里鎮", "新城鄉", "吉安鄉", "壽豐鄉", "光復鄉", "豐濱鄉", "瑞穗鄉", "富里鄉", "秀林鄉", "萬榮鄉", "卓溪鄉"],
    "台東縣": ["台東市", "成功鎮", "關山鎮", "卑南鄉", "鹿野鄉", "池上鄉", "東河鄉", "長濱鄉", "太麻里鄉", "大武鄉", "綠島鄉", "海端鄉", "延平鄉", "金峰鄉", "達仁鄉", "蘭嶼鄉"],
    "澎湖縣": ["馬公市", "湖西鄉", "白沙鄉", "西嶼鄉", "望安鄉", "七美鄉"],
    "金門縣": ["金城鎮", "金湖鎮", "金沙鎮", "金寧鄉", "烈嶼鄉", "烏坵鄉"],
    "連江縣": ["南竿鄉", "北竿鄉", "莒光鄉", "東引鄉"]
}

# --- 2. 核心初始化 (自動修復 404 機制) ---
st.set_page_config(page_title="樂福集團：精準門牌偵察系統", layout="wide", page_icon="🦅")

@st.cache_resource
def get_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ 找不到 API 金鑰。")
        return None
    genai.configure(api_key=api_key)
    try:
        # 動態列舉可用模型，確保不發生 404
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
        return genai.GenerativeModel(model_name=target, system_instruction="你現在是樂福集團金牌教練。")
    except Exception as e:
        st.error(f"連線失敗：{e}")
        return None

model = get_model()

# --- 3. 介面設計 (門牌格式重組) ---
st.title("🦅 樂福集團：金牌偵察作戰系統")
st.markdown("---")

# 1. 地址連動區 (第一行)
st.subheader("📍 1. 精確物件地址")
c1, c2, c3 = st.columns([2, 2, 4])
with c1:
    sel_city = st.selectbox("縣市", options=list(TAIWAN_DATA.keys()), index=3) # 預設台中
with c2:
    sel_dist = st.selectbox("區域", options=TAIWAN_DATA[sel_city])
with c3:
    road_name = st.text_input("路街名", placeholder="例如：崇德路")

# 2. 門牌細項區 (第二行，嚴格排序)
st.markdown("##### 門牌細節說明")
d1, d2, d3, d4, d5, d6 = st.columns([1, 1, 1, 1, 1, 2])
with d1: addr_lane = st.text_input("巷")
with d2: addr_alley = st.text_input("弄")
with d3: addr_sub = st.text_input("衖")
with d4: addr_sec = st.text_input("段")
with d5: addr_num = st.text_input("號")
with d6: addr_floor = st.text_input("樓層 (例如：15樓之1)")

# 3. 其他資訊進入表單
with st.form("love_pro_master_form"):
    c_name = st.text_input("🏠 案名/社區名稱")
    st.divider()

    # 4. 坪數自由輸入區 (純空白框)
    st.subheader("📏 2. 建物坪數拆解 (空白自由輸入)")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        c_main = st.text_input("🏠 主建物坪數")
        c_sub = st.text_input("➕ 附屬建物")
    with p2:
        c_public = st.text_input("🏢 公設坪數")
        c_parking = st.text_input("🚗 車位坪數")
    with p3:
        c_total = st.text_input("📊 權狀總坪數")
        c_land = st.text_input("🌱 持分地坪")
    with p4:
        c_floor_all = st.text_input("🏢 總樓高")
        c_price = st.text_input("💰 總開價")

    st.divider()
    
    # 5. 戰術指標
    f1, f2, f3 = st.columns(3)
    with f1:
        c_age = st.text_input("📅 屋齡")
        c_layout = st.text_input("🛏️ 格局")
    with f2:
        c_face = st.selectbox("朝向", ["座北朝南", "座南朝北", "座東朝西", "座西朝東", "其他"])
        c_status = st.selectbox("屋況", ["全新整理", "現況自住", "需大整理", "毛胚屋"])
    with f3:
        c_road = st.text_input("🛣️ 路寬/面寬")
        c_agent = st.text_input("👤 樂福戰鬥員姓名")

    submitted = st.form_submit_button("🔥 啟動樂福金牌深度分析")

# --- 4. 執行邏輯 ---
if submitted:
    if not model:
        st.error("API 故障中。")
    else:
        # 組合精準門牌地址
        full_addr = f"{sel_city}{sel_dist}{road_name}{addr_lane+'巷' if addr_lane else ''}{addr_alley+'弄' if addr_alley else ''}{addr_sub+'衖' if addr_sub else ''}{addr_sec+'段' if addr_sec else ''}{addr_num+'號' if addr_num else ''}{addr_floor}"
        
        with st.spinner("🎯 教練正在分析門牌價值..."):
            try:
                prompt = f"經紀人：{c_agent} (樂福集團)。地址：{full_addr}。案名：{c_name}。總建：{c_total}。主建物：{c_main}。請以金牌教練身分給予深度戰術。"
                response = model.generate_content(prompt)
                st.markdown(f"### 📋 {c_agent} 專屬報告")
                st.success(f"📍 分析目標：{full_addr}")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"分析失敗：{e}")
