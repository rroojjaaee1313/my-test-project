import streamlit as st
import google.generativeai as genai
import urllib.parse
import json

# --- 1. 全台完整行政區與郵遞區號資料庫 ---
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

# --- 2. 系統設定 ---
st.set_page_config(page_title="樂福集團 HOUSE MANAGER AI", layout="wide", page_icon="🦅")

if 'addr_data' not in st.session_state:
    st.session_state.addr_data = {
        "city": "", "dist": "", "road": "", "sec": "", 
        "lane": "", "alley": "", "no": "", "floor": ""
    }

# CSS
st.markdown("""
    <style>
    .stTextInput>div>div>input, .stSelectbox>div>div>div { background-color: transparent; border: none; border-bottom: 2px solid #1e3a8a; border-radius: 0px; padding: 5px 0px; }
    h1 { color: #1e3a8a; font-family: 'Noto Sans TC', sans-serif; font-weight: 800; }
    .section-title { color: #334155; border-left: 5px solid #1e3a8a; padding-left: 15px; margin-top: 30px; margin-bottom: 15px; font-weight: bold; font-size: 1.25rem; }
    .ai-parser-box { background-color: #e0f2fe; padding: 20px; border-radius: 10px; border: 2px dashed #0284c7; margin-bottom: 20px; }
    .map-container { border: 2px solid #1e3a8a; border-radius: 10px; overflow: hidden; margin-top: 10px; margin-bottom: 10px; }
    
    /* 按鈕 */
    .action-btn { display: inline-block; width: 100%; text-align: center; padding: 8px; margin: 3px 0; border-radius: 5px; text-decoration: none; color: white; font-weight: bold; transition: 0.3s; font-size: 0.9rem;}
    .btn-leju { background-color: #5F9EA0; }
    .btn-591 { background-color: #FF8C00; }
    .btn-google { background-color: #4682B4; }
    .btn-street { background-color: #FFC107; color: black; }
    .btn-life { background-color: #64748b; color: white; }
    .action-btn:hover { opacity: 0.9; }
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
        # 指令升級：加入「攻防策略」邏輯
        instruction = """
        你現在是樂福集團的【金牌房產戰略教練】。
        
        【任務重點】：
        1. 嚴禁使用模糊字眼，必須具體指名學校、市場、公園名稱。
        2. 【攻防策略核心】：你將獲得「開價」、「曾經出價紀錄(下斡沒成)」與「屋主期望底價」。
           - 若 (曾經出價) < (內建估值) < (屋主期望)：分析差距，給出如何「向上管理屋主」的策略。
           - 若 (曾經出價) 接近 (屋主期望)：分析成交關鍵點，給出臨門一腳的話術。
           - 若 (開價) 遠高於 (市場行情)：給出「殺價與議價」的數據子彈。
        3. 語氣：專業、數據導向、霸氣。
        """
        return genai.GenerativeModel(model_name=target, system_instruction=instruction)
    except: return None

model = get_model()

# --- 3. 介面設計 ---
st.title("🦅 HOUSE MANAGER")
st.caption("鼎泰一不動產經紀有限公司 · 樂福集團 | 談判攻防戰略版")

# === A. ⚡ 智能地址快搜 ===
st.markdown('<div class="ai-parser-box">', unsafe_allow_html=True)
st.subheader("⚡ 智能地址快搜 (貼上整串地址，AI 自動填表)")
c_parse_1, c_parse_2 = st.columns([5, 1])
with c_parse_1:
    raw_addr_input = st.text_input("輸入範例：台中市北屯區松竹路一段100巷5號12樓", key="raw_addr")
with c_parse_2:
    st.write("") 
    do_parse = st.button("🔍 AI 解析", type="primary", use_container_width=True)

if do_parse and raw_addr_input and model:
    with st.spinner("AI 正在拆解門牌..."):
        try:
            prompt = f"""
            將此地址拆解為JSON (若無該欄位則留空):
            地址: {raw_addr_input}
            欄位: city(縣市), dist(區), road(路街), sec(段), lane(巷), alley(弄), no(號), floor(樓)
            只回傳JSON。
            """
            resp = model.generate_content(prompt)
            parsed = json.loads(resp.text.replace('```json','').replace('```',''))
            st.session_state.addr_data.update(parsed)
            st.success("✅ 解析完成！")
        except:
            st.error("解析失敗，請手動輸入")
st.markdown('</div>', unsafe_allow_html=True)

# === B. 詳細門牌與地圖連動 ===
st.markdown('<div class="section-title">📍 物件位置與實景</div>', unsafe_allow_html=True)

col_L, col_R = st.columns([1, 1])

with col_L:
    c1, c2 = st.columns(2)
    with c1: 
        current_city = st.session_state.addr_data.get("city", "")
        if current_city in POSTAL_DATA:
            sel_city = st.selectbox("城市 *", options=list(POSTAL_DATA.keys()), index=list(POSTAL_DATA.keys()).index(current_city))
        else:
            sel_city = st.selectbox("城市 *", options=list(POSTAL_DATA.keys()), index=0)

    with c2:
        current_dist = st.session_state.addr_data.get("dist", "")
        dist_opts = list(POSTAL_DATA[sel_city].keys())
        idx_dist = dist_opts.index(current_dist) if current_dist in dist_opts else 0
        sel_dist = st.selectbox("鄉/鎮/市/區 *", options=dist_opts, index=idx_dist)

    p_code = POSTAL_DATA[sel_city][sel_dist]
    st.caption(f"📮 郵遞區號：{p_code}")

    r1, r2 = st.columns([2, 1])
    with r1: road_name = st.text_input("路/街名 *", value=st.session_state.addr_data.get("road", ""))
    with r2: addr_sec = st.text_input("段", value=st.session_state.addr_data.get("sec", ""))

    r3, r4, r5 = st.columns(3)
    with r3: addr_lane = st.text_input("巷", value=st.session_state.addr_data.get("lane", ""))
    with r4: addr_alley = st.text_input("弄", value=st.session_state.addr_data.get("alley", ""))
    with r5: addr_num = st.text_input("號", value=st.session_state.addr_data.get("no", ""))
    
    addr_floor = st.text_input("樓層", value=st.session_state.addr_data.get("floor", ""))

map_addr = f"{sel_city}{sel_dist}{road_name}"
if addr_sec: map_addr += f"{addr_sec}段"
if addr_lane: map_addr += f"{addr_lane}巷"
if addr_alley: map_addr += f"{addr_alley}弄"
if addr_num: map_addr += f"{addr_num}號"

with col_R:
    if road_name:
        q_url = urllib.parse.quote(map_addr)
        st.markdown(f"""
        <div class="map-container">
            <iframe width="100%" height="250" frameborder="0" style="border:0" 
            src="https://maps.google.com/maps?q={q_url}&output=embed" allowfullscreen></iframe>
        </div>
        """, unsafe_allow_html=True)
        
        b_street, b_school, b_market = st.columns(3)
        with b_street: 
            st.markdown(f'<a href="https://www.google.com/maps/search/?api=1&query={q_url}" target="_blank" class="action-btn btn-street">👀 720° 街景</a>', unsafe_allow_html=True)
        with b_school:
            q_school = urllib.parse.quote(f"{map_addr} 國小 國中")
            st.markdown(f'<a href="https://www.google.com/maps/search/{q_school}" target="_blank" class="action-btn btn-life">🏫 查學區</a>', unsafe_allow_html=True)
        with b_market:
            q_market = urllib.parse.quote(f"{map_addr} 市場 全聯")
            st.markdown(f'<a href="https://www.google.com/maps/search/{q_market}" target="_blank" class="action-btn btn-life">🥦 查市場</a>', unsafe_allow_html=True)

    else:
        st.info("👈 請輸入地址顯示地圖與機能按鈕")

# === C. 戰情室 ===
st.markdown('<div class="section-title">📉 戰情室 (指名度與攻防)</div>', unsafe_allow_html=True)

with st.form("battle_room_form"):
    c_name = st.text_input("🏢 案名/社區名稱")
    
    if c_name:
        leju_q = urllib.parse.quote(c_name)
        q_591 = urllib.parse.quote(f"{sel_city}{sel_dist} {c_name}")
        st.markdown("🔍 **外部行情偵查**：")
        b1, b2, b3 = st.columns(3)
        with b1: st.markdown(f'<a href="https://www.leju.com.tw/community?keyword={leju_q}" target="_blank" class="action-btn btn-leju">🏠 樂居實價</a>', unsafe_allow_html=True)
        with b2: st.markdown(f'<a href="https://market.591.com.tw/list?keywords={q_591}" target="_blank" class="action-btn btn-591">🔢 591 行情</a>', unsafe_allow_html=True)
        with b3: st.markdown(f'<a href="https://www.google.com/search?q={q_591}" target="_blank" class="action-btn btn-google">🌍 Google 全搜</a>', unsafe_allow_html=True)

    st.markdown("---")
    p1, p2, p3 = st.columns(3)
    with p1: c_main = st.text_input("🏠 主建物")
    with p2: c_sub = st.text_input("➕ 附屬建物")
    with p3: c_public = st.text_input("🏢 公設坪數")

    p4, p5 = st.columns(2)
    with p4: c_total = st.text_input("📊 權狀總坪")
    with p5: c_land = st.text_input("🌱 持分地坪")

    st.markdown("##### 💰 價格戰略 (核心數據)")
    price_cols = st.columns(3)
    with price_cols[0]: c_price = st.text_input("本案開價 (萬)")
    with price_cols[1]: internal_val = st.text_input("🔒 樂福內建估值 (萬)")
    with price_cols[2]: coop_status = st.text_input("合作狀況")
    
    # --- 🆕 新增：攻防策略機密區 ---
    st.markdown("##### 🔐 談判機密檔案 (攻防分析用)")
    secret_c1, secret_c2 = st.columns(2)
    with secret_c1:
        owner_expect = st.text_input("屋主期望價格 (心中底價)", placeholder="選填，若知道請填入")
    with secret_c2:
        past_offer = st.text_input("曾經出價紀錄 (下斡沒成)", placeholder="選填，市場驗證過的價格")

    other_cols = st.columns(3)
    with other_cols[0]: c_age = st.text_input("屋齡")
    with other_cols[1]: c_face = st.text_input("朝向")
    with other_cols[2]: c_agent = st.text_input("經紀人姓名")

    submitted = st.form_submit_button("🔥 啟動攻防戰略分析")

# --- 4. AI 分析邏輯 ---
if submitted:
    if model:
        full_addr_str = map_addr + (f"{addr_floor}樓" if addr_floor else "")
        with st.spinner("🦁 金牌教練正在推演攻防戰術..."):
            try:
                prompt = f"""
                經紀人：{c_agent} (樂福集團)。
                物件地址：{full_addr_str} ({c_name})。
                屋齡：{c_age}。
                
                【戰略數據】：
                開價：{c_price}萬 / 總坪：{c_total} / 主+附：{c_main}+{c_sub}。
                樂福內建估值：{internal_val} 萬。
                
                【談判機密】：
                屋主期望(底價)：{owner_expect} 萬。
                曾經最高出價(失敗)：{past_offer} 萬。
                
                【任務】：
                1. (機能指名)：具體列出附近的學校(指定校名)、市場(指定名稱)、公園。
                2. (價格三角分析)：請詳細分析「曾經出價」vs「屋主底價」vs「內建估值」的差距。
                3. (攻防策略)：
                   - 若有「曾經出價」但沒成，請分析買方心態與屋主堅持點。
                   - 提供下一步的議價策略(如何打破屋主堅持)與銷售策略(如何說服新買家)。
                """
                response = model.generate_content(prompt)
                st.info(f"📍 分析目標：{full_addr_str}")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"分析中斷：{e}")
