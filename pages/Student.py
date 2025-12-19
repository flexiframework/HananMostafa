import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS
import urllib.request
import urllib.parse
import streamlit.components.v1 as components

# 1. إعداد الهوية البصرية لـ Flexi Academy
st.set_page_config(page_title="Flexi Student Portal", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    /* ألوان Flexi Academy الأساسية */
    :root { --flexi-blue: #002e5b; --flexi-light-blue: #0056b3; }
    .main { background-color: #ffffff; }
    .stSidebar { background-color: #002e5b !important; color: white !important; }
    .stSidebar [data-testid="stMarkdownContainer"] p { color: white !important; font-weight: bold; }
    
    /* تنسيق صندوق الدرس */
    .lesson-area { 
        direction: rtl; text-align: right; line-height: 1.8; 
        padding: 30px; border-left: 8px solid #002e5b; 
        background-color: #f8f9fa; border-radius: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* أزرار مخصصة */
    .stButton>button { 
        background-color: #002e5b !important; color: white !important; 
        border-radius: 20px !important; padding: 10px 25px !important;
    }
    
    @media print {
        .stButton, .stAudio, section[data-testid="stSidebar"], header, footer, .print-ignore { display: none !important; }
        .main { width: 100% !important; padding: 0 !important; }
        .lesson-area { border: none !important; box-shadow: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. الشعار والبيانات في القائمة الجانبية (بدون أي روابط للمعلم)
with st.sidebar:
    st.image("https://flexiacademy.com/assets/images/flexi-logo-2021.png", width=180)
    st.markdown("---")
    st.markdown("### 👤 ملف الطالب")
    student_name = st.text_input("اسم الطالب:", value="Flexian Student")
    content_format = st.selectbox("نمط العرض:", ["درس تفاعلي", "قصة مصورة (Comic)", "سيناريو فيديو"])
    level = st.selectbox("المستوى الأكاديمي:", ["مبتدئ", "متوسط", "متقدم"])
    language = st.selectbox("اللغة:", ["العربية", "English", "Français", "Deutsch"])
    
    st.divider()
    # زر الطباعة المطور
    print_btn = """
        <script>function printPage() { window.parent.print(); }</script>
        <button onclick="printPage()" style="width: 100%; background-color: #ffffff; color: #002e5b; padding: 10px; border: 2px solid #ffffff; border-radius: 10px; cursor: pointer; font-weight: bold;">🖨️ طباعة الدرس PDF</button>
    """
    components.html(print_btn, height=50)
    
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("🏆 نقاطك", st.session_state.score)

# 3. تهيئة الذكاء الاصطناعي
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("مفتاح API غير متوفر!")
    st.stop()

@st.cache_resource
def get_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(models[0])
    except: return None

model = get_model()

# 4. عرض المحتوى
teacher_topic = st.session_state.get('teacher_content', "")

st.markdown(f"## مرحباً بك في بوابة Flexi Academy ✨")

if not teacher_topic:
    st.warning("بانتظار المعلم لرفع المادة العلمية... يرجى تحديث الصفحة لاحقاً.")
else:
    st.success(f"📍 الدرس الحالي: {teacher_topic}")
    
    if st.button("توليد المحتوى التعليمي 🚀"):
        with st.spinner("جاري التجهيز بناءً على هوية Flexi Academy..."):
            prompt = f"أنت معلم في Flexi Academy. اشرح {teacher_topic} لـ {student_name}. اللغة: {language}. المستوى: {level}. النمط: {content_format}. أضف [[Visual]] للصور و 3 أسئلة TF_START Q: | A: TF_END في النهاية."
            try:
                response = model.generate_content(prompt)
                st.session_state.lesson_data = response.text
                
                # توليد الصوت
                clean_txt = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', re.sub(r'\[\[.*?\]\]|TF_START.*?TF_END', '', response.text, flags=re.DOTALL))
                tts = gTTS(text=clean_txt[:500], lang={'العربية': 'ar', 'English': 'en', 'Français': 'fr', 'Deutsch': 'de'}[language])
                tts.save("voice.mp3")
                st.rerun()
            except Exception as e: st.error(f"خطأ: {e}")

    if st.session_state.get('lesson_data'):
        data = st.session_state.lesson_data
        if os.path.exists("voice.mp3"): st.audio("voice.mp3")
        
        # الصور
        imgs = re.findall(r'\[\[(.*?)\]\]', data)
        if imgs: st.image(f"https://pollinations.ai/p/{imgs[0].replace(' ', '%20')}?width=1000&height=400&model=flux")
        
        # النص
        st.markdown(f'<div class="lesson-area">{data.split("TF_START")[0].replace("\n", "<br>")}</div>', unsafe_allow_html=True)
        
        # الأسئلة
        if "TF_START" in data:
            st.divider()
            st.subheader("🏆 اختبار التميز من Flexi")
            try:
                tf_block = re.search(r'TF_START(.*?)TF_END', data, re.DOTALL).group(1)
                for i, line in enumerate([l for l in tf_block.strip().split("\n") if "|" in l]):
                    q, a = line.split("|")
                    ans = st.radio(f"{q.replace('Q:', '').strip()}", ["صح ✅", "خطأ ❌"], key=f"q_{i}")
                    if st.button(f"تحقق {i+1}", key=f"b_{i}"):
                        if (ans == "صح ✅" and "True" in a) or (ans == "خطأ ❌" and "False" in a):
                            st.success("إجابة صحيحة! 🏆")
                            st.balloons()
                            st.session_state.score += 10
                        else: st.error("حاول مجدداً!")
            except: pass
