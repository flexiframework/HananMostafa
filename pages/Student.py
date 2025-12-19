import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS
import urllib.request
import urllib.parse
import streamlit.components.v1 as components

# 1. إعداد الصفحة والهوية البصرية لـ Flexi Academy
st.set_page_config(page_title="Flexi Student Portal", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    :root { --flexi-blue: #002e5b; }
    .main { background-color: #ffffff; }
    
    /* تنسيق القائمة الجانبية باللون الأزرق الداكن */
    [data-testid="stSidebar"] { background-color: #002e5b !important; }
    
    /* تلوين جميع النصوص في القائمة الجانبية باللون الأبيض */
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMetric div,
    [data-testid="stSidebar"] .stRadio div,
    [data-testid="stSidebar"] .st-ae {
        color: white !important;
    }
    
    /* ضمان ظهور نصوص خيارات الراديو (بصري/سمعي/حركي) بالأبيض */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: white !important; font-weight: bold; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: white !important; }

    /* تنسيق النقاط (Score) */
    [data-testid="stMetricValue"] { color: white !important; font-weight: bold; }

    /* تنسيق منطقة الدرس الرئيسي */
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
        .lesson-area { border: none !important; box-shadow: none !important; background: white !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. القائمة الجانبية (Sidebar) - الهوية الكاملة
with st.sidebar:
    st.image("https://flexiacademy.com/assets/images/flexi-logo-2021.png", width=180)
    st.markdown("---")
    
    student_name = st.text_input("اسم الطالب:", value="Flexian Student")
    
    st.markdown("### ⚙️ تخصيص الدرس")
    content_format = st.selectbox("شكل العرض:", ["درس تفاعلي", "قصة مصورة (Comic Style)", "سيناريو فيديو"])
    level = st.selectbox("المستوى الأكاديمي:", ["مبتدئ", "متوسط", "متقدم"])
    
    # خيارات نمط التعلم (ستظهر باللون الأبيض الآن)
    learning_style = st.radio("نمط التعلم الخاص بك:", 
                              ["بصري (صور مكثفة)", "سمعي (فيديو وصوت)", "حركي (تجارب ومشروعات)"])
    
    language = st.selectbox("لغة الدرس:", ["العربية", "English", "Français", "Deutsch"])
    
    st.divider()
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("🏆 نقاط التميز", st.session_state.score)
    
    st.divider()
    # زر الطباعة (مخفي عند الطباعة نفسها)
    print_btn_code = """
        <script>function printPage() { window.parent.print(); }</script>
        <button onclick="printPage()" style="width: 100%; background-color: white; color: #002e5b; padding: 10px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">🖨️ طباعة PDF</button>
    """
    components.html(print_btn_code, height=50)

# 3. محرك الذكاء الاصطناعي (Gemini)
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

# 4. معالجة وإنتاج الدرس
teacher_topic = st.session_state.get('teacher_content', "")
st.title("🎓 بوابة الطالب - Flexi Academy")

if not teacher_topic:
    st.warning("بانتظار المعلم لرفع مادة الدرس...")
else:
    st.success(f"📍 الموضوع المطلوب: {teacher_topic}")
    
    if st.button("توليد الدرس المخصص ✨"):
        with st.spinner("ذكاء Flexy يجهز محتواك..."):
            prompt = f"""
            أنت معلم في Flexi Academy. اشرح {teacher_topic}.
            النمط المفضل للطالب: {learning_style}. المستوى: {level}.
            الشكل: {content_format}. اللغة: {language}.
            
            ملاحظات:
            - للنمط البصري: أضف وصف صور [[Description]].
            - للسمعي: اقترح فيديوهات. للـ حركي: تجارب عملية.
            - أضف 3 أسئلة صح وخطأ في النهاية: TF_START Q: | A: TF_END.
            """
            try:
                response = flexi_ai.generate_content(prompt)
                st.session_state.lesson_data = response.text
                
                # توليد الصوت المنظف
                clean_txt = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', re.sub(r'\[\[.*?\]\]|TF_START.*?TF_END', '', response.text, flags=re.DOTALL))
                tts = gTTS(text=clean_txt[:500], lang={'العربية':'ar','English':'en','Français':'fr','Deutsch':'de'}[language])
                tts.save("voice.mp3")
                st.rerun()
            except Exception as e: st.error(f"خطأ: {e}")

    # 5. عرض المحتوى
    if st.session_state.get('lesson_data'):
        res = st.session_state.lesson_data
        if os.path.exists("voice.mp3"): st.audio("voice.mp3")

        # نمط سمعي (فيديو)
        if "سمعي" in learning_style:
            st.subheader("📺 فيديو تعليمي")
            q = urllib.parse.quote(f"{teacher_topic} {language} educational")
            html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={q}").read().decode()
            ids = re.findall(r"watch\?v=(\S{11})", html)
            if ids: st.video(f"https://www.youtube.com/watch?v={ids[0]}")

        # الصور
        imgs = re.findall(r'\[\[(.*?)\]\]', res)
        if imgs: st.image(f"https://pollinations.ai/p/{imgs[0].replace(' ', '%20')}?width=1000&height=400&model=flux")

        # النص (اتجاه اللغة)
        dir_css = "rtl" if language == "العربية" else "ltr"
        st.markdown(f'<div class="lesson-area" style="direction: {dir_css};">{res.split("TF_START")[0].replace("\n", "<br>")}</div>', unsafe_allow_html=True)

        # الأسئلة
        if "TF_START" in res:
            st.divider()
            st.subheader("✅ اختبار التحدي")
            try:
                tf_part = re.search(r'TF_START(.*?)TF_END', res, re.DOTALL).group(1)
                for i, line in enumerate([l for l in tf_part.strip().split("\n") if "|" in l]):
                    q_t, q_a = line.split("|")
                    ans = st.radio(f"{q_t.replace('Q:', '').strip()}", ["صح ✅", "خطأ ❌"], key=f"q_{i}")
                    if st.button(f"تأكيد {i+1}", key=f"b_{i}"):
                        if (ans == "صح ✅" and "True" in q_a) or (ans == "خطأ ❌" and "False" in q_a):
                            st.success("إجابة صحيحة! 🏆")
                            st.balloons()
                            st.session_state.score += 10
                        else: st.error("حاول مرة أخرى!")
            except: pass
