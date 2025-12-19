import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS
import urllib.request
import urllib.parse
import streamlit.components.v1 as components

# 1. إعداد الصفحة وإخفاء التنقل التلقائي بين الصفحات (لحماية صفحة المعلم)
st.set_page_config(page_title="Flexi Student Portal", layout="wide", page_icon="🎓")

# الكود السحري لإخفاء قائمة الصفحات الجانبية تماماً
st.markdown("""
    <style>
    /* إخفاء خيار التنقل بين الصفحات من القائمة الجانبية */
    [data-testid="stSidebarNav"] {display: none !important;}
    
    :root { --flexi-blue: #002e5b; }
    .main { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #002e5b !important; }
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMetric div,
    [data-testid="stSidebar"] .stRadio div,
    [data-testid="stSidebar"] .st-ae {
        color: white !important;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: white !important; font-weight: bold; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: white !important; }
    [data-testid="stMetricValue"] { color: white !important; font-weight: bold; }

    .lesson-area { 
        direction: rtl; text-align: right; line-height: 1.8; 
        padding: 30px; border-right: 8px solid #002e5b; 
        background-color: #f8f9fa; border-radius: 10px; color: #333;
    }
    
    .stButton>button { 
        background-color: #002e5b !important; color: white !important; 
        border-radius: 10px !important; width: 100%; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. القائمة الجانبية (مخصصة فقط للطالب)
with st.sidebar:
    st.image("https://flexiacademy.com/assets/images/flexi-logo-2021.png", width=180)
    st.markdown("<h3 style='text-align: center; color: white;'>بوابة الطالب الذكية</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    student_name = st.text_input("اسم الطالب:", value="Flexian Student")
    
    st.markdown("### ⚙️ إعدادات الدرس")
    content_format = st.selectbox("شكل العرض:", ["درس تفاعلي", "قصة مصورة (Comic Style)", "سيناريو فيديو"])
    level = st.selectbox("المستوى الأكاديمي:", ["مبتدئ", "متوسط", "متقدم"])
    learning_style = st.radio("نمط التعلم الخاص بك:", ["بصري (صور مكثفة)", "سمعي (فيديو وصوت)", "حركي (تجارب ومشروعات)"])
    language = st.selectbox("لغة الدرس:", ["العربية", "English", "Français", "Deutsch"])
    
    st.divider()
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("🏆 نقاط التميز", st.session_state.score)
    
    st.divider()
    print_btn_code = """
        <script>function printPage() { window.parent.print(); }</script>
        <button onclick="printPage()" style="width: 100%; background-color: white; color: #002e5b; padding: 10px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">🖨️ طباعة PDF</button>
    """
    components.html(print_btn_code, height=50)

# 3. محرك الذكاء الاصطناعي والربط
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("مفتاح API مفقود!")
    st.stop()

@st.cache_resource
def get_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(models[0])
    except: return None

flexi_ai = get_model()

# 4. عرض المحتوى (استرجاع ما وضعه المعلم في الخلفية)
teacher_topic = st.session_state.get('teacher_content', "")
st.title("🎓 Flexi Academy - AI Learning Path")

if not teacher_topic:
    st.info("👋 مرحباً بك! يرجى انتظار المعلم لتفعيل الدرس الخاص بك.")
else:
    st.success(f"📍 الدرس المتاح الآن: {teacher_topic}")
    
    if st.button("توليد محتوى الدرس ✨"):
        with st.spinner("ذكاء فلكسي يصمم لك تجربة فريدة..."):
            prompt = f"اشرح موضوع {teacher_topic} بأسلوب Flexi Academy. النمط: {learning_style}, المستوى: {level}, الشكل: {content_format}, اللغة: {language}. أضف [[Visual]] للصور و 3 أسئلة TF_START Q: | A: TF_END."
            try:
                response = flexi_ai.generate_content(prompt)
                st.session_state.lesson_data = response.text
                
                # توليد الصوت
                clean_txt = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', re.sub(r'\[\[.*?\]\]|TF_START.*?TF_END', '', response.text, flags=re.DOTALL))
                tts = gTTS(text=clean_txt[:500], lang={'العربية':'ar','English':'en','Français':'fr','Deutsch':'de'}[language])
                tts.save("voice.mp3")
                st.rerun()
            except Exception as e: st.error(f"خطأ: {e}")

    # 5. عرض النتائج
    if st.session_state.get('lesson_data'):
        res = st.session_state.lesson_data
        if os.path.exists("voice.mp3"): st.audio("voice.mp3")

        if "سمعي" in learning_style:
            st.subheader("📺 فيديو تعليمي")
            q = urllib.parse.quote(f"{teacher_topic} {language} educational")
            html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={q}").read().decode()
            ids = re.findall(r"watch\?v=(\S{11})", html)
            if ids: st.video(f"https://www.youtube.com/watch?v={ids[0]}")

        imgs = re.findall(r'\[\[(.*?)\]\]', res)
        if imgs: st.image(f"https://pollinations.ai/p/{imgs[0].replace(' ', '%20')}?width=1000&height=400&model=flux")

        dir_css = "rtl" if language == "العربية" else "ltr"
        st.markdown(f'<div class="lesson-area" style="direction: {dir_css};">{res.split("TF_START")[0].replace("\n", "<br>")}</div>', unsafe_allow_html=True)

        if "TF_START" in res:
            st.divider()
            st.subheader("✅ اختبار التميز")
            try:
                tf_part = re.search(r'TF_START(.*?)TF_END', res, re.DOTALL).group(1)
                for i, line in enumerate([l for l in tf_part.strip().split("\n") if "|" in l]):
                    q_t, q_a = line.split("|")
                    ans = st.radio(f"{q_t.replace('Q:', '').strip()}", ["صح ✅", "خطأ ❌"], key=f"q_{i}")
                    if st.button(f"تحقق {i+1}", key=f"b_{i}"):
                        if (ans == "صح ✅" and "True" in q_a) or (ans == "خطأ ❌" and "False" in q_a):
                            st.success("إجابة صحيحة! 🏆")
                            st.balloons(); st.session_state.score += 10
                        else: st.error("حاول مرة أخرى!")
            except: pass
