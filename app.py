# -- coding: utf-8 --
import streamlit as st
import os
import traceback
import io
import unicodedata
from dotenv import load_dotenv
from note_parser import pdf_to_text
from huggingface_hub import InferenceClient
from fpdf import FPDF

# === Load environment variables ===
load_dotenv()

HF_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# === Initialize Hugging Face model ===
client = InferenceClient("facebook/bart-large-cnn", token=HF_TOKEN)

# === Streamlit setup ===
st.set_page_config(page_title="📚 AI Note Converter", layout="wide")
st.session_state.setdefault("uploaded_text", "")

st.title("📚✨ AI Note Converter – Study Buddy 2.0")

st.markdown("""
<div style='background-color:#000000;
    color:white;
    padding:14px;
    border-radius:10px;
    margin-bottom:20px;
    text-align:center;
    font-size:17px;
    font-weight:600;
'>
<b>🚀 Upload your notes and let AI generate a 🧠summary, 🔖flashcards, and a 📝quiz instantly!</b>
</div>
""", unsafe_allow_html=True)

st.info("📱 Tip: If you're using a phone, keep this tab open — reloading will clear uploaded notes.")


# === Helper Functions ===
def summarize_text(text):
    """Summarize long text safely by chunking."""
    try:
        max_len = 1000  # safe chunk size for BART
        chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)]
        summaries = []

        for chunk in chunks:
            response = client.summarization(chunk)
            if isinstance(response, list) and len(response) > 0:
                first = response[0]
                if isinstance(first, dict):
                    for key in ("summary_text", "generated_text", "text", "content", "summary"):
                        if key in first:
                            summaries.append(first[key])
                            break
                    else:
                        summaries.append(str(first))
                else:
                    summaries.append(str(first))
            elif isinstance(response, dict):
                for key in ("summary_text", "generated_text", "text", "content", "summary"):
                    if key in response:
                        summaries.append(response[key])
                        break
                else:
                    summaries.append(str(response))
            else:
                summaries.append(str(response))

        return "\n\n".join(summaries)

    except Exception as e:
        raise Exception(f"Summarization error: {e}")


def generate_pdf(content: str) -> io.BytesIO:
    """Generate a PDF safely with Unicode replacement (no latin-1 error)."""
    replacements = {
        "\u2014": "-",   # em dash
        "\u2013": "-",   # en dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2022": "-",   # bullet
        "\u2026": "...", # ellipsis
        "\u2212": "-",   # minus
    }

    text = unicodedata.normalize("NFKD", content)
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or 32 <= ord(ch) <= 126 or ord(ch) >= 160)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.splitlines():
        pdf.multi_cell(0, 8, line)

    pdf_str = pdf.output(dest="S")
    pdf_bytes = pdf_str.encode("latin-1", errors="replace") if isinstance(pdf_str, str) else pdf_str
    pdf_buffer = io.BytesIO(pdf_bytes)
    pdf_buffer.seek(0)
    return pdf_buffer


def get_download_button(content, filename, label):
    """Display TXT and PDF download buttons using in-memory files only."""
    pdf_buffer = generate_pdf(content)
    txt_filename = filename
    pdf_filename = filename.replace(".txt", ".pdf")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label=f"💾 Download {label} (TXT)",
            data=content,
            file_name=txt_filename,
            mime="text/plain"
        )

    with col2:
        st.download_button(
            label=f"📘 Download {label} (PDF)",
            data=pdf_buffer,
            file_name=pdf_filename,
            mime="application/pdf"
        )


# === File Upload ===
uploaded_file = st.file_uploader("📤 Upload your notes (PDF or TXT)", type=["pdf", "txt"])
text = ""

if uploaded_file:
    try:
        if uploaded_file.type == "application/pdf":
            text = pdf_to_text(uploaded_file)
        else:
            text = uploaded_file.read().decode("utf-8")
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.text(traceback.format_exc())
        st.stop()

    # Display original notes
    with st.expander("📄 View Original Notes", expanded=False):
        st.text_area("Original Notes", text, height=300)

    # === Summarize Notes ===
    if st.button("📝 Summarize Notes"):
        with st.spinner("✨ Summarizing your notes..."):
            try:
                summary = summarize_text(text)
                st.markdown("<h3 style='color:#2E8B57;'>🧾 Summary</h3>", unsafe_allow_html=True)
                st.success(summary)
                get_download_button(summary, "Summary.txt", "Summary")
            except Exception as e:
                st.error("❌ Error summarizing notes.")
                st.caption(str(e))

    # === Flashcards ===
    if st.button("🧠 Generate Flashcards"):
        with st.spinner("🪄 Generating flashcards..."):
            try:
                from study_guide_generator import get_flashcard_chain
                flashcards = get_flashcard_chain().run(input_text=text)
                st.markdown("<h3 style='color:#4169E1;'>🔖 Flashcards</h3>", unsafe_allow_html=True)
                st.info(flashcards)
                get_download_button(flashcards, "Flashcards.txt", "Flashcards")
            except Exception as e:
                st.error("❌ Error generating flashcards.")
                st.caption(str(e))

    # === Quiz Generator ===
    if st.button("❓ Create Quiz"):
        with st.spinner("🧩 Generating quiz..."):
            try:
                from study_guide_generator import get_quiz_chain
                quiz = get_quiz_chain().run(input_text=text)
                st.markdown("<h3 style='color:#FF6347;'>📝 Quiz Questions</h3>", unsafe_allow_html=True)
                st.warning(quiz)
                get_download_button(quiz, "Quiz.txt", "Quiz")
            except Exception as e:
                st.error("❌ Error generating quiz.")
                st.caption(str(e))

    # === Reset Notes Button ===
    if st.button("🔄 Reset Notes"):
        st.session_state.clear()
        st.success("✅ Notes cleared successfully! Upload new notes to start again.")
        

else:
    st.info("📂 Please upload a PDF or TXT file to get started.")
