import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import os
import io
import PIL.Image
import json

# 1. 系統初始化與金鑰
API_KEY = "AIzaSyCALV4Zyjpc5h5_7DJpy-OXha19QTVXbIE"
genai.configure(api_key=API_KEY)
st.set_page_config(page_title="老鷹 AI 長期助理", layout="wide")

# 初始化模型
model = genai.GenerativeModel('models/gemini-1.5-flash')

# --- 記憶功能：讀取與儲存 JSON 檔案 ---
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# 初始化 Session State 中的對話紀錄
if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 介面設計 ---
st.title("🦅 老鷹團隊：長期 AI 智慧助理")

with st.sidebar:
    st.header("⚙️ 助理管理")
    if st.button("🗑️ 清空所有對話紀錄"):
        st.session_state.messages = []
        save_history([])
        st.rerun()
    
    st.divider()
    uploaded_pdf = st.file_uploader("上傳培訓教材 (PDF)", type="pdf")
    uploaded_image = st.file_uploader("上傳對話截圖 (分析用)", type=["png", "jpg", "jpeg"])

# 處理 PDF 知識庫
context_text = ""
if uploaded_pdf:
    reader = PdfReader(uploaded_pdf)
    for page in reader.pages:
        context_text += page.extract_text() + "\n"

# --- 顯示歷史對話紀錄 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 使用者輸入區 (Chat Input) ---
if prompt := st.chat_input("請問導師..."):
    # 1. 顯示使用者訊息
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. 準備分析內容
    content_list = []
    if uploaded_image:
        img = PIL.Image.open(uploaded_image)
        content_list.append(img)
    
    # 加入教材背景與歷史紀錄的脈絡
    history_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]]) # 只取最近5則
    full_prompt = f"你是老鷹團隊導師。教材內容：\n{context_text[:5000]}\n近期對話：\n{history_context}\n現在問題：{prompt}"
    content_list.append(full_prompt)

    # 3. 獲取 AI 回覆
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            response = model.generate_content(content_list)
            full_response = response.text
            st.markdown(full_response)
            
            # 生成語音按鈕
            tts = gTTS(text=full_response[:200], lang='zh-tw') # 取前200字生成語音避免過長
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.audio(audio_fp, format='audio/mp3')

    # 4. 存入記憶
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    save_history(st.session_state.messages)
