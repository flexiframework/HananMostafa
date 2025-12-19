import streamlit as st
import google.generativeai as genai
import re
from gtts import gTTS
import urllib.request
import urllib.parse
import os

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="Flexy AI Tutor", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    .lesson-box { padding: 25px; border-radius: 15px; border-left: 10px solid #1a73e8; background-color: #f9f9f9; color: #2c3e50; direction: rtl; line-height: 1.8; }
    .comic-panel { border: 4px solid #000; padding: 15px; background: white; box-shadow: 8px 8px 0px #000; margin-bottom: 20px; }
    .caption-tag { background: #ffde59; color: black; padding: 5px 10px; font-weight: bold; border: 2px solid #000; display: inline-block; margin-bottom: 10px; }
    .quiz-container { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e0e0e0; margin-top: 20px; direction: rtl; }
    /* إخفاء عناصر معينة عند الطباعة */
    @media print {
        .stButton, .stAudio, section[data-testid="stSidebar"], header { display: none !important; }
        .main { width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الربط مع API ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("المفتاح مفقود في إعدادات Secrets!")
    st.stop()

# --- 3. إدارة الحالة (State) ---
if 'score' not in st.session_state: st.session_state.score = 0
if 'lesson_data' not in st.session_state: st.session_state.lesson_data = None

# --- 4. اختيار الموديل التلقائي ---
@st.cache_resource
def load_model():
    try:
        available_models = genai.list_models()
        valid_models = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
        selected_name = valid_models[0]
        return genai.GenerativeModel(selected_name), selected_name
    except: return None, None

model, model_name = load_model()

# --- 5. وظائف مساعدة ---
def get_youtube_video(query):
    try:
        query_string = urllib.parse.urlencode({"search_query": query + " تعليمي للأطفال"})
        format_url = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)
        search_results = re.findall(r"watch\?v=(\S{11})", format_url.read().decode())
        if search_results: return "https://www.youtube.com/embed/" + search_results[0]
    except: return None

# --- 6. واجهة المستخدم (Sidebar) ---
with st.sidebar:
    st.title("⚙️ الإعدادات")
    st.success(f"الموديل: {model_name}")
    student_name = st.text_input("اسم الطالب:", value="طالب ذكي")
    age = st.number_input("العمر:", 5, 20, 12)
    output_format = st.radio("طريقة العرض:", ["درس تقليدي", "قصة مصورة (Comic)"])
    st.divider()
    st.metric("🏆 رصيد النقاط", st.session_state.score)
    
    # زر الحفظ كـ PDF (باستخدام خاصية الطباعة في المتصفح)
    st.markdown('<button onclick="window.print()" style="width:100%; padding:10px; background:#1a73e8; color:white; border:none; border-radius:5px; cursor:pointer;">📥 حفظ الدرس (PDF)</button>', unsafe_allow_html=True)
    
    if st.button("🗑️ ابدأ موضوعاً جديداً"):
        st.session_state.lesson_data = None
        st.session_state.score = 0
        st.rerun()

# --- 7. تنفيذ المحتوى ---
st.title("🌟 معلم Flexy الذكي")
topic = st.text_area("ماذا تريد أن تتعلم اليوم؟", placeholder="اكتب هنا الموضوع الذي يثير فضولك...")

if st.button("ابدأ الرحلة التعليمية 🚀"):
    if topic and model:
        with st.spinner("جاري ابتكار درسك الخاص..."):
            prompt = f"""
            أنت معلم محترف وممتع. اشرح موضوع {topic} لـ {student_name} (عمره {age}).
            التنسيق مطلوب كالتالي:
            1. إذا كان الاختيار 'قصة مصورة': أنشئ 4 لوحات. لكل لوحة:
               PANEL X:
               CAPTION: وصف المشهد بالعربية.
               DIALOGUE: حوار الشخصيات.
               VISUAL: [English description of the scene for AI image generation].
            2. إذا كان 'درس تقليدي': استخدم عناوين واضحة وصورة توضيحية [[English description for image]].
            3. في النهاية أضف سؤالين اختيار من متعدد:
               Q1: السؤال؟
               Options: A) كذا, B) كذا
               Correct: A
            اللغة: العربية الفصحى البسيطة.
            """
            response = model.generate_content(prompt)
            st.session_state.lesson_data = response.text
            
            # توليد الصوت
            try:
                clean_text = re.sub(r'\[\[.*?\]\]|PANEL.*|VISUAL:.*|Q\d:.*', '', response.text)
                tts = gTTS(text=clean_text[:500], lang='ar')
                tts.save("voice.mp3")
            except: pass
            st.rerun()

# --- 8. عرض النتائج ---
if st.session_state.lesson_data:
    content = st.session_state.lesson_data
    
    if os.path.exists("voice.mp3"):
        st.audio("voice.mp3")

    # عرض القصة المصورة
    if "PANEL" in content:
        panels = re.split(r'PANEL \d+:', content.split("Q1:")[0])[1:]
        cols = st.columns(2)
        for i, p in enumerate(panels[:4]):
            with cols[i % 2]:
                st.markdown('<div class="comic-panel">', unsafe_allow_html=True)
                vis = re.search(r'VISUAL:(.*?)(?=\n|$)', p)
                if vis:
                    img_q = vis.group(1).strip().replace(' ', '%20')
                    st.image(f"https://pollinations.ai/p/{img_q}?width=600&height=400&model=flux&seed={i}")
                
                # عرض النص (Caption & Dialogue)
                txt = p.split("VISUAL:")[0].replace("CAPTION:", "🎬").replace("DIALOGUE:", "💬")
                st.write(txt)
                st.markdown('</div>', unsafe_allow_html=True)
    
    # عرض الدرس التقليدي
    else:
        v_url = get_youtube_video(topic)
        if v_url:
            st.markdown(f'<iframe width="100%" height="450" src="{v_url}" frameborder="0" allowfullscreen style="border-radius:15px;"></iframe>', unsafe_allow_html=True)
        
        img_match = re.search(r'\[\[(.*?)\]\]', content)
        if img_match:
            img_q = img_match.group(1).replace(' ', '%20')
            st.image(f"https://pollinations.ai/p/{img_q}?width=1000&height=400&model=flux")
        
        clean_lesson = re.sub(r"\[\[.*?\]\]", "", content.split("Q1:")[0]).replace("\n", "<br>")
        st.markdown(f'<div class="lesson-box">{clean_lesson}</div>', unsafe_allow_html=True)

    # --- 9. قسم الاختبار التفاعلي ---
    st.divider()
    st.header("🧠 اختبر ذكاءك")
    
    if "Q1:" in content:
        q_text = content.split("Q1:")[1].split("Options:")[0]
        options = content.split("Options:")[1].split("Correct:")[0].strip()
        correct_ans = content.split("Correct:")[1][1:2].strip() # يأخذ حرف الإجابة
        
        st.write(f"**سؤال:** {q_text}")
        choice = st.radio("اختر الإجابة الصحيحة:", ["A", "B"], key="quiz_1")
        
        if st.button("تحقق من الإجابة"):
            if choice == correct_ans:
                st.success("إجابة رائعة! +10 نقاط 🏆")
                st.session_state.score += 10
                st.balloons()
            else:
                st.error(f"محاولة جيدة! الإجابة الصحيحة كانت {correct_ans}")
