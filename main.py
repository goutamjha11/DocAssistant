import streamlit as st
import fitz
import io
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import re
from pathlib import Path
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.callbacks import get_openai_callback
from src.utils import save_image_correctly, extract_text_blocks, translate_text_blocks, clean_bullet_points

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

with st.sidebar:
    st.title('Document translation App')
    st.markdown('''
    ## About
    Translation APP
    ''')
    st.write('Owner [Goutam Kumar Jha](https://www.linkedin.com/in/goutam-kumar-jha-519701182/)')


def create_translated_pdf_from_blocks(file_content, translated_blocks, output_pdf_path):
    original_pdf = fitz.open(stream=io.BytesIO(file_content), filetype="pdf")

    pdf_dimensions = [(page.rect.width, page.rect.height) for page in original_pdf]

    new_pdf = canvas.Canvas(output_pdf_path, pagesize=letter)

    for i, (page_blocks, (width, height)) in enumerate(zip(translated_blocks, pdf_dimensions)):
        page = original_pdf[i]

        # Adjust canvas to match the original page size
        new_pdf.setPageSize((width, height))

        # Draw images from the original PDF
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = original_pdf.extract_image(xref)
            img_bytes = base_image["image"]
            img_ext = base_image["ext"]
            img_filename = f"image_{i}_{img_index}.{img_ext}"
            save_image_correctly(img_bytes, img_ext, img_filename)
            image_rect = page.get_image_rects(xref)[0]
            x, y = image_rect.x0, image_rect.y0
            img_width, img_height = image_rect.width, image_rect.height
            new_pdf.drawImage(img_filename, x, height - y - img_height, width=img_width, height=img_height)

        # Place the translated text, maintaining formatting
        for block in page_blocks:
            for line in block['lines']:
                for span in line['spans']:
                    x0 = span['bbox'][0]
                    y0 = span['bbox'][1]
                    text = span['text']
                    text = re.sub(r'•\n', '• ', text)
                    text = re.sub(r'o\n', 'o ', text)
                    text = re.sub(r'\uf0b7\s*', '• ', text)
                    text = re.sub(r'\uf0a7\s*', '• ', text)  # change square bullet to round
                    text = re.sub(r'(?<=\S)\n(?=\S)', ' ', text)
                    text = re.sub(r'(?<=\S)[\n»](?=\S)', ' ', text)
                    font = span['font']
                    size = span['size']
                    flags = span['flags']
                    text_y = height - y0  # Adjust y position according to ReportLab coordinates

                    # Set font and size based on original PDF
                    if flags & 2:  # Bold flag in MuPDF
                        new_pdf.setFont("Helvetica-Bold", size)
                    else:
                        new_pdf.setFont("Helvetica", size)

                    # Draw the translated text
                    available_width = width - x0
                    wrapped_text = simpleSplit(text, new_pdf._fontname, size, available_width)
                    for line in wrapped_text:
                        new_pdf.drawString(x0, text_y, line)
                        text_y -= new_pdf._leading  # Move down for the next line

        new_pdf.showPage()

    new_pdf.save()

def main():
    st.header('Translate your PDF ')

    uploaded_file = st.file_uploader("Upload your PDF", type='pdf')
    language_code =st.text_input("Enter the target language code (e.g., 'fr' for French, 'es' for Spanish)")

    if st.button("Translate"):
        if uploaded_file is not None and language_code:
            # Read the file content once and reuse it
            file_content = uploaded_file.read()

            # Step 1: Extract text blocks
            text_blocks = extract_text_blocks(file_content)

            # Step 2: Translate the text blocks
            translated_blocks = translate_text_blocks(text_blocks, language_code)

            # Step 3: Create translated PDF
            translated_pdf_path = f"{uploaded_file.name}_translated.pdf"
            create_translated_pdf_from_blocks(file_content, translated_blocks, translated_pdf_path)

            # Step 4: Provide download link
            with open(translated_pdf_path, "rb") as file:
                st.download_button(
                    label="Download Translated PDF",
                    data=file,
                    file_name=translated_pdf_path,
                    mime="application/pdf"
                )
        else:
            st.error("Please upload a file and enter a language code.")


if __name__ == "__main__":
    main()