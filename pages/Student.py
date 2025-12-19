import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS
import urllib.request
import urllib.parse

# 1. إعداد الصفحة مع دعم التنسيق للطباعة
st.set_page_config(page_title="رحلة الطالب الذكية", layout="wide", page_icon="🎓")

# تنسيق CSS خاص لإخفاء العناصر غير الضرورية عند الطباعة
st.markdown("""
    <style>
    @media print {
        .stButton, .stAudio, section[data-testid="stSidebar"], header, footer {
            display: none !important;
        }
        .main {
            width: 100% !important;
            padding: 0 !important;
        }
    }
    .print-btn {
        background-color: #1a73e8;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. الربط واختيار الموديل تلقائياً
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("المفتاح مفقود!")
    st.stop()

@st.cache_resource
def load_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(available_models[0]) if available_models else None
    except: return None

model_engine = load_model()

# 3. واجهة الطالب (Sidebar)
with st.sidebar:
    st.header("👤 ملف الطالب")
    student_name = st.text_input("الاسم:", value="طالب ذكي")
    
    # إضافة الخيار الجديد: شكل الدرس
    content_format = st.selectbox("شكل الدرس المشوق:", [
        "درس تفاعلي بالصور", 
        "قصة مصورة (Comic Style)", 
        "سيناريو فيديو قصير"
    ])
    
    level = st.selectbox("المستوى:", ["مبتدئ", "متوسط", "متقدم"])
    language = st.selectbox("اللغة:", ["العربية", "English", "Français", "Deutsch"])
    
    st.divider()
    # زر الطباعة في القائمة الجانبية
    st.markdown('<button onclick="window.print()" class="print-btn">🖨️ طباعة الدرس (PDF)</button>', unsafe_allow_html=True)
    
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("🏆 نقاط التميز", st.session_state.score)

# 4. وظيفة تنظيف النص للصوت
def clean_text_for_speech(text):
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    return " ".join(text.split())

# 5. استرجاع درس المعلم وتوليد المحتوى
teacher_topic = st.session_state.get('teacher_content', "")

st.title(f"مرحباً بك يا {student_name}! 🚀")

if not teacher_topic:
    st.warning("بانتظار المعلم لوضع موضوع الدرس...")
else:
    if st.button("توليد درسي المشوق الآن ✨"):
        with st.spinner("جاري ابتكار المحتوى بشكل ممتع..."):
            prompt = f"""
            أنت معلم مبدع وفنان قصصي. الموضوع: {teacher_topic}.
            الهدف: تحويل الدرس إلى '{content_format}'.
            المتطلبات:
            1. اللغة: {language}. 2. المستوى: {level}.
            3. إذا كان 'قصة مصورة': قسم المحتوى إلى (مشهد 1، مشهد 2...) مع وصف بصري لكل مشهد [[Visual Description]].
            4. إذا كان 'سيناريو فيديو': اكتبه كأسلوب (راوٍ، حوار، حركة كاميرا).
            5. الأسئلة التفاعلية (صح وخطأ): أضف 3 أسئلة في النهاية بصيغة:
              TF_START
              Q: [السؤال] | A: [True/False]
              TF_END
            """
            try:
                response = model_engine.generate_content(prompt)
                st.session_state.lesson_data = response.text
                
                # توليد الصوت المنظف
                lang_map = {'العربية': 'ar', 'English': 'en', 'Français': 'fr', 'Deutsch': 'de'}
                pure_text = re.sub(r'\[\[.*?\]\]|TF_START.*?TF_END', '', response.text, flags=re.DOTALL)
                tts = gTTS(text=clean_text_for_speech(pure_text[:500]), lang=lang_map[language])
                tts.save("voice.mp3")
                st.rerun()
            except Exception as e:
                st.error(f"خطأ: {e}")

    # 6. عرض المحتوى
    if st.session_state.get('lesson_data'):
        content = st.session_state.lesson_data
        
        # 🖨️ زر طباعة إضافي في أعلى الصفحة
        st.markdown('<div style="text-align: left;"><button onclick="window.print()" class="print-btn">🖨️ طباعة</button></div>', unsafe_allow_html=True)
        
        if os.path.exists("voice.mp3"): st.audio("voice.mp3")

        # معالجة الصور بناءً على النمط المختلق
        main_lesson = content.split("TF_START")[0]
        
        # إذا كانت قصة مصورة، سنحاول عرض أكثر من صورة
        images = re.findall(r'\[\[(.*?)\]\]', main_lesson)
        if images:
            if "قصة مصورة" in content_format:
                cols = st.columns(len(images[:3])) # عرض أول 3 مشاهد في أعمدة
                for idx, img_desc in enumerate(images[:3]):
                    with cols[idx]:
                        st.image(f"https://pollinations.ai/p/{img_desc.replace(' ', '%20')}?width=400&height=400&model=flux", caption=f"مشهد {idx+1}")
            else:
                st.image(f"https://pollinations.ai/p/{images[0].replace(' ', '%20')}?width=1000&height=400&model=flux")

        # عرض النص التنسيقي
        direction = "rtl" if language == "العربية" else "ltr"
        st.markdown(f'<div class="lesson-area" style="direction: {direction}; background: white; padding: 30px; border: 2px solid #e0e0e0; border-radius: 15px;">{main_lesson.replace("\n", "<br>")}</div>', unsafe_allow_html=True)

        # 7. قسم الأسئلة
        if "TF_START" in content:
            st.divider()
            st.subheader("✅ تحدي الفهم (صح أم خطأ)")
            try:
                questions_block = re.search(r'TF_START(.*?)TF_END', content, re.DOTALL).group(1)
                for i, line in enumerate([l for l in questions_block.strip().split("\n") if "|" in l]):
                    q_text, q_ans = line.split("|")
                    user_ans = st.radio(f"{q_text.strip()}", ["صح ✅", "خطأ ❌"], key=f"tf_{i}")
                    if st.button(f"تأكيد إجابة {i+1}", key=f"btn_{i}"):
                        is_correct = (user_ans == "صح ✅" and "True" in q_ans) or (user_ans == "خطأ ❌" and "False" in q_ans)
                        if is_correct:
                            st.success("عبقري! إجابة صحيحة 🏆")
                            st.balloons()
                            st.session_state.score += 5
                        else: st.error("حاول مرة أخرى يا بطل!")
            except: pass
