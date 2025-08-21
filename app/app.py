# app/app.py
import os
import streamlit as st
from infer import get_model

st.set_page_config(page_title="Sentiment Analysis", page_icon="🧠")

st.title("🧠 Sentiment Analysis (DistilBERT)")
st.caption("Enter a sentence and click **Analyze** to see Positive/Negative.")

# Model klasörü bilgisi (görsel uyarı)
model_dir = os.getenv("MODEL_DIR", "models/distilbert/global_tf")
with st.expander("Model settings", expanded=False):
    st.write(f"**MODEL_DIR**: `{model_dir}`")
    st.info("If model files are not found, set environment variable: "
            "`MODEL_DIR=/full/path/to/global_tf`")

# Modeli yükle (cache'li)
@st.cache_resource(show_spinner=True)
def load_cached():
    return get_model()

try:
    sm = load_cached()
except Exception as e:
    st.error(
        "Model yüklenemedi. `MODEL_DIR` yolunu ve model dosyalarını kontrol et.\n\n"
        f"Hata: {e}"
    )
    st.stop()

# Basit örnekler
examples = [
    "I absolutely love this phone, the battery lasts forever!",
    "This is the worst purchase I have ever made.",
    "Pretty decent quality for the price.",
]

with st.sidebar:
    st.subheader("Quick examples")
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["input_text"] = ex

st.markdown("### Input")
text = st.text_area(
    "Write a single sentence or multiple lines (each line will be analyzed).",
    value=st.session_state.get("input_text", "I love this product!"),
    height=140,
)

col1, col2 = st.columns([2, 1])
with col1:
    max_len = st.slider("Max sequence length", 32, 512, 256, 32)
with col2:
    show_probs = st.toggle("Show probabilities", value=True)

analyze = st.button("Analyze", type="primary")

def sanitize_lines(s: str):
    # Çoklu satır varsa; boşları at
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    return lines if len(lines) > 1 else [s.strip()] if s.strip() else []

if analyze:
    texts = sanitize_lines(text)
    if not texts:
        st.warning("Please enter a longer text.")
    else:
        preds, probs = sm.predict(texts, max_len=max_len)
        id2label = sm.id2label

        st.markdown("### Results")
        for i, t in enumerate(texts):
            label = id2label[int(preds[i])]
            st.write(f"**{i+1}. {label}** — {t}")
            if show_probs and probs:
                # Basit olasılık tablosu
                st.write({id2label[j]: float(probs[i][j]) for j in range(len(probs[i]))})

