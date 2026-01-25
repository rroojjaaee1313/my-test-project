import streamlit as st
import google.generativeai as genai
import urllib.parse
import json
import datetime
import pandas as pd
# 新增：Google Sheets 連線套件
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False

# --- 0. 系統基本設定 ---
TEAM_MEMBERS = ["店長", "林小明", "陳大華", "張美美", "王大砲", "新進同仁"]
ADMIN_PASSWORD = "Love168"

# --- 1. 資料庫 (完整行政區) ---
POSTAL_DATA = {
    "臺中市": {"中區": "400", "東區": "401", "南區": "402", "西區": "403", "北區": "404", "北屯區": "406", "西屯區": "407", "南屯區": "408", "太平區": "411", "大里區": "412", "霧峰區": "413", "烏日區": "414", "豐原區": "420", "后里區": "421", "石岡區": "422", "東勢區": "423", "新社區": "424", "潭子區": "427", "大雅區": "428", "神岡區": "429", "大肚區": "432", "沙鹿區": "433", "龍井區": "434", "梧棲區": "435", "清水區": "436", "大甲區": "437", "外埔區": "438", "大安區": "439", "和平區": "426"},
    "臺北市": {"中正區": "100", "大同區": "103", "中山區": "104", "松山區": "105", "大安區": "106", "萬華區": "108", "信義區": "110", "士林區": "111", "北投區": "112", "內湖區": "114", "南港區": "115", "文山區": "116"},
    "新北市": {"板橋區": "220", "三重區": "241", "中和區": "235", "永和區": "234", "新莊區": "242", "新店區": "231", "樹林區": "238", "鶯歌區": "239", "三峽區": "237", "淡水區": "251", "汐止區": "221", "土城區": "236", "蘆洲區": "247", "五股區": "248", "泰山區": "243", "林口區": "244", "深坑區": "222", "石碇區": "223", "坪林區": "224", "三芝區": "252", "石門區": "253", "八里區": "249", "平溪區": "226", "雙溪區": "227", "貢寮區": "228", "金山區": "208", "萬里區": "207", "烏來區": "233"},
    "桃園市": {"桃園區": "330", "中壢區": "320", "大溪區": "335", "楊梅區": "326", "蘆竹區": "338", "大園區": "337", "龜山區": "333", "八德區": "334", "龍潭區": "325", "平鎮區": "324", "新屋區": "327", "觀音區": "328", "復興區": "336"},
    "臺南市": {"中西區": "700", "東區": "701", "南區": "702", "北區": "704", "安平區": "708", "安南區": "709", "永康區": "710", "歸仁區": "711", "新化區": "712", "左鎮區": "713", "玉井區": "714", "楠西區": "715", "南化區": "716", "仁德區": "717", "關廟區": "718", "龍崎區": "719", "官田區": "720", "麻豆區": "721", "佳里區": "722", "西港區": "723", "七股區": "724", "將軍區": "725", "學甲區": "726", "北門區": "727", "新營區": "730", "後壁區": "731", "白河區": "732", "東山區": "733", "六甲區": "734", "下營區": "735", "柳營區": "736", "鹽水區": "737", "善化區": "741", "大內區": "742", "山上區": "743", "新市區": "744", "安定區": "745"},
    "高雄市": {"新興區": "800", "前金區": "801", "苓雅區": "802", "鹽埕區": "803", "鼓山區": "804", "旗津區": "805", "前鎮區": "806", "三民區": "807", "楠梓區": "808", "小港區": "812", "左營區": "813", "仁武區": "814", "大社區": "815", "岡山區": "820", "路竹區": "821", "阿蓮區": "822", "田寮區": "823", "燕巢區": "824", "橋頭區": "825", "梓官區": "826", "彌陀區": "827", "永安區": "828", "湖內區": "829", "鳳山區": "830", "大寮區": "831", "林園區": "832", "鳥松區": "833", "大樹區": "834", "旗山區": "840", "美濃區": "842", "六龜區": "844", "內門區": "845", "杉林區": "846", "甲仙區": "847", "桃源區": "848", "那瑪夏區": "849", "茂林區": "851", "茄萣區": "852"},
    "基隆市": {"仁愛區": "200", "信義區": "201", "中正區": "202", "中山區": "203", "安樂區": "204", "暖暖區": "205", "七堵區": "206"},
    "新竹市": {"東區": "300", "北區": "300", "香山區": "300"},
    "新竹縣": {"竹北市": "302", "竹東鎮": "310", "新埔鎮": "305", "關西鎮": "306", "湖口鄉": "303", "新豐鄉": "304", "芎林鄉": "307", "橫山鄉": "312", "北埔鄉": "314", "寶山鄉": "308", "峨眉鄉": "315", "尖石鄉": "313", "五峰鄉": "311"},
    "苗栗縣": {"苗栗市": "360", "頭份市": "351", "竹南鎮": "350", "後龍鎮": "356", "通霄鎮": "357", "苑裡鎮": "358", "卓蘭鎮": "369", "造橋鄉": "361", "西湖鄉": "368", "頭屋鄉": "362", "公館鄉": "363", "銅鑼鄉": "366", "三義鄉": "367", "大湖鄉": "364", "獅潭鄉": "354", "三灣鄉": "352", "南庄鄉": "353", "泰安鄉": "365"},
    "彰化縣": {"彰化市": "500", "員林市": "510", "鹿港鎮": "505", "和美鎮": "508", "北斗鎮": "521", "溪湖鎮": "514", "田中鎮": "520", "二林鎮": "526", "線西鄉": "507", "伸港鄉": "509", "福興鄉": "506", "秀水鄉": "504", "花壇鄉": "503", "芬園鄉": "502", "大村鄉": "515", "埔鹽鄉": "516", "埔心鄉": "513", "永靖鄉": "512", "社頭鄉": "511", "二水鄉": "530", "田尾鄉": "522", "埤頭鄉": "523", "芳苑鄉": "528", "大城鄉": "527", "竹塘鄉": "525", "溪州鄉": "524"},
    "南投縣": {"南投市": "540", "埔里鎮": "545", "草屯鎮": "542", "竹山鎮": "557", "集集鎮": "552", "名間鄉": "551", "鹿谷鄉": "558", "中寮鄉": "541", "魚池鄉": "555", "國姓鄉": "544", "水里鄉": "553", "信義鄉": "556", "仁愛鄉": "546"},
    "雲林縣": {"斗六市": "640", "斗南鎮": "630", "虎尾鎮": "632", "西螺鎮": "648", "土庫鎮": "633", "北港鎮": "651", "古坑鄉": "646", "大埤鄉": "631", "莿桐鄉": "647", "林內鄉": "643", "二崙鄉": "649", "崙背鄉": "637", "麥寮鄉": "638", "東勢鄉": "635", "褒忠鄉": "634", "台西鄉": "636", "元長鄉": "655", "四湖鄉": "654", "口湖鄉": "653", "水林鄉": "652"},
    "嘉義市": {"東區": "600", "西區": "600"},
    "嘉義縣": {"太保市": "612", "朴子市": "613", "布袋鎮": "625", "大林鎮": "622", "民雄鄉": "621", "溪口鄉": "623", "新港鄉": "616", "六腳鄉": "615", "東石鄉": "614", "義竹鄉": "624", "鹿草鄉": "611", "水上鄉": "608", "中埔鄉": "606", "竹崎鄉": "604", "梅山鄉": "603", "番路鄉": "602", "大埔鄉": "607", "阿里山鄉": "605"},
    "屏東縣": {"屏東市": "900", "潮州鎮": "920", "東港鎮": "928", "恆春鎮": "946", "萬丹鄉": "913", "長治鄉": "908", "麟洛鄉": "909", "九如鄉": "904", "里港鄉": "905", "高樹鄉": "906", "鹽埔鄉": "907", "內埔鄉": "912", "竹田鄉": "911", "萬巒鄉": "923", "枋寮鄉": "940", "新埤鄉": "925", "枋山鄉": "941", "車城鄉": "944", "滿州鄉": "947", "三地門鄉": "901", "霧臺鄉": "902", "瑪家鄉": "903", "泰武鄉": "921", "來義鄉": "922", "春日鄉": "942", "獅子鄉": "943", "牡丹鄉": "945", "琉球鄉": "929", "崁頂鄉": "924", "南州鄉": "926", "佳冬鄉": "927"},
    "宜蘭縣": {"宜蘭市": "260", "羅東鎮": "265", "蘇澳鎮": "270", "頭城鎮": "261", "礁溪鄉": "262", "壯圍鄉": "263", "員山鄉": "264", "冬山鄉": "269", "五結鄉": "268", "三星鄉": "266", "大同鄉": "267", "南澳鄉": "272"},
    "花蓮縣": {"花蓮市": "970", "鳳林鎮": "975", "玉里鎮": "981", "新城鄉": "971", "吉安鄉": "973", "壽豐鄉": "974", "光復鄉": "976", "豐濱鄉": "977", "瑞穗鄉": "978", "富里鄉": "983", "秀林鄉": "972", "萬榮鄉": "979", "卓溪鄉": "982"},
    "台東縣": {"台東市": "950", "成功鎮": "961", "關山鎮": "962", "卑南鄉": "954", "鹿野鄉": "955", "池上鄉": "956", "東河鄉": "959", "長濱鄉": "962", "太麻里鄉": "963", "大武鄉": "965", "綠島鄉": "951", "海端鄉": "957", "延平鄉": "953", "金峰鄉": "964", "達仁鄉": "966", "蘭嶼鄉": "952"},
    "澎湖縣": {"馬公市": "880", "湖西鄉": "885", "白沙鄉": "884", "西嶼鄉": "881", "望安鄉": "882", "七美鄉": "883"},
    "金門縣": {"金城鎮": "893", "金湖鎮": "891", "金沙鎮": "890", "金寧鄉": "892", "烈嶼鄉": "894", "烏坵鄉": "896"},
    "連江縣": {"南竿鄉": "209", "北竿鄉": "210", "莒光鄉": "211", "東引鄉": "212"}
}

# --- 2. 系統初始化 ---
st.set_page_config(page_title="樂福集團 HOUSE MANAGER", layout="wide", page_icon="🦅")

# 初始化 State
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = ""
if 'usage_logs' not in st.session_state: st.session_state.usage_logs = []
if 'addr_data' not in st.session_state: st.session_state.addr_data = {"city": "", "dist": "", "road": "", "sec": "", "lane": "", "alley": "", "no": "", "floor": ""}
if 'history' not in st.session_state: st.session_state.history = []
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'current_report' not in st.session_state: st.session_state.current_report = ""

# CSS
st.markdown("""
    <style>
    .stTextInput>div>div>input, .stSelectbox>div>div>div { background-color: transparent; border: none; border-bottom: 2px solid #1e3a8a; border-radius: 0px; padding: 5px 0px; }
    .section-title { color: #334155; border-left: 5px solid #1e3a8a; padding-left: 15px; margin-top: 20px; font-weight: bold; font-size: 1.25rem; }
    .action-btn { display: inline-block; width: 100%; text-align: center; padding: 10px; margin: 5px 0; border-radius: 8px; text-decoration: none; color: white; font-weight: bold; }
    .btn-street { background-color: #FFC107; color: black; }
    .key-factor-box { background-color: #fff7ed; padding: 15px; border-radius: 10px; border: 1px solid #fdba74; margin-bottom: 15px; }
    .login-container { max-width: 400px; margin: 50px auto; padding: 40px; border: 1px solid #e0e0e0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center;}
    .alert-box { background-color: #fecaca; padding: 10px; border-radius: 5px; color: #7f1d1d; border: 1px solid #f87171; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Google Sheets 連結設定 (未設定前會使用本地暫存) ---
@st.cache_resource
def get_google_sheet_client():
    if not GSHEETS_AVAILABLE: return None
    try:
        # 請在 Streamlit Secrets 中設定 gcp_service_account
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"],
            ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        )
        client = gspread.authorize(creds)
        return client
    except Exception:
        return None

# 讀取歷史回報
def check_property_history(addr_str):
    client = get_google_sheet_client()
    if not client: return None
    try:
        sheet = client.open("LoveGroup_KB").sheet1
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        # 簡單模糊比對
        match = df[df['Address'].str.contains(addr_str, na=False)]
        if not match.empty:
            return match.to_dict('records')
        return None
    except:
        return None

# 寫入回報
def save_property_report(data_dict):
    client = get_google_sheet_client()
    if not client: return # 如果沒設定就只存本地
    try:
        sheet = client.open("LoveGroup_KB").sheet1
        sheet.append_row(list(data_dict.values()))
    except:
        pass

# AI 模型
@st.cache_resource
def get_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = 'models/gemini-1.5-flash'
        if target not in models: target = 'models/gemini-pro'
        if target not in models and models: target = models[0]
        return genai.GenerativeModel(model_name=target)
    except: return None

model = get_model()

# --- 4. 側邊欄與登入 ---
with st.sidebar:
    st.title("🦅 戰情選單")
    if st.session_state.logged_in:
        st.write(f"👤 經紀人：**{st.session_state.current_user}**")
        nav = st.radio("功能切換", ["🎯 戰報生成器", "📊 管理儀表板"])
        if st.button("登出切換"):
            st.session_state.logged_in = False
            st.rerun()
        if nav == "📊 管理儀表板":
            st.markdown("---")
            if st.text_input("輸入管理密碼", type="password") != ADMIN_PASSWORD:
                st.error("🔒 權限不足"); st.stop()
        st.markdown("---")
        if st.session_state.history:
            st.caption("📜 歷史紀錄")
            for i, r in enumerate(reversed(st.session_state.history)):
                if st.button(f"{r['time']} - {r['addr'][:5]}", key=f"h_{i}"):
                    st.session_state.current_report = r['report']
                    st.session_state.chat_history = [] 
    else: nav = "LOGIN"

if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("## 🦅 樂福 AI 戰情室")
        st.caption("請打卡登入以使用系統")
        with st.form("login_form"):
            user = st.selectbox("請選擇您的姓名", TEAM_MEMBERS)
            if st.form_submit_button("🚀 上班打卡", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.current_user = user
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 5. 主程式 ---
if nav == "🎯 戰報生成器":
    st.title("🦅 HOUSE MANAGER AI")
    battle_type = st.radio("⚔️ 任務模式", ["🛡️ 開發/議價 (對屋主)", "🏹 銷售/包裝 (對買方)"], horizontal=True)

    # 解析
    st.markdown('<div style="background:#f0f9ff; padding:15px; border-radius:10px; margin-bottom:15px;">', unsafe_allow_html=True)
    raw_addr = st.text_input("⚡ 智能地址快搜 (整串貼上)")
    if st.button("🔍 AI 解析"):
        if model and raw_addr:
            try:
                resp = model.generate_content(f"將此地址拆解為JSON (city, dist, road, sec, lane, alley, no, floor): {raw_addr}。只回傳JSON。")
                st.session_state.addr_data.update(json.loads(resp.text.replace('```json','').replace('```','')))
                st.success("✅ 解析成功")
            except: st.error("解析失敗")
    st.markdown('</div>', unsafe_allow_html=True)

    # 地圖
    st.markdown('<div class="section-title">📍 物件位置</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1: 
        curr_city = st.session_state.addr_data.get('city', '')
        sel_city = st.selectbox("城市", list(POSTAL_DATA.keys()), index=list(POSTAL_DATA.keys()).index(curr_city) if curr_city in POSTAL_DATA else 0)
    with c2: 
        curr_dist = st.session_state.addr_data.get('dist', '')
        opts = list(POSTAL_DATA[sel_city].keys())
        sel_dist = st.selectbox("區域", opts, index=opts.index(curr_dist) if curr_dist in opts else 0)
    with c3: road = st.text_input("路街", value=st.session_state.addr_data.get('road', ''))
    
    r1, r2, r3, r4 = st.columns(4)
    with r1: sec = st.text_input("段", value=st.session_state.addr_data.get('sec', ''))
    with r2: lane = st.text_input("巷", value=st.session_state.addr_data.get('lane', ''))
    with r3: alley = st.text_input("弄", value=st.session_state.addr_data.get('alley', ''))
    with r4: no = st.text_input("號", value=st.session_state.addr_data.get('no', ''))
    full_addr = f"{sel_city}{sel_dist}{road}{sec+'段' if sec else ''}{lane+'巷' if lane else ''}{alley+'弄' if alley else ''}{no+'號' if no else ''}"
    
    if road:
        st.markdown(f'<a href="https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(full_addr)}" target="_blank" class="action-btn btn-street">👀 720° 街景 (Street View)</a>', unsafe_allow_html=True)

        # 【知識庫讀取】 - 檢查歷史紀錄
        history_records = check_property_history(full_addr)
        if history_records:
            st.markdown(f'<div class="alert-box">⚠️ 發現此物件有 {len(history_records)} 筆歷史回報！AI 已自動載入參考。</div>', unsafe_allow_html=True)
            with st.expander("查看歷史回報細節"):
                st.table(history_records)

    # 表單
    with st.form("battle_form"):
        st.markdown(f'<div class="section-title">📉 {battle_type} 核心參數</div>', unsafe_allow_html=True)
        st.text_input("👤 經紀人", value=st.session_state.current_user, disabled=True)
        c_price = st.text_input("💰 開價 (萬)")
        c_name = st.text_input("🏢 社區 (選填)")

        st.markdown('<div class="key-factor-box">', unsafe_allow_html=True)
        st.markdown("#### 🔑 關鍵成交因子 (AI 讀心術)")
        
        prompt_inject = ""
        kb_data = {} # 準備存入知識庫的資料

        if "開發" in battle_type:
            col1, col2 = st.columns(2)
            with col1: expect_price = st.text_input("屋主底價 (萬)")
            with col2: last_offer = st.text_input("最高出價紀錄 (萬)")
            f1, f2 = st.columns(2)
            with f1: sell_reason = st.selectbox("🔥 售屋動機", ["資金周轉/欠債 (極急)", "分家產/離婚 (急)", "換屋/移民 (中)", "資產配置 (不急)", "閒置資產 (不急)"])
            with f2: owner_style = st.selectbox("🧠 屋主性格", ["講理/數據派", "固執/感覺派", "怕麻煩/授權派", "貪心/比價派"])
            prompt_inject = f"屋主動機：{sell_reason}。性格：{owner_style}。請針對此動機設計『恐懼行銷』或『願景行銷』話術。"
            kb_data = {"Type": "開發", "Price": expect_price, "Offer": last_offer, "Note": f"動機:{sell_reason}"}
            
        else:
            col1, col2, col3 = st.columns(3)
            with col1: total_ping = st.text_input("總坪數")
            with col2: internal_val = st.text_input("🔒 內建估值")
            with col3: buyer_type = st.selectbox("買方類型", ["首購族", "換屋族", "投資置產", "退休養老", "為子女置產"])
            f1, f2 = st.columns(2)
            with f1: trigger_point = st.selectbox("❤️ 成交觸發點", ["學區/教育", "交通便利/捷運", "離娘家/親友近", "生活機能", "價格/增值"])
            with f2: concern_point = st.multiselect("🚧 核心抗性", ["價格太貴", "屋況/需整理", "地點/嫌遠", "格局/風水", "貸款/自備款"])
            prompt_inject = f"買方是{buyer_type}。觸發點：{trigger_point}。抗性：{', '.join(concern_point)}。請將優點連結到觸發點，並用『重新定義』化解抗性。"
            kb_data = {"Type": "銷售", "Price": c_price, "Valuation": internal_val, "Note": f"買方:{buyer_type}, 抗性:{concern_point}"}
        
        st.markdown('</div>', unsafe_allow_html=True)

        if st.form_submit_button("🔥 啟動 AI 戰略分析"):
            if model:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                # 1. 存入 Session Log
                st.session_state.usage_logs.append({"時間": now, "經紀人": st.session_state.current_user, "角色": battle_type, "地址": full_addr, "金額": c_price})
                
                # 2. 存入 Knowledge Base (如果已連線)
                kb_full_data = {"Date": now, "Agent": st.session_state.current_user, "Address": full_addr, **kb_data}
                save_property_report(kb_full_data)

                # 3. AI 生成
                with st.spinner("教練正在分析..."):
                    try:
                        # 將歷史紀錄注入 Prompt
                        history_context = ""
                        if history_records:
                            history_context = f"\n【⚠️ 重要情報：本物件有歷史回報紀錄】\n{history_records}\n請參考這些過去的情報，判斷屋主心態是否軟化，或市場是否有變化。\n"

                        prompt = f"""
                        你是樂福集團金牌教練。身分：{battle_type} 顧問。
                        地址：{full_addr} ({c_name})。開價：{c_price}萬。
                        {history_context}
                        【關鍵人性分析】：{prompt_inject}
                        任務：
                        1. 【環境掃描】：列出學區、市場、公園。
                        2. 【人性戰略】：針對動機/抗性深度剖析。
                        3. 【必殺話術】：提供直接對話稿。
                        """
                        resp = model.generate_content(prompt)
                        st.session_state.current_report = resp.text
                        st.session_state.history.append({"time": now, "addr": full_addr, "report": resp.text})
                        st.session_state.chat_history = []
                    except Exception as e: st.error(f"錯誤：{e}")

    if st.session_state.current_report:
        st.markdown("---")
        st.subheader(f"📋 戰略報告")
        st.markdown(st.session_state.current_report)
        st.markdown("---")
        st.subheader("💬 戰情室對話")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        if u_in := st.chat_input("追問..."):
            with st.chat_message("user"): st.markdown(u_in)
            st.session_state.chat_history.append({"role": "user", "content": u_in})
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    resp = model.generate_content(f"背景：{st.session_state.current_report}\n追問：{u_in}")
                    st.markdown(resp.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": resp.text})

# --- 6. 儀表板 ---
elif nav == "📊 管理儀表板":
    st.title("🔒 管理儀表板")
    if st.session_state.usage_logs:
        df = pd.DataFrame(st.session_state.usage_logs)
        c1, c2, c3 = st.columns(3)
        c1.metric("總次數", len(df))
        c2.metric("活躍人數", len(df["經紀人"].unique()))
        try: c3.metric("熱區", df["地址"].str[:6].mode()[0])
        except: c3.metric("熱區", "-")
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df["經紀人"].value_counts())
    else: st.info("無資料")
