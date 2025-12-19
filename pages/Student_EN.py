import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS

# 1. إعدادات الصفحة واللغة (من اليسار لليمين)
st.set_page_config(page_title="Flexi AI Tutor - EN", layout="wide")
st.markdown("""<style>.main { direction: ltr; text-align: left; }</style>""", unsafe_allow_html=True)

# 2. جلب البيانات من الرابط
query_params = st.query_params
links_context = query_params.get("links", "")
topic_context = query_params.get("topic", "")
target_topic = links_context if links_context else topic_context

# 3. إعداد محرك الذكاء الاصطناعي
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key Missing!")
    st.stop()

# دالة اختيار الموديل (تم تبسيطها جداً لتجنب خطأ 404)
@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-1.5-flash')

# دالة حفظ الإجابات (تمنع خطأ 429)
@st.cache_data(ttl=3600)
def get_ai_response(prompt_text):
    model = get_model()
    response = model.generate_content(prompt_text)
    return response.text

# 4. واجهة التطبيق
st.title("🎓 Flexy Smart Assistant (EN)")

if not target_topic:
    st.warning("Waiting for lesson content from Moodle...")
else:
    if st.button("Start Lesson Now ✨"):
        with st.spinner("Flexy is thinking..."):
            prompt = f"Explain this lesson in simple English: {target_topic}. Format: Interactive Lesson. Level: Intermediate. Language: English. Please end with 3 True/False questions."
            try:
                # طلب الإجابة
                result = get_ai_response(prompt)
                st.session_state.lesson_en = result
                # توليد صوت
                tts = gTTS(text=result[:500], lang='en')
                tts.save("voice_en.mp3")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

# 5. عرض الدرس
if st.session_state.get('lesson_en'):
    res = st.session_state.lesson_en
    if os.path.exists("voice_en.mp3"): st.audio("voice_en.mp3")
    st.markdown(f'<div style="text-align:left; direction:ltr; padding:20px; background:#f9f9f9; border-radius:10px;">{res.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
