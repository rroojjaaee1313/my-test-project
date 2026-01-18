import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import os
import io
import PIL.Image
import json

# --- 1. 系統初始化 (強化模型相容性) ---
st.set_page_config(page_title="老鷹 AI 長期助理", layout="wide")

try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=API_KEY)
    else:
        st.error("❌ 找不到 API 金鑰，請檢查 Streamlit Secrets 設定。")
        st.stop()

    # 自動偵測可用的模型名稱 (避開 v1beta 404 問題)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # 優先找 1.5 flash，如果沒有就找第一個可用的
    MODEL_NAME = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    
    model = genai.GenerativeModel(model_name=MODEL_NAME)
    
except Exception as e:
    st.error(f"❌ 系統啟動失敗，請確認 API Key 是否正確。錯誤訊息: {e}")
    st.stop()

# --- 2. 記憶功能 ---
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 3. 介面設計 ---
st.title("🦅 老鷹團隊：長期 AI 智慧助理")
st.caption(f"目前運作模型: {MODEL_NAME}") # 方便我們檢查

with st.sidebar:
    st.header("⚙️ 助理管理")
    if st.button("🗑️ 清空所有對話紀錄"):
        st.session_state.messages = []
        save_history([])
        st.rerun()
    st.divider()
    uploaded_pdf = st.file_uploader("上傳培訓教材 (PDF)", type="pdf")
    uploaded_image = st.file_uploader("上傳對話截圖 (分析用)", type=["png", "jpg", "jpeg"])

# PDF 處理邏輯
context_text = ""
if uploaded_pdf:
    reader = PdfReader(uploaded_pdf)
    for page in reader.pages:
        context_text += page.extract_text() + "\n"
    st.sidebar.success("✅ 教材已載入")

# 顯示歷史紀錄
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. 問答邏輯 ---
if prompt := st.chat_input("請問導師..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    content_list = []
    if uploaded_image:
        img = PIL.Image.open(uploaded_image)
        content_list.append(img)

    history_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-3:]])
    full_prompt = f"你是一位專業的老鷹團隊導師。教材內容：\n{context_text[:4000]}\n近期對話：\n{history_context}\n現在問題：{prompt}"
    content_list.append(full_prompt)

    with st.chat_message("assistant"):
        with st.spinner("老鷹導師思考中..."):
            try:
                response = model.generate_content(content_list)
                full_response = response.text
                st.markdown(full_response)
                
                # 語音生成
                tts = gTTS(text=full_response[:100], lang='zh-tw')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format='audio/mp3')

                # 儲存紀錄
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                save_history(st.session_state.messages)
            except Exception as e:
                st.error(f"⚠️ 呼叫 AI 失敗: {e}")
