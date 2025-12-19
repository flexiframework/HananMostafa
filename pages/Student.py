import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS
import urllib.request
import urllib.parse

# 1. إعداد الصفحة وتصميم الواجهة
st.set_page_config(page_title="رحلة الطالب المبدع", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    .lesson-box { padding: 25px; border-radius: 15px; border-right: 10px solid #1a73e8; background-color: #f9f9f9; color: #2c3e50; direction: rtl; line-height: 1.8; text-align: right; }
    .comic-panel { border: 3px solid #000; padding: 15px; background: white; box-shadow: 5px 5px 0px #000; margin-bottom: 20px; direction: rtl; }
    @media print { .stButton, .stAudio, section[data-testid="stSidebar"], header { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

# 2. الربط مع جوجل (API)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("المفتاح مفقود في إعدادات التطبيق!")
    st.stop()

# 3. اختيار الموديل
@st.cache_resource
def load_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(models[0])
    except: return None

model = load_model()

# 4. واجهة الطالب (Sidebar)
with st.sidebar:
    st.header("🎓 إعداداتك يا بطل")
    student_name = st.text_input("اسمك:", value="طالب ذكي")
    age = st.number_input("عمرك:", 5, 20, 12)
    style = st.radio("كيف تحب عرض الدرس؟", ["درس تفاعلي", "قصة مصورة (Comic)"])
    st.divider()
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("🏆 رصيد نقاطك", st.session_state.score)
    st.markdown('<button onclick="window.print()" style="width:100%; padding:10px; background:#1a73e8; color:white; border:none; border-radius:5px; cursor:pointer;">📥 حفظ كـ PDF</button>', unsafe_allow_html=True)

# 5. التحقق من وجود محتوى من المعلم
teacher_topic = st.session_state.get('teacher_content', "")

st.title(f"مرحباً بك يا {student_name}! ✨")

if not teacher_topic:
    st.warning("👋 بانتظار المعلم ليقوم بوضع موضوع الدرس الجديد...")
    st.image("https://cdn-icons-png.flaticon.com/512/3406/3406830.png", width=100)
else:
    st.info(f"الموضوع الحالي: **{teacher_topic}**")
    
    if st.button("ابدأ الرحلة التعليمية الآن 🚀"):
        with st.spinner("جاري ابتكار عالمك الخاص..."):
            prompt = f"""
            الموضوع: {teacher_topic}. الطالب: {student_name} (عمره {age}).
            قم بشرح الموضوع بأسلوب ممتع.
            التنسيق المطلوب:
            1. إذا كان 'قصة مصورة': أنشئ 4 لوحات. لكل لوحة: PANEL X, CAPTION, DIALOGUE, VISUAL [English Description for image].
            2. إذا كان 'درس تفاعلي': استخدم عناوين وصور توضيحية بصيغة [[English Description for image]].
            3. أضف في النهاية سؤال MCQ بصيغة: Q:، Options: A) ، B) ، Correct: الحرف.
            اللغة: العربية.
            """
            try:
                response = model.generate_content(prompt)
                st.session_state.lesson_data = response.text
                
                # تحويل النص لصوت
                clean_text = re.sub(r'\[\[.*?\]\]|PANEL.*|VISUAL:.*|Q:.*', '', response.text)
                tts = gTTS(text=clean_text[:500], lang='ar')
                tts.save("voice.mp3")
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ: {e}")

    # 6. عرض محتوى الدرس
    if 'lesson_data' in st.session_state and st.session_state.lesson_data:
        lesson = st.session_state.lesson_data
        
        if os.path.exists("voice.mp3"):
            st.audio("voice.mp3")

        # حالة القصة المصورة
        if "PANEL" in lesson:
            panels = re.split(r'PANEL \d+:', lesson.split("Q:")[0])[1:]
            cols = st.columns(2)
            for i, p in enumerate(panels[:4]):
                with cols[i % 2]:
                    st.markdown('<div class="comic-panel">', unsafe_allow_html=True)
                    vis = re.search(r'VISUAL:(.*?)(?=\n|$)', p)
                    if vis:
                        img_q = vis.group(1).strip().replace(' ', '%20')
                        st.image(f"https://pollinations.ai/p/{img_q}?width=600&height=400&model=flux&seed={i}")
                    st.write(p.split("VISUAL:")[0].replace("CAPTION:", "🎬").replace("DIALOGUE:", "💬"))
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # حالة الدرس التفاعلي
        else:
            img_match = re.search(r'\[\[(.*?)\]\]', lesson)
            if img_match:
                img_q = img_match.group(1).replace(' ', '%20')
                st.image(f"https://pollinations.ai/p/{img_q}?width=1000&height=400&model=flux")
            
            clean_lesson = re.sub(r"\[\[.*?\]\]", "", lesson.split("Q:")[0]).replace("\n", "<br>")
            st.markdown(f'<div class="lesson-box">{clean_lesson}</div>', unsafe_allow_html=True)

        # 7. قسم الاختبار
        if "Q:" in lesson:
            st.divider()
            st.subheader("🧠 اختبر ذكاءك")
            try:
                q_text = lesson.split("Q:")[1].split("Options:")[0]
                correct_ans = re.search(r'Correct:\s*([A-B])', lesson).group(1)
                st.write(f"**سؤال:** {q_text}")
                choice = st.radio("اختر الإجابة:", ["A", "B"], key="quiz")
                if st.button("تحقق من إجابتي"):
                    if choice == correct_ans:
                        st.success("إجابة صحيحة! +10 نقاط 🏆")
                        st.session_state.score += 10
                        st.balloons()
                    else: st.error("إجابة خاطئة، حاول مرة أخرى!")
            except: st.write("أجب على السؤال الموجود في نهاية الدرس.")
