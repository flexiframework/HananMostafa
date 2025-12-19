import streamlit as st
import google.generativeai as genai
import re
import os
from gtts import gTTS
import urllib.request
import urllib.parse

# 1. إعداد الصفحة والتصميم
st.set_page_config(page_title="رحلة الطالب الذكية", layout="wide", page_icon="🎓")

# 2. الربط مع Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("المفتاح مفقود!")
    st.stop()

# 3. واجهة الطالب الإحترافية (Sidebar)
with st.sidebar:
    st.header("👤 ملف الطالب الشخصي")
    student_name = st.text_input("اسم الطالب:", value="طالب ذكي")
    
    # 1. المستوى الأكاديمي
    level = st.selectbox("المستوى الأكاديمي:", ["مبتدئ", "متوسط", "متقدم"])
    
    # 2. العمر
    age = st.slider("عمر الطالب:", 5, 20, 12)
    
    # 3. نمط التعلم
    learning_style = st.radio("نمط التعلم المفضل:", ["بصري (صور مكثفة)", "سمعي (فيديو وصوت)", "حركي (تجارب ومشروعات)"])
    
    # 4. اللغة
    language = st.selectbox("لغة المحتوى:", ["العربية", "English", "Français", "Deutsch"])
    
    st.divider()
    if 'score' not in st.session_state: st.session_state.score = 0
    st.metric("🏆 نقاط التميز", st.session_state.score)

# 4. استرجاع درس المعلم
teacher_topic = st.session_state.get('teacher_content', "")

st.title(f"مرحباً بك يا {student_name}! 🚀")

if not teacher_topic:
    st.warning("بانتظار المعلم لوضع مادة الدرس...")
else:
    st.info(f"📍 الموضوع المطلوب دراسته: **{teacher_topic}**")
    
    if st.button("توليد درسي الخاص الآن ✨"):
        model = genai.GenerativeModel("gemini-1.5-flash")
        with st.spinner("ذكاء Flexy يحلل طلبك..."):
            
            # بناء الأمر (Prompt) بناءً على اختيارات الطالب
            prompt = f"""
            أنت معلم خبير في التعليم المخصص. اشرح موضوع: {teacher_topic}.
            المتطلبات الأساسية للرد:
            1. لغة المخرجات: {language} فقط.
            2. الفئة العمرية: {age} سنة (استخدم مفردات ولغة تخاطب تناسب هذا العمر).
            3. المستوى الأكاديمي: {level} (إذا كان مبتدئاً بسط المعلومات، إذا كان متقدماً تعمق في التفاصيل العلمية).
            4. نمط التعلم: {learning_style}. 
               - إذا كان بصرياً: ركز على الأوصاف الصورية المكثفة واستخدم [[Visual Description]].
               - إذا كان سمعياً: ركز على النصوص القابلة للقراءة الصوتية واقترح مصادر من (Khan Academy, National Geographic).
               - إذا كان حركياً: أضف قسماً خاصاً بعنوان 'تجارب ومشروعات منزلية' وأنشطة تفاعلية للقيام بها.
            5. التنسيق: استخدم عناوين واضحة، وأضف سؤالاً في النهاية بصيغة Q:, Options:, Correct:.
            """
            
            try:
                response = model.generate_content(prompt)
                st.session_state.lesson_data = response.text
                
                # توليد الصوت (فقط إذا كانت اللغة العربية أو الإنجليزية)
                lang_code = {'العربية': 'ar', 'English': 'en', 'Français': 'fr', 'Deutsch': 'de'}[language]
                clean_text = re.sub(r'\[\[.*?\]\]|Q:.*', '', response.text)
                tts = gTTS(text=clean_text[:500], lang=lang_code)
                tts.save("voice.mp3")
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ: {e}")

    # 5. عرض المخرجات المخصصة
    if st.session_state.get('lesson_data'):
        content = st.session_state.lesson_data
        
        # تشغيل الصوت
        if os.path.exists("voice.mp3"):
            st.audio("voice.mp3")

        # عرض الصور إذا كان النمط بصرياً أو درساً عادياً
        img_match = re.search(r'\[\[(.*?)\]\]', content)
        if img_match:
            img_q = img_match.group(1).replace(' ', '%20')
            st.image(f"https://pollinations.ai/p/{img_q}?width=1000&height=400&model=flux")

        # عرض المحتوى النصي بتنسيق جميل
        st.markdown(f'<div style="direction: {"rtl" if language == "العربية" else "ltr"}; text-align: justify; background: #f0f2f6; padding: 20px; border-radius: 10px;">{content.split("Q:")[0].replace("\n", "<br>")}</div>', unsafe_allow_html=True)

        # إذا كان النمط سمعياً، ابحث عن فيديو يوتيوب من منصات عالمية
        if "سمعي" in learning_style:
            st.subheader("📺 فيديو تعليمي مقترح")
            search_query = f"{teacher_topic} {language} educational video"
            # وظيفة البحث المبسطة (التي استخدمناها سابقاً)
            query_string = urllib.parse.urlencode({"search_query": search_query})
            format_url = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)
            search_results = re.findall(r"watch\?v=(\S{11})", format_url.read().decode())
            if search_results:
                st.video(f"https://www.youtube.com/watch?v={search_results[0]}")
