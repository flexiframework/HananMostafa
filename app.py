import streamlit as st
import google.generativeai as genai

# 1. إعداد الصفحة
st.set_page_config(page_title="Flexy AI Tutor", layout="wide", page_icon="🎓")

# 2. الربط مع جوجل (باستخدام Secrets)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("المفتاح غير موجود في Secrets!")
    st.stop()

# 3. اختيار الموديل
model = genai.GenerativeModel("gemini-1.5-flash")

# 4. واجهة المستخدم
st.title("🌟 معلم Flexy الذكي")
st.sidebar.success("✅ متصل وجاهز للعمل")

topic = st.text_area("ماذا تريد أن تتعلم؟")
if st.button("ابدأ 🚀"):
    if topic:
        with st.spinner("جاري التحضير..."):
            try:
                response = model.generate_content(f"اشرح باختصار عن {topic}")
                st.write(response.text)
            except Exception as e:
                st.error(f"حدث خطأ: {e}")
