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

# --- 3. اختيار الموديل (النسخة الكلاسيكية المستقرة) ---
@st.cache_resource
def load_model():
    # سنحاول الاتصال بالموديل الأكثر قبولاً في جميع المناطق
    try:
        # جرب النسخة المستقرة gemini-pro
        m = genai.GenerativeModel("gemini-pro")
        m.generate_content("Hi", generation_config={"max_output_tokens": 1})
        return m, "gemini-pro"
    except Exception:
        try:
            # إذا فشل، جرب النسخة 1.0 pro
            m = genai.GenerativeModel("models/gemini-1.0-pro")
            m.generate_content("Hi", generation_config={"max_output_tokens": 1})
            return m, "gemini-1.0-pro"
        except Exception as e:
            # طباعة الخطأ الحقيقي للمساعدة في التشخيص
            st.sidebar.write(f"Error Detail: {e}")
            return None, None

model, final_name = load_model()

# --- 4. واجهة المستخدم ---
if model:
    st.sidebar.success(f"✅ متصل بـ {final_name}")
else:
    st.sidebar.error("❌ الموديل غير مدعوم في منطقتك أو حسابك")

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
