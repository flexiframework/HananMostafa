import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS

# 1. Page Config (Force LTR for English)
st.set_page_config(page_title="Flexi AI Tutor - EN", layout="wide")
st.markdown('<style>.main {direction: ltr; text-align: left;}</style>', unsafe_allow_html=True)

# 2. API Setup
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Missing API Key in Secrets!")
    st.stop()

# 3. Smart Model Selection (Prevents 404 Error)
@st.cache_resource
def get_safe_model():
    try:
        # البحث عن أي موديل متاح في حسابك بدلاً من كتابة الاسم يدوياً
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # نفضل فلاش 1.5 إذا وجده، وإلا سيأخذ أول واحد يعمل
                if '1.5-flash' in m.name:
                    return genai.GenerativeModel(m.name)
        return genai.GenerativeModel('gemini-pro')
    except:
        # إذا فشل البحث، نستخدم الاسم المختصر الذي يقبله النظام دائماً
        return genai.GenerativeModel('gemini-pro')

# 4. Caching Response (Prevents 429 Error)
@st.cache_data(ttl=3600)
def get_lesson_content(topic):
    model = get_safe_model()
    response = model.generate_content(f"Explain this lesson simply in English: {topic}")
    return response.text

# 5. UI Logic
st.title("🎓 Flexy Smart Assistant (EN)")

# جلب البيانات من الموودل
query_params = st.query_params
topic = query_params.get("topic", "") or query_params.get("links", "")

if not topic:
    st.warning("Please open this page from Moodle context.")
else:
    if st.button("Start Lesson Now ✨"):
        with st.spinner("Flexy is preparing your lesson..."):
            try:
                res = get_lesson_content(topic)
                st.session_state.lesson_en = res
                st.rerun()
            except Exception as e:
                st.error(f"Technical error: {str(e)}")

# عرض المحتوى
if 'lesson_en' in st.session_state:
    st.markdown(f'<div style="background:#f0f2f6; padding:25px; border-radius:15px; border-left: 5px solid #002e5b;">{st.session_state.lesson_en.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
