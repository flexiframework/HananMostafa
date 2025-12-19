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

# --- 3. اختيار الموديل (تعديل ليتناسب مع v1beta) ---
@st.cache_resource
def load_model():
    # سنحاول تجربة الأسماء المختلفة للموديل حتى ينجح أحدها
    model_names = [
        "models/gemini-1.5-flash-latest", 
        "gemini-1.5-flash", 
        "models/gemini-pro"
    ]
    
    for name in model_names:
        try:
            m = genai.GenerativeModel(name)
            # تجربة حقيقية للتأكد من أن الموديل يدعم generateContent
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m, name
        except Exception:
            continue
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
