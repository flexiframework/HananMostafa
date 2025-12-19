import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS
import streamlit.components.v1 as components

# 1. Page Config & Visual Identity
st.set_page_config(page_title="Flexi AI Tutor - EN", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none !important;}
    :root { --flexi-blue: #002e5b; }
    .main { direction: ltr; text-align: left; }
    [data-testid="stSidebar"] { background-color: #002e5b !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .lesson-area { 
        direction: ltr; text-align: left; line-height: 1.6; 
        padding: 30px; border-left: 8px solid #002e5b; 
        background-color: #f8f9fa; border-radius: 10px; color: #333;
    }
    .stButton>button { 
        background-color: #002e5b !important; color: white !important; 
        border-radius: 10px !important; width: 100%; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. API Setup & Dynamic Model Selection
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key Missing!")
    st.stop()

@st.cache_resource
def get_model():
    # محاولة البحث عن الموديل المتاح لتجنب خطأ 404 نهائياً
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for name in available:
            if '1.5-flash' in name: return genai.GenerativeModel(name)
        return genai.GenerativeModel(available[0])
    except:
        return genai.GenerativeModel('gemini-pro')

@st.cache_data(ttl=3600)
def get_ai_response(prompt_text):
    model = get_model()
    response = model.generate_content(prompt_text)
    return response.text

# 3. Sidebar
with st.sidebar:
    st.image("https://flexiacademy.com/assets/images/flexi-logo-2021.png", width=180)
    st.markdown("---")
    st.subheader("Student Dashboard")
    student_name = st.text_input("Student Name:", value="Flexian Student")
    content_format = st.selectbox("Format:", ["Interactive Lesson", "Comic Story", "Video Script"])
    level = st.selectbox("Level:", ["Beginner", "Intermediate", "Advanced"])
    learning_style = st.radio("Learning Style:", ["Visual (Images)", "Auditory (Audio)", "Kinesthetic (Activities)"])
    
    if 'score_en' not in st.session_state: st.session_state.score_en = 0
    st.metric("🏆 Achievement Points", st.session_state.score_en)
    
    st.divider()
    components.html("""
        <script>function printPage() { window.parent.print(); }</script>
        <button onclick="printPage()" style="width: 100%; background-color: white; color: #002e5b; padding: 10px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">🖨️ Print to PDF</button>
    """, height=50)

# 4. Main UI Logic
query_params = st.query_params
target_topic = query_params.get("links", "") or query_params.get("topic", "")

st.title("🎓 Flexy Smart Assistant (EN)")

if not target_topic:
    st.warning("Waiting for lesson data from Moodle...")
else:
    if st.button("Start Lesson Now ✨"):
        with st.spinner("Flexy AI is analyzing the content for you..."):
            prompt = f"Expert tutor at Flexi Academy. Topic: {target_topic}. Level: {level}. Style: {learning_style}. Format: {content_format}. End with 3 True/False questions: TF_START Q: | A: TF_END."
            try:
                res_text = get_ai_response(prompt)
                st.session_state.lesson_en = res_text
                # Voice logic
                clean_text = re.sub(r'\[\[.*?\]\]|TF_START.*?TF_END', '', res_text)
                tts = gTTS(text=clean_text[:500], lang='en')
                tts.save("voice_en.mp3")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# 5. Display Content
if st.session_state.get('lesson_en'):
    res = st.session_state.lesson_en
    if os.path.exists("voice_en.mp3"): st.audio("voice_en.mp3")
    
    # Image Display
    imgs = re.findall(r'\[\[(.*?)\]\]', res)
    if imgs: st.image(f"https://pollinations.ai/p/{imgs[0].replace(' ', '%20')}?width=1000&height=400&model=flux")
    
    # Text Display
    st.markdown(f'<div class="lesson-area">{res.split("TF_START")[0].replace("\n", "<br>")}</div>', unsafe_allow_html=True)
    
    # Quiz Logic
    if "TF_START" in res:
        st.divider()
        st.subheader("📝 Quiz")
        try:
            tf_part = re.search(r'TF_START(.*?)TF_END', res, re.DOTALL).group(1)
            for i, line in enumerate([l for l in tf_part.strip().split("\n") if "|" in l]):
                q, a = line.split("|")
                ans = st.radio(f"{q.replace('Q:', '').strip()}", ["True ✅", "False ❌"], key=f"en_q_{i}")
                if st.button(f"Submit Answer {i+1}", key=f"en_b_{i}"):
                    if (ans == "True ✅" and "True" in a) or (ans == "False ❌" and "False" in a):
                        st.success("Correct!"); st.balloons(); st.session_state.score_en += 10
                    else: st.error("Try again!")
        except: pass
