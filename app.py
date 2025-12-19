import streamlit as st
import google.generativeai as genai
import re
from gtts import gTTS
import urllib.request
import urllib.parse
import os

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="Flexy AI Smart Tutor", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    .lesson-box { padding: 25px; border-radius: 15px; border-right: 10px solid #1a73e8; background-color: #f9f9f9; color: #2c3e50; direction: rtl; line-height: 1.8; text-align: right; }
    .comic-panel { border: 3px solid #000; padding: 15px; background: white; box-shadow: 5px 5px 0px #000; margin-bottom: 20px; direction: rtl; }
    .quiz-container { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e0e0e0; margin-top: 20px; direction: rtl; text-align: right; }
    @media print { .stButton, .stAudio, section[data-testid="stSidebar"], header { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الحالة (State) ---
if 'score' not in st.session_state: st.session_state.score = 0
if 'lesson_data' not in st.session_state: st.session_state.lesson_data = None
if 'teacher_content' not in st.session_state: st.session_state.teacher_content = ""

# --- 3. الربط مع API واختيار الموديل ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("المفتاح مفقود في Secrets!")
    st.stop()

@st.cache_resource
def load_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(models[0]), models[0]
    except: return None, None

model, model_name = load_model()

# --- 4. القائمة الجانبية (إعدادات الطالب + قفل المعلم) ---
with st.sidebar:
    st.title("🎓 رحلة الطالب")
    student_name = st.text_input("اسمك البطل:", value="طالب ذكي")
    age = st.number_input("عمرك:", 5, 20, 12)
    output_format = st.radio("شكل الدرس:", ["درس ممتع بالصور", "قصة مصورة (Comic)"])
    st.divider()
    st.metric("🏆 نقاطك", st.session_state.score)
    st.markdown('<button onclick="window.print()" style="width:100%; padding:10px; background:#1a73e8; color:white; border:none; border-radius:5px; cursor:pointer;">📥 حفظ الدرس PDF</button>', unsafe_allow_html=True)
    
    st.divider()
    # نظام قفل المعلم
    show_teacher_ui = False
    is_teacher = st.checkbox("🔑 دخول المعلم")
    if is_teacher:
        pwd = st.text_input("كلمة المرور:", type="password")
        if pwd == "1234": # يمكنك تغيير الرقم السرّي هنا
            show_teacher_ui = True
        else:
            st.warning("كلمة المرور خاطئة")

# --- 5. منطقة المعلم (تظهر فقط عند فتح القفل) ---
if show_teacher_ui:
    st.header("👨‍🏫 لوحة تحكم المعلم")
    st.session_state.teacher_content = st.text_area(
        "اكتب محتوى الدرس أو الموضوع هنا:",
        value=st.session_state.teacher_content,
        placeholder="مثال: شرح مبسط عن البراكين أو قصة عن الصدق...",
        height=150
    )
    st.info("💡 بعد كتابة المحتوى، قم بإلغاء 'دخول المعلم' من الجانب لبدء رحلة الطالب.")
    st.divider()

# --- 6. منطقة الطالب (العرض والنتائج) ---
if not st.session_state.teacher_content:
    st.info("👋 أهلاً بك! بانتظار المعلم ليقوم بوضع موضوع الدرس...")
else:
    st.title(f"مرحباً {student_name}! 🚀")
    st.write(f"الموضوع الحالي: **{st.session_state.teacher_content}**")
    
    if st.button("ابدأ الرحلة التعليمية ✨"):
        with st.spinner("جاري تحويل الدرس إلى عالم من الخيال..."):
            prompt = f"""
            أنت معلم مبدع. المحتوى: {st.session_state.teacher_content}. الطالب: {student_name}، العمر: {age}.
            1. إذا كان 'قصة مصورة': 4 لوحات. لكل لوحة PANEL, CAPTION, DIALOGUE, VISUAL [English Description].
            2. إذا كان 'درس ممتع': نص مشوق مع [[English Description]] للصور.
            3. سؤال اختيار من متعدد في النهاية: Q:، Options: A) ، B) ، Correct: الحرف.
            اللغة: العربية.
            """
            response = model.generate_content(prompt)
            st.session_state.lesson_data = response.text
            
            try:
                clean_text = re.sub(r'\[\[.*?\]\]|PANEL.*|VISUAL:.*|Q:.*', '', response.text)
                tts = gTTS(text=clean_text[:500], lang='ar')
                tts.save("voice.mp3")
            except: pass
            st.rerun()

    # عرض النتائج
    if st.session_state.lesson_data:
        content = st.session_state.lesson_data
        if os.path.exists("voice.mp3"): st.audio("voice.mp3")

        if "PANEL" in content:
            panels = re.split(r'PANEL \d+:', content.split("Q:")[0])[1:]
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
        else:
            img_match = re.search(r'\[\[(.*?)\]\]', content)
            if img_match:
                img_q = img_match.group(1).replace(' ', '%20')
                st.image(f"https://pollinations.ai/p/{img_q}?width=1000&height=400&model=flux")
            
            clean_lesson = re.sub(r"\[\[.*?\]\]", "", content.split("Q:")[0]).replace("\n", "<br>")
            st.markdown(f'<div class="lesson-box">{clean_lesson}</div>', unsafe_allow_html=True)

        # الاختبار
        if "Q:" in content:
            st.divider()
            st.subheader("🧠 اختبار ذكاء سريع")
            try:
                q_part = content.split("Q:")[1]
                correct_ans = re.search(r'Correct:\s*([A-B])', content).group(1)
                st.write(q_part.split("Options:")[0])
                choice = st.radio("اختر الإجابة:", ["A", "B"], key="q1")
                if st.button("تحقق"):
                    if choice == correct_ans:
                        st.success("أحسنت يا بطل! +10 نقاط 🏆")
                        st.session_state.score += 10
                        st.balloons()
                    else: st.error("حاول مرة أخرى!")
            except: pass
