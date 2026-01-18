import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import os
import io
import PIL.Image
import json

# --- 1. 系統初始化 (使用最新的 Secrets 讀取方式) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error("❌ 找不到 API 金鑰，請檢查 Streamlit Secrets 設定。")
    st.stop()

st.set_page_config(page_title="老鷹 AI 長期助理", layout="wide")

# 使用穩定版的模型名稱格式
MODEL_NAME = 'gemini-1.5-flash'
# 初始化模型
try:
    model = genai.GenerativeModel(model_name=MODEL_NAME)
except Exception as e:
    st.error(f"❌ 無法讀取模型 {MODEL_NAME}，錯誤內容: {e}")
    st.stop()

# --- 2. 記憶功能 (JSON 儲存) ---
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 3. 介面設計 ---
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

# 處理 PDF
context_text = ""
if uploaded_pdf:
    try:
        reader = PdfReader(uploaded_pdf)
        for page in reader.pages:
            context_text += page.extract_text() + "\n"
        st.sidebar.success("✅ 教材已載入")
    except Exception as e:
        st.sidebar.error(f"PDF 讀取失敗: {e}")

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
        try:
            img = PIL.Image.open(uploaded_image)
            content_list.append(img)
        except:
            st.error("圖片格式錯誤")

    # 組合脈絡
    history_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-3:]])
    full_prompt = f"你是一位專業的老鷹團隊導師。教材背景：\n{context_text[:5000]}\n近期對話：\n{history_context}\n現在問題：{prompt}"
    content_list.append(full_prompt)

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                # 核心調用處
                response = model.generate_content(content_list)
                full_response = response.text
                st.markdown(full_response)
                
                # 語音生成
                tts = gTTS(text=full_response[:150], lang='zh-tw')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format='audio/mp3')

                # 儲存對話
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                save_history(st.session_state.messages)
            except Exception as e:
                st.error(f"⚠️ 發生錯誤: {e}")
                st.info("請確認您的 API 金鑰是否有效，以及該模型是否支援您的所在地區。")
