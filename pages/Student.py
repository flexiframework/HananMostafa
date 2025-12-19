import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS
import urllib.request
import urllib.parse

# 1. إعداد الصفحة
st.set_page_config(page_title="رحلة الطالب الذكية", layout="wide", page_icon="🎓")

# 2. الربط مع Gemini واختيار الموديل تلقائياً
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
    level = st.selectbox("المستوى:", ["مبتدئ", "متوسط", "متقدم"])
    age = st.slider("العمر:", 5, 20, 12)
    learning_style = st.radio("نمط التعلم:", ["بصري (صور)", "سمعي (فيديو)", "حركي (تجارب)"])
    language = st.selectbox("اللغة:", ["العربية", "English", "Français", "Deutsch"])
    
    st.divider()
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("🏆 نقاط التميز", st.session_state.score)
    if model_engine:
        st.caption(f"🤖 الموديل النشط: {model_engine.model_name.split('/')[-1]}")

# 4. معالجة النص للصوت (تنظيف علامات الترقيم والإيموجي)
def clean_text_for_speech(text):
    # إزالة الإيموجي والرموز الخاصة
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    # إزالة المسافات الزائدة
    text = " ".join(text.split())
    return text

# 5. استرجاع درس المعلم
teacher_topic = st.session_state.get('teacher_content', "")

st.title(f"مرحباً بك يا {student_name}! 🚀")

if not teacher_topic:
    st.warning("بانتظار المعلم لوضع موضوع الدرس...")
else:
    if st.button("توليد درسي الخاص الآن ✨"):
        with st.spinner("جاري ابتكار درسك المخصص..."):
            prompt = f"""
            أنت معلم خبير. اشرح موضوع: {teacher_topic}.
            1. اللغة: {language}. 2. العمر: {age}. 3. المستوى: {level}. 4. النمط: {learning_style}.
            
            التنسيق المطلوب:
            - الشرح: استخدم [[Visual Description]] للصور.
            - الأسئلة التفاعلية (صح وخطأ): أضف 3 أسئلة في النهاية تماماً بهذا الشكل:
              TF_START
              Q: [نص السؤال هنا] | A: [True أو False]
              Q: [نص السؤال هنا] | A: [True أو False]
              Q: [نص السؤال هنا] | A: [True أو False]
              TF_END
            """
            try:
                response = model_engine.generate_content(prompt)
                st.session_state.lesson_data = response.text
                
                # توليد الصوت المنظف
                lang_map = {'العربية': 'ar', 'English': 'en', 'Français': 'fr', 'Deutsch': 'de'}
                pure_text = re.sub(r'\[\[.*?\]\]|TF_START.*?TF_END', '', response.text, flags=re.DOTALL)
                final_audio_text = clean_text_for_speech(pure_text)
                
                tts = gTTS(text=final_audio_text[:500], lang=lang_map[language])
                tts.save("voice.mp3")
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ: {e}")

    # 6. عرض المحتوى والأسئلة
    if st.session_state.get('lesson_data'):
        content = st.session_state.lesson_data
        
        # تشغيل الصوت المنظم
        if os.path.exists("voice.mp3"): st.audio("voice.mp3")

        # عرض الصور والشرح
        main_lesson = content.split("TF_START")[0]
        img_match = re.search(r'\[\[(.*?)\]\]', main_lesson)
        if img_match:
            st.image(f"https://pollinations.ai/p/{img_match.group(1).replace(' ', '%20')}?width=1000&height=400&model=flux")
        
        direction = "rtl" if language == "العربية" else "ltr"
        st.markdown(f'<div style="direction: {direction}; text-align: justify; background: #f0f2f6; padding: 20px; border-radius: 10px;">{main_lesson.replace("\n", "<br>")}</div>', unsafe_allow_html=True)

        # 7. قسم أسئلة "صح وخطأ" التفاعلية
        if "TF_START" in content:
            st.divider()
            st.subheader("✅ اختبار التحدي (صح أم خطأ)")
            
            questions_block = re.search(r'TF_START(.*?)TF_END', content, re.DOTALL).group(1)
            q_lines = [line.strip() for line in questions_block.strip().split("\n") if "|" in line]
            
            for i, line in enumerate(q_lines):
                q_text, q_answer = line.split("|")
                q_text = q_text.replace("Q:", "").strip()
                ans_value = q_answer.replace("A:", "").strip() # True or False
                
                st.write(f"**{i+1}. {q_text}**")
                user_ans = st.radio(f"اختر إجابة السؤال {i+1}:", ["صح ✅", "خطأ ❌"], key=f"tf_{i}")
                
                if st.button(f"تحقق من السؤال {i+1}", key=f"btn_{i}"):
                    is_correct = (user_ans == "صح ✅" and ans_value == "True") or (user_ans == "خطأ ❌" and ans_value == "False")
                    if is_correct:
                        st.success("إجابة رائعة! استلم كأس التميز: 🏆")
                        st.session_state.score += 5
                        st.balloons()
                    else:
                        st.error("للأسف، إجابة غير صحيحة. حاول التركيز في القراءة!")
