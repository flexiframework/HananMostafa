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
    :root { --flexi-blue: #002e5b; }
    .main { background-color: #ffffff; }
    
    /* تنسيق القائمة الجانبية باللون الأزرق الداكن والنصوص البيضاء */
    [data-testid="stSidebar"] { background-color: #002e5b !important; }
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMetric div,
    [data-testid="stSidebar"] .stRadio label {
        color: white !important;
    }
    [data-testid="stMetricValue"] { color: white !important; font-weight: bold; }

    /* تنسيق منطقة الدرس */
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

# 2. القائمة الجانبية (Sidebar) مع إعادة إضافة الأنماط
with st.sidebar:
    st.image("https://flexiacademy.com/assets/images/flexi-logo-2021.png", width=180)
    st.markdown("---")
    
    student_name = st.text_input("اسم الطالب:", value="Flexian Student")
    
    st.markdown("### ⚙️ تخصيص محتوى الدرس")
    content_format = st.selectbox("شكل العرض:", ["درس تفاعلي", "قصة مصورة (Comic Style)", "سيناريو فيديو"])
    level = st.selectbox("المستوى الأكاديمي:", ["مبتدئ", "متوسط", "متقدم"])
    
    # إرجاع الجزء الخاص بأنماط التعلم
    learning_style = st.radio("نمط التعلم الخاص بك:", ["بصري (صور مكثفة)", "سمعي (فيديو وصوت)", "حركي (تجارب ومشروعات)"])
    
    language = st.selectbox("لغة الدرس:", ["العربية", "English", "Français", "Deutsch"])
    
    st.divider()
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("🏆 نقاط التميز", st.session_state.score)
    
    st.divider()
    print_btn = """
        <script>function printPage() { window.parent.print(); }</script>
        <button onclick="printPage()" style="width: 100%; background-color: white; color: #002e5b; padding: 10px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">🖨️ طباعة PDF</button>
    """
    components.html(print_btn, height=50)

# 3. إعدادات الذكاء الاصطناعي
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("مفتاح API مفقود!")
    st.stop()

@st.cache_resource
def get_flexi_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(models[0])
    except: return None

flexi_ai = get_flexi_model()

# 4. معالجة الدرس
teacher_topic = st.session_state.get('teacher_content', "")
st.title("🎓 بوابة الطالب - Flexi Academy")

if not teacher_topic:
    st.warning("بانتظار المعلم لرفع مادة الدرس...")
else:
    st.success(f"📍 الموضوع المطلوب: {teacher_topic}")
    
    if st.button("توليد الدرس المخصص ✨"):
        with st.spinner("ذكاء Flexy يحلل نمط تعلمك المفضل..."):
            prompt = f"""
            أنت معلم خبير في Flexi Academy. اشرح موضوع: {teacher_topic}.
            الهدف: الطالب يفضل النمط {learning_style} وبمستوى {level}.
            شكل المخرجات: {content_format}. اللغة: {language}.
            
            المتطلبات الإضافية:
            - إذا كان النمط بصرياً: استخدم أوصافاً صورية دقيقة [[Description]].
            - إذا كان سمعياً: ركز على الشرح السلس واقترح مصادر فيديو.
            - إذا كان حركياً: أضف أنشطة عملية وتجارب منزلية.
            - أضف 3 أسئلة صح وخطأ في النهاية: TF_START Q: | A: TF_END.
            """
            try:
                response = flexi_ai.generate_content(prompt)
                st.session_state.lesson_data = response.text
                
                # توليد الصوت (تنظيف النص من الرموز)
                lang_map = {'العربية': 'ar', 'English': 'en', 'Français': 'fr', 'Deutsch': 'de'}
                clean_txt = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', re.sub(r'\[\[.*?\]\]|TF_START.*?TF_END', '', response.text, flags=re.DOTALL))
                tts = gTTS(text=clean_txt[:500], lang=lang_map[language])
                tts.save("voice.mp3")
                st.rerun()
            except Exception as e: st.error(f"خطأ: {e}")

    # 5. عرض النتائج
    if st.session_state.get('lesson_data'):
        res = st.session_state.lesson_data
        if os.path.exists("voice.mp3"): st.audio("voice.mp3")

        # معالجة الصور والفيديو حسب النمط
        if "سمعي" in learning_style:
            st.subheader("📺 فيديو تعليمي مقترح")
            q = urllib.parse.quote(f"{teacher_topic} {language} educational")
            html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={q}").read().decode()
            ids = re.findall(r"watch\?v=(\S{11})", html)
            if ids: st.video(f"https://www.youtube.com/watch?v={ids[0]}")

        imgs = re.findall(r'\[\[(.*?)\]\]', res)
        if imgs: st.image(f"https://pollinations.ai/p/{imgs[0].replace(' ', '%20')}?width=1000&height=400&model=flux")

        # عرض النص
        dir_ltr = "ltr" if language != "العربية" else "rtl"
        st.markdown(f'<div class="lesson-area" style="direction: {dir_ltr};">{res.split("TF_START")[0].replace("\n", "<br>")}</div>', unsafe_allow_html=True)

        # الأسئلة التفاعلية
        if "TF_START" in res:
            st.divider()
            st.subheader("🏆 اختبار التميز (صح أم خطأ)")
            try:
                tf_part = re.search(r'TF_START(.*?)TF_END', res, re.DOTALL).group(1)
                for i, line in enumerate([l for l in tf_part.strip().split("\n") if "|" in l]):
                    q_t, q_a = line.split("|")
                    u_a = st.radio(f"{q_t.replace('Q:', '').strip()}", ["صح ✅", "خطأ ❌"], key=f"q_f_{i}")
                    if st.button(f"تأكيد {i+1}", key=f"bt_f_{i}"):
                        if (u_a == "صح ✅" and "True" in q_a) or (u_a == "خطأ ❌" and "False" in q_a):
                            st.success("إجابة صحيحة! 🏆")
                            st.balloons()
                            st.session_state.score += 10
                        else: st.error("إجابة غير صحيحة، حاول مجدداً!")
            except: pass
