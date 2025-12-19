# --- 3. اختيار الموديل الذكي (لتجنب خطأ 404) ---
@st.cache_resource
def load_model():
    try:
        # البحث عن الموديلات التي تدعم توليد المحتوى
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not available_models:
            return None
        # اختيار أول موديل متاح (غالباً سيكون الأحدث)
        return genai.GenerativeModel(available_models[0])
    except Exception as e:
        st.error(f"خطأ في الاتصال بالموديلات: {e}")
        return None

model = load_model()

# --- في جزء الضغط على زر "توليد درسي الخاص الآن" ---
if st.button("توليد درسي الخاص الآن ✨"):
    if model is None:
        st.error("عذراً، لا يوجد موديل ذكاء اصطناعي متاح حالياً.")
    else:
        with st.spinner("ذكاء Flexy يحلل طلبك باستخدام أفضل الموديلات المتاحة..."):
            # نفس الـ Prompt الاحترافي الذي طلبته
            prompt = f"""
            أنت معلم خبير. اشرح موضوع: {teacher_topic}.
            المتطلبات:
            1. اللغة: {language}.
            2. العمر: {age} سنة.
            3. المستوى: {level}.
            4. نمط التعلم: {learning_style}.
               - إذا كان بصرياً: استخدم [[Visual Description]].
               - إذا كان سمعياً: اقترح فيديوهات تعليمية.
               - إذا كان حركياً: أضف قسم 'تجارب ومشروعات'.
            5. التنسيق: عناوين واضحة وسؤال MCQ في النهاية.
            """
            try:
                # نستخدم الموديل الذي تم تحميله تلقائياً
                response = model.generate_content(prompt)
                st.session_state.lesson_data = response.text
                # ... بقية كود الصوت والصور ...
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ أثناء التوليد: {e}")
