import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS
import urllib.request
import urllib.parse
import streamlit.components.v1 as components

# 1. إعداد الصفحة وتنسيق الطباعة (CSS)
st.set_page_config(page_title="رحلة الطالب الذكية", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    /* تنسيق المحتوى ليكون جميلاً */
    .lesson-area { direction: rtl; text-align: right; line-height: 1.8; }
    
    /* إخفاء العناصر غير الضرورية عند الطباعة */
    @media print {
        .stButton, .stAudio, section[data-testid="stSidebar"], header, footer, .stRadio, .print-ignore {
            display: none !important;
        }
        .main { width: 100% !important; padding: 0 !important; }
        .lesson-area { border: none !important; background: white !important; color: black !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. تهيئة الموديل بشكل ديناميكي (تجنب خطأ 404)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("المفتاح مفقود في إعدادات Secrets!")
    st.stop()

@st.cache_resource
def load_dynamic_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(models[0]) if models else None
    except: return None

model_engine = load_dynamic_model()

# 3. واجهة الطالب الإحترافية (القائمة الجانبية)
with st.sidebar:
    st.header("👤 ملف الطالب الشخصي")
    student_name = st.text_input("اسم الطالب:", value="طالب ذكي")
    
    st.subheader("⚙️ إعدادات الدرس")
    content_format = st.selectbox("شكل الدرس:", ["درس تفاعلي", "قصة مصورة (Comic Style)", "سيناريو فيديو قصير"])
    level = st.selectbox("المستوى الأكاديمي:", ["مبتدئ", "متوسط", "متقدم"])
    age = st.slider("عمر الطالب:", 5, 20, 12)
    learning_style = st.radio("نمط التعلم:", ["بصري (صور)", "سمعي (فيديو وصوت)", "حركي (تجارب ومشروعات)"])
    language = st.selectbox("لغة المحتوى:", ["العربية", "English", "Français", "Deutsch"])
    
    st.divider()
    # زر الطباعة المطور (JavaScript)
    st.markdown("### 🖨️ أدوات الحفظ")
    print_btn_html = """
        <script>function printPage() { window.parent.print(); }</script>
        <button onclick="printPage()" style="width: 100%; background-color: #1a73e8; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">🖨️ حفظ كـ PDF / طباعة</button>
    """
    components.html(print_btn_html, height=50)
    
    st.divider()
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("🏆 نقاط التميز", st.session_state.score)
    if model_engine: st.caption(f"🤖 الموديل النشط: {model_engine.model_name.split('/')[-1]}")

# 4. وظيفة تنظيف النص للصوت (بدون رموز أو إيموجي)
def clean_for_audio(text):
    # إزالة الإيموجي والرموز وعلامات الترقيم لقراءة واضحة
    clean = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    return " ".join(clean.split())

# 5. استرجاع درس المعلم والإنتاج
teacher_topic = st.session_state.get('teacher_content', "")

st.title(f"مرحباً بك يا {student_name}! 🚀")

if not teacher_topic:
    st.warning("👋 بانتظار المعلم ليقوم بتحديد موضوع الدرس من صفحة Teacher.")
else:
    st.info(f"📌 الموضوع الحالي: **{teacher_topic}**")
    
    if st.button("توليد درسي المخصص الآن ✨"):
        with st.spinner("جاري ابتكار محتواك المخصص..."):
            prompt = f"""
            أنت معلم مبدع. اشرح موضوع: {teacher_topic}.
            الهدف: تحويل الدرس إلى '{content_format}'.
            المتطلبات:
            1. اللغة: {language}. 2. العمر: {age}. 3. المستوى: {level}. 4. النمط: {learning_style}.
            5. التنسيق: 
               - استخدم [[English Description]] لوصف الصور.
               - أضف 3 أسئلة صح وخطأ في النهاية تماماً بهذا الشكل:
                 TF_START
                 Q: [السؤال] | A: [True أو False]
                 TF_END
            """
            try:
                response = model_engine.generate_content(prompt)
                st.session_state.lesson_data = response.text
                
                # توليد الصوت المنظف
                lang_codes = {'العربية': 'ar', 'English': 'en', 'Français': 'fr', 'Deutsch': 'de'}
                pure_text = re.sub(r'\[\[.*?\]\]|TF_START.*?TF_END', '', response.text, flags=re.DOTALL)
                tts_text = clean_for_audio(pure_text[:500])
                tts = gTTS(text=tts_text, lang=lang_codes[language])
                tts.save("voice.mp3")
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ: {e}")

    # 6. عرض المحتوى الناتج
    if st.session_state.get('lesson_data'):
        content = st.session_state.lesson_data
        
        # عرض مشغل الصوت
        if os.path.exists("voice.mp3"): st.audio("voice.mp3")

        # معالجة الصور
        main_lesson = content.split("TF_START")[0]
        images = re.findall(r'\[\[(.*?)\]\]', main_lesson)
        if images:
            if "قصة مصورة" in content_format:
                cols = st.columns(len(images[:3]))
                for i, img_desc in enumerate(images[:3]):
                    with cols[i]: st.image(f"https://pollinations.ai/p/{img_desc.replace(' ', '%20')}?width=400&height=400&model=flux", caption=f"مشهد {i+1}")
            else:
                st.image(f"https://pollinations.ai/p/{images[0].replace(' ', '%20')}?width=1000&height=400&model=flux")

        # عرض نص الدرس
        dir_css = "rtl" if language == "العربية" else "ltr"
        st.markdown(f'<div class="lesson-area" style="direction: {dir_css}; background: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #ddd;">{main_lesson.replace("\n", "<br>")}</div>', unsafe_allow_html=True)

        # 7. قسم فيديوهات يوتيوب (للمتعلم السمعي)
        if "سمعي" in learning_style:
            st.divider()
            st.subheader("📺 فيديو مقترح من YouTube")
            search_query = urllib.parse.quote(f"{teacher_topic} {language} educational")
            html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={search_query}").read().decode()
            v_ids = re.findall(r"watch\?v=(\S{11})", html)
            if v_ids: st.video(f"https://www.youtube.com/watch?v={v_ids[0]}")

        # 8. قسم أسئلة صح وخطأ التفاعلية
        if "TF_START" in content:
            st.divider()
            st.subheader("✅ اختبار ذكاء سريع (صح أم خطأ)")
            try:
                tf_block = re.search(r'TF_START(.*?)TF_END', content, re.DOTALL).group(1)
                for i, line in enumerate([l for l in tf_block.strip().split("\n") if "|" in l]):
                    q_text, q_ans = line.split("|")
                    st.write(f"**س{i+1}: {q_text.replace('Q:', '').strip()}**")
                    user_choice = st.radio("إجابتك:", ["صح ✅", "خطأ ❌"], key=f"user_q_{i}")
                    
                    if st.button(f"تحقق من إجابة {i+1}", key=f"check_{i}"):
                        is_correct = (user_choice == "صح ✅" and "True" in q_ans) or (user_choice == "خطأ ❌" and "False" in q_ans)
                        if is_correct:
                            st.success("إجابة صحيحة! استحققت الكأس 🏆")
                            st.balloons()
                            st.session_state.score += 5
                        else:
                            st.error("إجابة خاطئة، ركز جيداً في المرة القادمة!")
            except: pass
