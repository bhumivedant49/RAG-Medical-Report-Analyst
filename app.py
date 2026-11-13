import os
import streamlit as st
from dotenv import load_dotenv

from src.pdf_reader import extract_pdf_pages, split_into_chunks
from src.retriever import ReportIndex, get_embedding_model
from src.groq_client import answer_question, summarize_report

load_dotenv()

st.set_page_config(
    page_title="ReportLens | Medical Report Explainer",
    page_icon="🩺",
    layout="wide",
)

DISCLAIMER = (
    "ReportLens is an educational document-explanation tool. It does not diagnose, "
    "recommend treatment, or replace advice from a qualified healthcare professional."
)

def init_state():
    defaults = {"report_index": None, "report_names": [], "messages": [], "report_text": ""}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def run_app():
    init_state()
    st.title("🩺 ReportLens")
    st.caption("Understand what your medical report says — with answers linked back to its pages.")
    st.info(DISCLAIMER)

    with st.sidebar:
        st.header("Your documents")
        uploads = st.file_uploader(
            "Upload one or more PDF reports",
            type=["pdf"],
            accept_multiple_files=True,
            help="Text-based PDFs are supported. Scanned image-only PDFs need OCR and are not processed yet.",
        )
        groq_key = st.text_input(
            "Groq API key",
            value=os.getenv("GROQ_API_KEY", ""),
            type="password",
            help="Your key is used for this session and is not saved by the app.",
        )
        if st.button("Process reports", type="primary", use_container_width=True, disabled=not uploads):
            if not groq_key:
                st.error("Add your Groq API key to continue.")
            else:
                try:
                    all_chunks, names, full_text = [], [], []
                    with st.spinner("Reading PDFs and preparing searchable sections..."):
                        for upload in uploads:
                            pages = extract_pdf_pages(upload.getvalue(), upload.name)
                            chunks = split_into_chunks(pages)
                            if not chunks:
                                st.warning(f"No selectable text found in {upload.name}. It may be a scanned PDF.")
                                continue
                            all_chunks.extend(chunks)
                            names.append(upload.name)
                            full_text.extend([p["text"] for p in pages if p["text"].strip()])
                        if not all_chunks:
                            st.error("No readable text was found. Try a text-based PDF.")
                        else:
                            model = get_embedding_model()
                            st.session_state.report_index = ReportIndex(all_chunks, model)
                            st.session_state.report_names = names
                            st.session_state.report_text = "\n\n".join(full_text)
                            st.session_state.messages = []
                            st.success(f"Processed {len(names)} report(s).")
                except Exception as exc:
                    st.error(f"Could not process the reports: {exc}")

        if st.session_state.report_names:
            st.success("Loaded: " + ", ".join(st.session_state.report_names))
            if st.button("Clear session", use_container_width=True):
                for key in ("report_index", "report_names", "messages", "report_text"):
                    st.session_state[key] = [] if key in ("report_names", "messages") else ("" if key == "report_text" else None)
                st.rerun()

    if st.session_state.report_index is None:
        st.markdown("### Get started")
        st.write("Upload a blood test, discharge summary, prescription, or other text-based PDF report.")
        st.write("Once processed, you can request a plain-language overview or ask questions about specific terms and values.")
        return

    overview_tab, chat_tab, sources_tab = st.tabs(["Report overview", "Ask your report", "How it works"])
    with overview_tab:
        st.subheader("Plain-language overview")
        st.write("The overview is generated only from the text extracted from your uploaded reports.")
        if st.button("Generate overview", type="primary"):
            if not groq_key:
                st.error("Add your Groq API key in the sidebar.")
            else:
                with st.spinner("Preparing an explanation..."):
                    try:
                        st.session_state.overview = summarize_report(groq_key, st.session_state.report_text)
                    except Exception as exc:
                        st.error(f"Summary failed: {exc}")
        if st.session_state.get("overview"):
            st.markdown(st.session_state.overview)
        st.caption("Always verify important findings and reference ranges with your clinician.")

    with chat_tab:
        st.subheader("Ask a question")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        prompt = st.chat_input("Example: What does the HbA1c section say?")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                if not groq_key:
                    response = "Please add your Groq API key in the sidebar."
                else:
                    with st.spinner("Searching the report..."):
                        try:
                            matches = st.session_state.report_index.search(prompt, top_k=5)
                            response = answer_question(groq_key, prompt, matches)
                        except Exception as exc:
                            response = f"I couldn't complete the request: {exc}"
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    with sources_tab:
        st.subheader("Document processing")
        st.markdown(
            "- Extracts selectable text from each PDF page.\n"
            "- Splits text into overlapping passages while retaining page numbers.\n"
            "- Creates local sentence embeddings and searches with FAISS.\n"
            "- Sends only retrieved passages to the language model for question answering.\n\n"
            "**Current limitation:** image-only/scanned PDFs are not OCR-processed."
        )
        st.warning(DISCLAIMER)

if __name__ == "__main__":
    run_app()
