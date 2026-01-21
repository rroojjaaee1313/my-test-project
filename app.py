import streamlit as st
import google.generativeai as genai
import urllib.parse
import json
import datetime
import pandas as pd

# --- 1. 資料庫 (資料省略，請保持原本的完整字典) ---
POSTAL_DATA = { "臺中市": {"北屯區": "406", "西屯區": "407"}, "臺北市": {"中正區": "100"} } # 此處僅縮略，請用您原本完整的

# --- 2. 系統初始化與日誌管理 ---
st.set_page_config(page_title="樂福集團 HOUSE MANAGER", layout="wide", page_icon="🦅")

# 初始化日誌 (模擬資料庫)
if 'usage_logs' not in st.session_state:
    st.session_state.usage_logs = []
if 'addr_data' not in st.session_state:
    st.session_state.addr_data = {"city": "", "dist": "", "road": "", "sec": "", "lane": "", "alley": "", "no": "", "floor": ""}

# CSS 高質感底線風格
st.markdown("""
    <style>
    .stTextInput>div>div>input { background-color: transparent; border: none; border-bottom: 2px solid #1e3a8a; border-radius: 0px; }
    .section-title { color: #334155; border-left: 5px solid #1e3a8a; padding-left: 15px; margin-top: 20px; font-weight: bold; }
    .action-btn { display: inline-block; width: 100%; text-align: center; padding: 10px; margin: 5px 0; border-radius: 8px; text-decoration: none; color: white; font-weight: bold; }
    .btn-street { background-color: #FFC107; color: black; }
    .stRadio>div{gap: 20px;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('models/gemini-1.5-flash')

model = get_model()

# --- 3. 側邊欄：導航與管理員專區 ---
with st.sidebar:
    st.title("🦅 戰情選單")
    nav = st.radio("前往頁面", ["🎯 戰報生成器", "📊 管理儀表板"])
    
    if nav == "📊 管理儀表板":
        st.markdown("---")
        pwd = st.text_input("輸入管理員密碼", type="password")
        if pwd != "Love168": # 這是您的管理密碼
            st.error("密碼錯誤，無法存取數據")
            st.stop()

# --- 4. 介面 A：戰報生成器 (分流邏輯) ---
if nav == "🎯 戰報生成器":
    st.title("🦅 HOUSE MANAGER AI")
    
    # 【核心分流選擇】
    battle_type = st.radio("⚔️ 請選擇目前的任務：", ["🛡️ 開發/議價 (對屋主)", "🏹 銷售/包裝 (對買方)"], horizontal=True)

    # 1. 智能解析
    st.markdown('<div style="background:#f0f9ff; padding:15px; border-radius:10px;">', unsafe_allow_html=True)
    raw_addr = st.text_input("⚡ 智能地址快搜 (直接貼上地址)")
    if st.button("🔍 AI 解析地址"):
        if model and raw_addr:
            resp = model.generate_content(f"將此地址拆解為JSON (city, dist, road, sec, lane, alley, no, floor): {raw_addr}。只回傳JSON。")
            st.session_state.addr_data.update(json.loads(resp.text.replace('```json','').replace('```','')))
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. 基本資料與地圖 (共用)
    st.markdown('<div class="section-title">📍 物件位置與地圖</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1: 
        city = st.text_input("城市", value=st.session_state.addr_data['city'])
    with c2: 
        dist = st.text_input("區域", value=st.session_state.addr_data['dist'])
    with c3:
        road = st.text_input("路街名", value=st.session_state.addr_data['road'])
    
    full_addr = f"{city}{dist}{road}"
    q_url = urllib.parse.quote(full_addr)
    st.markdown(f'<iframe width="100%" height="250" frameborder="0" src="https://maps.google.com/maps?q={q_url}&output=embed"></iframe>', unsafe_allow_html=True)
    st.markdown(f'<a href="https://www.google.com/maps/search/?api=1&query={q_url}" target="_blank" class="action-btn btn-street">👀 開啟 720° 現場實景</a>', unsafe_allow_html=True)

    # 3. 根據分流顯示不同的表單
    with st.form("battle_form"):
        st.markdown(f'<div class="section-title">📉 {battle_type} 專用欄位</div>', unsafe_allow_html=True)
        agent_name = st.text_input("👤 經紀人姓名")
        c_price = st.text_input("💰 目前開價 (萬)")
        
        if "開發" in battle_type:
            # 開發方專用：著重於底價與回報
            col1, col2 = st.columns(2)
            with col1: expect_price = st.text_input("屋主底價/期望 (萬)")
            with col2: last_offer = st.text_input("最高出價紀錄 (萬)")
            owner_mood = st.selectbox("屋主心態", ["硬朗", "動搖", "急售", "試水溫"])
            target_desc = "請教我如何回報並成功議價"
        else:
            # 銷售方專用：著重於坪數與特色
            col1, col2, col3 = st.columns(3)
            with col1: main_area = st.text_input("主建物坪")
            with col2: total_area = st.text_input("總建坪")
            with col3: internal_val = st.text_input("🔒 內建估值")
            buyer_focus = st.text_input("買方在意點", placeholder="例如：嫌路太窄、採光...")
            target_desc = "請教我如何包裝亮點並促成出價"

        if st.form_submit_button("🔥 啟動 AI 戰略分析"):
            # 存入日誌
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.usage_logs.append({
                "時間": now, "經紀人": agent_name, "角色": battle_type, "地址": full_addr, "金額": c_price
            })
            
            # AI 邏輯
            with st.spinner("教練正在布陣..."):
                prompt = f"""
                你是樂福集團金牌教練。身分是 {battle_type} 的助手。
                地址：{full_addr}。開價：{c_price}萬。
                {f'屋主期望：{expect_price}，最高出價：{last_offer}' if "開發" in battle_type else f'主建：{main_area}，內建估值：{internal_val}'}
                任務：
                1. 列出具體的學區名稱、最近市場名稱。
                2. 針對 {battle_type} 提供具體的攻防話術。
                """
                resp = model.generate_content(prompt)
                st.write(resp.text)

# --- 5. 介面 B：管理儀表板 ---
elif nav == "📊 管理儀表板":
    st.title("🔒 樂福管理員儀表板")
    
    if not st.session_state.usage_logs:
        st.info("目前尚無使用紀錄")
    else:
        df = pd.DataFrame(st.session_state.usage_logs)
        
        # 1. 統計數字
        c1, c2, c3 = st.columns(3)
        c1.metric("總查詢次數", len(df))
        c2.metric("活躍經紀人", len(df["經紀人"].unique()))
        c3.metric("最熱門區域", df["地址"].str[:3].mode()[0])

        # 2. 詳細列表
        st.markdown("### 📝 詳細使用流水帳")
        st.table(df)

        # 3. 頻率分析
        st.markdown("### 👤 經紀人排行")
        st.bar_chart(df["經紀人"].value_content())
