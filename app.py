import streamlit as st
import google.generativeai as genai
import urllib.parse
import json
import datetime

# --- 1. 資料庫 (核心地段資料) ---
POSTAL_DATA = {
    "臺中市": {"中區": "400", "東區": "401", "南區": "402", "西區": "403", "北區": "404", "北屯區": "406", "西屯區": "407", "南屯區": "408", "太平區": "411", "大里區": "412", "霧峰區": "413", "烏日區": "414", "豐原區": "420", "后里區": "421", "石岡區": "422", "東勢區": "423", "新社區": "424", "潭子區": "427", "大雅區": "428", "神岡區": "429", "大肚區": "432", "沙鹿區": "433", "龍井區": "434", "梧棲區": "435", "清水區": "436", "大甲區": "437", "外埔區": "438", "大安區": "439", "和平區": "426"},
    "臺北市": {"中正區": "100", "大同區": "103", "中山區": "104", "松山區": "105", "大安區": "106", "萬華區": "108", "信義區": "110", "士林區": "111", "北投區": "112", "內湖區": "114", "南港區": "115", "文山區": "116"},
    "新北市": {"板橋區": "220", "三重區": "241", "中和區": "235", "永和區": "234", "新莊區": "242", "新店區": "231", "樹林區": "238", "鶯歌區": "239", "三峽區": "237", "淡水區": "251", "汐止區": "221", "土城區": "236", "蘆洲區": "247", "五股區": "248", "泰山區": "243", "林口區": "244", "深坑區": "222", "石碇區": "223", "坪林區": "224", "三芝區": "252", "石門區": "253", "八里區": "249", "平溪區": "226", "雙溪區": "227", "貢寮區": "228", "金山區": "208", "萬里區": "207", "烏來區": "233"},
    "桃園市": {"桃園區": "330", "中壢區": "320", "大溪區": "335", "楊梅區": "326", "蘆竹區": "338", "大園區": "337", "龜山區": "333", "八德區": "334", "龍潭區": "325", "平鎮區": "324", "新屋區": "327", "觀音區": "328", "復興區": "336"},
    "臺南市": {"中西區": "700", "東區": "701", "南區": "702", "北區": "704", "安平區": "708", "安南區": "709", "永康區": "710", "歸仁區": "711", "新化區": "712", "左鎮區": "713", "玉井區": "714", "楠西區": "715", "南化區": "716", "仁德區": "717", "關廟區": "718", "龍崎區": "719", "官田區": "720", "麻豆區": "721", "佳里區": "722", "西港區": "723", "七股區": "724", "將軍區": "725", "學甲區": "726", "北門區": "727", "新營區": "730", "後壁區": "731", "白河區": "732", "東山區": "733", "六甲區": "734", "下營區": "735", "柳營區": "736", "鹽水區": "737", "善化區": "741", "大內區": "742", "山上區": "743", "新市區": "744", "安定區": "745"},
    "高雄市": {"新興區": "800", "前金區": "801", "苓雅區": "802", "鹽埕區": "803", "鼓山區": "804", "旗津區": "805", "前鎮區": "806", "三民區": "807", "楠梓區": "808", "小港區": "812", "左營區": "813", "仁武區": "814", "大社區": "815", "岡山區": "820", "路竹區": "821", "阿蓮區": "822", "田寮區": "823", "燕巢區": "824", "橋頭區": "825", "梓官區": "826", "彌陀區": "827", "永安區": "828", "湖內區": "829", "鳳山區": "830", "大寮區": "831", "林園區": "832", "鳥松區": "833", "大樹區": "834", "旗山區": "840", "美濃區": "842", "六龜區": "844", "內門區": "845", "杉林區": "846", "甲仙區": "847", "桃源區": "848", "那瑪夏區": "849", "茂林區": "851", "茄萣區": "852"},
    # ... 其他縣市省略，程式碼長度考量
}

# --- 2. 系統初始化 ---
st.set_page_config(page_title="樂福集團 HOUSE MANAGER AI", layout="wide", page_icon="🦅")

# 初始化 Session State (記憶體)
if 'addr_data' not in st.session_state:
    st.session_state.addr_data = {"city": "", "dist": "", "road": "", "sec": "", "lane": "", "alley": "", "no": "", "floor": ""}
if 'history' not in st.session_state:
    st.session_state.history = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_report' not in st.session_state:
    st.session_state.current_report = "" # 這裡存著 AI 的「內建估值」智慧

# CSS
st.markdown("""
    <style>
    .stTextInput>div>div>input, .stSelectbox>div>div>div { background-color: transparent; border: none; border-bottom: 2px solid #1e3a8a; border-radius: 0px; padding: 5px 0px; }
    h1 { color: #1e3a8a; font-family: 'Noto Sans TC', sans-serif; font-weight: 800; }
    .section-title { color: #334155; border-left: 5px solid #1e3a8a; padding-left: 15px; margin-top: 30px; margin-bottom: 15px; font-weight: bold; font-size: 1.25rem; }
    .ai-parser-box { background-color: #e0f2fe; padding: 20px; border-radius: 10px; border: 2px dashed #0284c7; margin-bottom: 20px; }
    .map-container { border: 2px solid #1e3a8a; border-radius: 10px; overflow: hidden; margin-top: 10px; margin-bottom: 10px; }
    .action-btn { display: inline-block; width: 100%; text-align: center; padding: 8px; margin: 3px 0; border-radius: 5px; text-decoration: none; color: white; font-weight: bold; transition: 0.3s; font-size: 0.9rem;}
    .btn-leju { background-color: #5F9EA0; }
    .btn-591 { background-color: #FF8C00; }
    .btn-google { background-color: #4682B4; }
    .btn-street { background-color: #FFC107; color: black; }
    .btn-life { background-color: #64748b; color: white; }
    .action-btn:hover { opacity: 0.9; }
    
    /* 對話框優化 */
    .stChatMessage { border-radius: 10px; padding: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
        return genai.GenerativeModel(model_name=target)
    except: return None

model = get_model()

# --- 3. 側邊欄：歷史戰報 ---
with st.sidebar:
    st.title("📜 歷史戰報")
    st.caption("點擊回顧過去的分析")
    if st.session_state.history:
        for i, record in enumerate(reversed(st.session_state.history)):
            btn_label = f"{record['time']} - {record['addr'][:6]}..."
            if st.button(btn_label, key=f"hist_{i}"):
                st.session_state.current_report = record['report']
                st.session_state.chat_history = [] # 換新報告時，清空對話
                st.info(f"已載入：{record['addr']}")
    else:
        st.write("尚無資料")

# --- 4. 主介面 ---
st.title("🦅 HOUSE MANAGER")
st.caption("鼎泰一不動產經紀有限公司 · 樂福集團 | 互動戰情室")

# 角色選擇
role_mode = st.radio("⚔️ 您的戰鬥位置？", ["🛡️ 開發方 (維護/屋主端)", "🏹 銷售方 (買方/帶看端)"], horizontal=True)

# A. 智能地址快搜
st.markdown('<div class="ai-parser-box">', unsafe_allow_html=True)
st.subheader("⚡ 智能地址快搜")
c_parse_1, c_parse_2 = st.columns([5, 1])
with c_parse_1:
    raw_addr_input = st.text_input("輸入範例：台中市北屯區松竹路一段100巷5號12樓", key="raw_addr")
with c_parse_2:
    st.write("") 
    do_parse = st.button("🔍 解析", type="primary", use_container_width=True)

if do_parse and raw_addr_input and model:
    with st.spinner("AI 拆解中..."):
        try:
            prompt = f"將地址拆解為JSON (city, dist, road, sec, lane, alley, no, floor): {raw_addr_input}。只回傳JSON。"
            resp = model.generate_content(prompt)
            parsed = json.loads(resp.text.replace('```json','').replace('```',''))
            st.session_state.addr_data.update(parsed)
            st.success("✅ 解析成功")
        except:
            st.error("解析失敗")
st.markdown('</div>', unsafe_allow_html=True)

# B. 地址與地圖
st.markdown('<div class="section-title">📍 物件位置</div>', unsafe_allow_html=True)
col_L, col_R = st.columns([1, 1])

with col_L:
    c1, c2 = st.columns(2)
    with c1: 
        curr_city = st.session_state.addr_data.get("city", "")
        sel_city = st.selectbox("城市", options=list(POSTAL_DATA.keys()), index=list(POSTAL_DATA.keys()).index(curr_city) if curr_city in POSTAL_DATA else 0)
    with c2:
        curr_dist = st.session_state.addr_data.get("dist", "")
        opts = list(POSTAL_DATA[sel_city].keys())
        sel_dist = st.selectbox("區域", options=opts, index=opts.index(curr_dist) if curr_dist in opts else 0)

    st.caption(f"📮 郵遞區號：{POSTAL_DATA[sel_city][sel_dist]}")

    r1, r2 = st.columns([2, 1])
    with r1: road_name = st.text_input("路名", value=st.session_state.addr_data.get("road", ""))
    with r2: addr_sec = st.text_input("段", value=st.session_state.addr_data.get("sec", ""))

    r3, r4, r5 = st.columns(3)
    with r3: addr_lane = st.text_input("巷", value=st.session_state.addr_data.get("lane", ""))
    with r4: addr_alley = st.text_input("弄", value=st.session_state.addr_data.get("alley", ""))
    with r5: addr_num = st.text_input("號", value=st.session_state.addr_data.get("no", ""))
    addr_floor = st.text_input("樓層", value=st.session_state.addr_data.get("floor", ""))

map_addr = f"{sel_city}{sel_dist}{road_name}{addr_sec+'段' if addr_sec else ''}{addr_lane+'巷' if addr_lane else ''}{addr_alley+'弄' if addr_alley else ''}{addr_num+'號' if addr_num else ''}"
full_addr_str = map_addr + (f"{addr_floor}樓" if addr_floor else "")

with col_R:
    if road_name:
        q_url = urllib.parse.quote(map_addr)
        st.markdown(f"""
        <div class="map-container">
            <iframe width="100%" height="250" frameborder="0" style="border:0" 
            src="https://maps.google.com/maps?q={q_url}&output=embed" allowfullscreen></iframe>
        </div>
        """, unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        with b1: st.markdown(f'<a href="https://www.google.com/maps/search/?api=1&query={q_url}" target="_blank" class="action-btn btn-street">👀 720° 街景</a>', unsafe_allow_html=True)
        with b2: st.markdown(f'<a href="https://www.google.com/maps/search/{urllib.parse.quote(map_addr+" 學校")}" target="_blank" class="action-btn btn-life">🏫 查學區</a>', unsafe_allow_html=True)
        with b3: st.markdown(f'<a href="https://www.google.com/maps/search/{urllib.parse.quote(map_addr+" 市場")}" target="_blank" class="action-btn btn-life">🥦 查市場</a>', unsafe_allow_html=True)
    else:
        st.info("👈 請輸入路名顯示地圖")

# C. 戰情室
st.markdown('<div class="section-title">📉 戰情室</div>', unsafe_allow_html=True)
with st.form("battle_form"):
    c_name = st.text_input("🏢 案名/社區")
    if c_name:
        q_url = urllib.parse.quote(f"{sel_city}{sel_dist} {c_name}")
        st.markdown(f'<a href="https://www.google.com/search?q={q_url}" target="_blank" class="action-btn btn-google">🌍 Google 全網搜</a>', unsafe_allow_html=True)

    st.markdown("---")
    p1, p2, p3 = st.columns(3)
    with p1: c_main = st.text_input("🏠 主建物")
    with p2: c_sub = st.text_input("➕ 附屬")
    with p3: c_public = st.text_input("🏢 公設")
    p4, p5 = st.columns(2)
    with p4: c_total = st.text_input("📊 總坪")
    with p5: c_land = st.text_input("🌱 地坪")

    st.markdown("##### 💰 價格與機密")
    pr1, pr2, pr3 = st.columns(3)
    with pr1: c_price = st.text_input("本案開價 (萬)")
    with pr2: internal_val = st.text_input("🔒 樂福內建估值")
    with pr3: coop_status = st.text_input("合作狀況")
    
    sec1, sec2 = st.columns(2)
    with sec1: owner_expect = st.text_input("屋主底價", placeholder="機密")
    with sec2: past_offer = st.text_input("最高出價紀錄", placeholder="機密")

    o1, o2, o3 = st.columns(3)
    with o1: c_age = st.text_input("屋齡")
    with o2: c_face = st.text_input("朝向")
    with o3: c_agent = st.text_input("經紀人")

    btn_text = "🔥 啟動開發回報" if "開發" in role_mode else "🚀 啟動銷售戰略"
    submitted = st.form_submit_button(btn_text)

# --- 5. 生成報告 ---
if submitted and model:
    role_prompt = "針對屋主進行議價回報，找出降價理由。" if "開發" in role_mode else "針對買方進行銷售，放大優勢與稀有性。"
    
    with st.spinner("🦁 教練思考中..."):
        try:
            prompt = f"""
            角色：樂福集團金牌教練 ({role_mode})。
            目標：{role_prompt}
            
            物件：{full_addr_str} ({c_name})
            開價：{c_price}萬 / 內建估值：{internal_val}萬。
            屋主底價：{owner_expect} / 曾經出價：{past_offer}。
            
            任務：
            1. (機能): 具體指出附近的學校、市場名稱。
            2. (價格): 分析 開價 vs 估值 vs 底價 的差距。
            3. (戰略): 給出具體話術。
            """
            resp = model.generate_content(prompt)
            st.session_state.current_report = resp.text
            
            # 存入歷史
            st.session_state.history.append({
                "time": datetime.datetime.now().strftime("%H:%M"),
                "addr": full_addr_str,
                "report": resp.text
            })
            st.session_state.chat_history = [] # 新報告清空對話
        except Exception as e:
            st.error(f"錯誤：{e}")

# --- 6. 報告與對話框 (核心新增) ---
if st.session_state.current_report:
    st.markdown("---")
    st.subheader(f"📋 {role_mode} 戰略報告")
    st.info(f"📍 分析中：{full_addr_str}")
    st.markdown(st.session_state.current_report)
    
    st.markdown("---")
    st.subheader("💬 戰情室對話 (針對本案追問)")
    
    # 顯示對話歷史
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # 對話輸入區
    if user_input := st.chat_input("例如：屋主如果說不急著賣怎麼辦？"):
        # 1. 顯示 User 訊息
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # 2. AI 回答
        with st.chat_message("assistant"):
            with st.spinner("教練推演中..."):
                # 將「當前報告」作為背景知識傳給 AI
                chat_prompt = f"""
                背景報告：
                {st.session_state.current_report}
                
                目前身分：{role_mode}
                經紀人提問：{user_input}
                
                請根據報告內容與內建估值，給出具體戰術建議。
                """
                chat_resp = model.generate_content(chat_prompt)
                st.markdown(chat_resp.text)
                st.session_state.chat_history.append({"role": "assistant", "content": chat_resp.text})
