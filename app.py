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

# 3. اختيار الموديل (البحث التلقائي)
@st.cache_resource
def load_model():
    try:
        # البحث عن الموديلات المتاحة
        available_models = genai.list_models()
        valid_models = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
        
        if not valid_models:
            return None, "No models found"

        # اختيار الموديل الأول المتاح وتجربته
        selected_name = valid_models[0]
        m = genai.GenerativeModel(selected_name)
        m.generate_content("Hi", generation_config={"max_output_tokens": 1})
        return m, selected_name
    except Exception as e:
        return None, str(e)

# تشغيل وظيفة التحميل
model, final_name = load_model()

# 4. واجهة المستخدم
st.title("🌟 معلم Flexy الذكي")

if model:
    st.sidebar.success(f"✅ متصل بـ {final_name}")
else:
    st.sidebar.error("❌ فشل العثور على موديل")
    st.sidebar.write(f"التفاصيل: {final_name}")

topic = st.text_area("ماذا تريد أن تتعلم؟")
if st.button("ابدأ 🚀"):
    if topic and model:
        with st.spinner("جاري التحضير..."):
            try:
                response = model.generate_content(f"اشرح باختصار عن {topic}")
                st.write(response.text)
            except Exception as e:
                st.error(f"حدث خطأ أثناء التوليد: {e}")
