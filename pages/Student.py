import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS
import urllib.request
import urllib.parse

# 1. إعداد الصفحة (يجب أن يكون أول أمر متعلق بـ streamlit)
st.set_page_config(page_title="رحلة الطالب الذكية", layout="wide", page_icon="🎓")

# 2. الربط مع Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("المفتاح مفقود!")
    st.stop()

# 3. اختيار الموديل الذكي (لتجنب خطأ 404)
@st.cache_resource
def load_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not available_models: return None
        # نختار الموديل المتاح (مثل gemini-1.5-flash أو gemini-pro)
        return genai.GenerativeModel(available_models[0])
    except: return None

model_engine = load_model()

# 4. واجهة الطالب (Sidebar)
with st.sidebar:
    st.header("👤 ملف الطالب الشخصي")
    student_name = st.text_input("اسم الطالب:", value="طالب ذكي")
    level = st.selectbox("المستوى الأكاديمي:", ["مبتدئ", "متوسط", "متقدم"])
    age = st.slider("عمر الطالب:", 5, 20, 12)
    learning_style = st.radio("نمط التعلم المفضل:", ["بصري (صور)", "سمعي (فيديو وصوت)", "حركي (تجارب)"])
    language = st.selectbox("لغة المحتوى:", ["العربية", "English", "Français", "Deutsch"])
    
    st.divider()
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("🏆 نقاط التميز", st.session_state.score)

# 5. استرجاع درس المعلم
teacher_topic = st.session_state.get('teacher_content', "")

st.title(f"مرحباً بك يا {student_name}! 🚀")

if not teacher_topic:
    st.warning("بانتظار المعلم لوضع مادة الدرس...")
else:
    st.info(f"📍 الموضوع المطلوب: **{teacher_topic}**")
    
    if st.button("توليد درسي الخاص الآن ✨"):
        if model_engine is None:
            st.error("فشل الاتصال بموديلات الذكاء الاصطناعي.")
        else:
            with st.spinner("ذكاء Flexy يحلل طلبك..."):
                prompt = f"""
                أنت معلم خبير. اشرح موضوع: {teacher_topic}.
                المتطلبات:
                1. اللغة: {language}.
                2. العمر: {age} سنة.
                3. المستوى: {level}.
                4. نمط التعلم: {learning_style}.
                   - إذا كان بصرياً: استخدم وصفاً صورياً [[Visual Description]].
                   - إذا كان سمعياً: ركز على الشرح الصوتي واقترح مصادر تعليمية فيديو.
                   - إذا كان حركياً: أضف قسم 'تجارب ومشروعات منزلية'.
                5. التنسيق: عناوين واضحة وسؤال MCQ في النهاية بصيغة Q:, Options:, Correct:.
                """
                try:
                    response = model_engine.generate_content(prompt)
                    st.session_state.lesson_data = response.text
                    
                    # توليد الصوت بناءً على اللغة
                    lang_map = {'العربية': 'ar', 'English': 'en', 'Français': 'fr', 'Deutsch': 'de'}
                    clean_text = re.sub(r'\[\[.*?\]\]|Q:.*', '', response.text)
                    tts = gTTS(text=clean_text[:500], lang=lang_map[language])
                    tts.save("voice.mp3")
                    st.rerun()
                except Exception as e:
                    st.error(f"حدث خطأ: {e}")

    # 6. عرض المخرجات
    if st.session_state.get('lesson_data'):
        content = st.session_state.lesson_data
        if os.path.exists("voice.mp3"): st.audio("voice.mp3")

        # عرض الصور
        img_match = re.search(r'\[\[(.*?)\]\]', content)
        if img_match:
            img_q = img_match.group(1).replace(' ', '%20')
            st.image(f"https://pollinations.ai/p/{img_q}?width=1000&height=400&model=flux")

        # عرض النص
        direction = "rtl" if language == "العربية" else "ltr"
        st.markdown(f'<div style="direction: {direction}; text-align: justify; background: #f0f2f6; padding: 20px; border-radius: 10px;">{content.split("Q:")[0].replace("\n", "<br>")}</div>', unsafe_allow_html=True)

        # إضافة يوتيوب إذا كان النمط سمعياً
        if "سمعي" in learning_style:
            st.subheader("📺 فيديو تعليمي مقترح")
            try:
                search_q = urllib.parse.quote(f"{teacher_topic} {language} educational")
                url = f"https://www.youtube.com/results?search_query={search_q}"
                html = urllib.request.urlopen(url).read().decode()
                video_ids = re.findall(r"watch\?v=(\S{11})", html)
                if video_ids: st.video(f"https://www.youtube.com/watch?v={video_ids[0]}")
            except: pass
