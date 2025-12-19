import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS
import urllib.request
import urllib.parse
import streamlit.components.v1 as components

# 1. إعدادات الهوية البصرية لـ Flexi Academy
st.set_page_config(page_title="Flexi AI Tutor", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    /* إخفاء القائمة التلقائية لحماية صفحة المعلم */
    [data-testid="stSidebarNav"] {display: none !important;}
    
    :root { --flexi-blue: #002e5b; }
    .main { background-color: #ffffff; }
    
    /* تنسيق القائمة الجانبية (Sidebar) */
    [data-testid="stSidebar"] { background-color: #002e5b !important; }
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMetric div,
    [data-testid="stSidebar"] .stRadio div,
    [data-testid="stSidebar"] .st-ae {
        color: white !important;
    }
    [data-testid="stMetricValue"] { color: white !important; font-weight: bold; }

    /* تنسيق منطقة عرض الدرس */
    .lesson-area { 
        direction: rtl; text-align: right; line-height: 1.8; 
        padding: 30px; border-right: 8px solid #002e5b; 
        background-color: #f8f9fa; border-radius: 10px; color: #333;
    }
    
    .stButton>button { 
        background-color: #002e5b !important; color: white !important; 
        border-radius: 10px !important; width: 100%; font-weight: bold;
    }
    
    @media print {
        .stButton, .stAudio, section[data-testid="stSidebar"], header, footer { display: none !important; }
        .main { width: 100% !important; padding: 0 !important; }
        .lesson-area { border: none !important; background: white !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. استلام البيانات من الرابط (Query Parameters)
query_params = st.query_params
links_context = query_params.get("links", "")  # استلام روابط الدرس
topic_context = query_params.get("topic", "")  # استلام اسم الدرس

# 3. القائمة الجانبية المخصصة
with st.sidebar:
    st.image("https://flexiacademy.com/assets/images/flexi-logo-2021.png", width=180)
    st.markdown("---")
    student_name = st.text_input("اسم الطالب:", value="طالب فلكسي")
    content_format = st.selectbox("شكل العرض:", ["درس تفاعلي", "قصة مصورة (Comic)", "سيناريو فيديو"])
    level = st.selectbox("المستوى:", ["مبتدئ", "متوسط", "متقدم"])
    learning_style = st.radio("نمط التعلم:", ["بصري (صور)", "سمعي (فيديو)", "حركي (أنشطة)"])
    language = st.selectbox("اللغة:", ["العربية", "English"])
    
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("🏆 نقاط التميز", st.session_state.score)
    
    st.divider()
    components.html("""
        <script>function printPage() { window.parent.print(); }</script>
        <button onclick="printPage()" style="width: 100%; background-color: white; color: #002e5b; padding: 10px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">🖨️ طباعة الدرس PDF</button>
    """, height=50)

# 4. محرك الذكاء الاصطناعي (تعديل لضمان اختيار الموديل المتاح)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("مفتاح API مفقود!")
    st.stop()

# دالة لاختيار الموديل المناسب تلقائياً لتجنب خطأ 404
@st.cache_resource
def get_available_model():
    try:
        # محاولة البحث عن الموديلات المتاحة في حسابك
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # نفضل فلاش إذا وجد، وإلا نأخذ أول موديل متاح
                if 'gemini-1.5-flash' in m.name:
                    return genai.GenerativeModel(m.name)
        # إذا لم يجد فلاش، يأخذ الموديل الافتراضي الأول
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(available_models[0])
    except Exception as e:
        # حل احتياطي أخير في حال فشل القائمة
        return genai.GenerativeModel('gemini-pro')

model = get_available_model()

# تحديد المحتوى المستهدف
target_topic = ""
if links_context:
    target_topic = f"شرح وتحليل المحتوى الموجود في هذه الروابط: {links_context}"
    st.info("🔗 تم استلام روابط الدرس بنجاح من المنصة.")
elif topic_context:
    target_topic = topic_context
    st.info(f"📚 الدرس المطلوب: {topic_context}")
else:
    target_topic = st.session_state.get('teacher_content', "")

st.title("🎓 مساعد Flexy الذكي")

if not target_topic:
    st.warning("بانتظار تحديد موضوع الدرس من منصة الموودل...")
else:
    if st.button("ابدأ شرح الدرس الآن ✨"):
        with st.spinner("ذكاء Flexy يحلل المحتوى ويعد لك درساً مخصصاً..."):
            prompt = f"""
            أنت معلم خبير في Flexi Academy. اشرح هذا المحتوى: {target_topic}.
            الهدف: الطالب يفضل النمط {learning_style} وبمستوى {level}.
            شكل المخرجات: {content_format}. اللغة: {language}.
            المتطلبات: 
            1. استخدم [[وصف صورة بالإنجليزية]] لوضع صور توضيحية.
            2. أضف 3 أسئلة صح وخطأ في النهاية: TF_START Q: | A: TF_END.
            """
            try:
                response = model.generate_content(prompt)
                st.session_state.lesson_data = response.text
                
                # توليد ملف الصوت
                clean_txt = re.sub(r'\[\[.*?\]\]|TF_START.*?TF_END|[^\w\s\u0600-\u06FF]', ' ', response.text, flags=re.DOTALL)
                tts = gTTS(text=clean_txt[:500], lang='ar' if language=="العربية" else 'en')
                tts.save("voice.mp3")
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ أثناء التوليد: {e}")

# 5. عرض النتائج (الجزء الجمالي)
if st.session_state.get('lesson_data'):
    res = st.session_state.lesson_data
    if os.path.exists("voice.mp3"): st.audio("voice.mp3")
    
    # عرض الصور
    imgs = re.findall(r'\[\[(.*?)\]\]', res)
    if imgs: st.image(f"https://pollinations.ai/p/{imgs[0].replace(' ', '%20')}?width=1000&height=400&model=flux")
    
    # عرض النص الرئيسي
    dir_css = "rtl" if language == "العربية" else "ltr"
    st.markdown(f'<div class="lesson-area" style="direction: {dir_css};">{res.split("TF_START")[0].replace("\n", "<br>")}</div>', unsafe_allow_html=True)
    
    # عرض الأسئلة التفاعلية
    if "TF_START" in res:
        st.divider()
        st.subheader("📝 اختبر فهمك")
        try:
            tf_part = re.search(r'TF_START(.*?)TF_END', res, re.DOTALL).group(1)
            for i, line in enumerate([l for l in tf_part.strip().split("\n") if "|" in l]):
                q, a = line.split("|")
                ans = st.radio(f"{q.replace('Q:', '').strip()}", ["صح ✅", "خطأ ❌"], key=f"q_{i}")
                if st.button(f"تأكيد الإجابة {i+1}", key=f"b_{i}"):
                    if (ans == "صح ✅" and "True" in a) or (ans == "خطأ ❌" and "False" in a):
                        st.success("إجابة صحيحة! استمر 🏆"); st.balloons(); st.session_state.score += 10
                    else: st.error("حاول مرة أخرى!")
        except: pass
