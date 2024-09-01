import fitz  # PyMuPDF
from PIL import Image
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.lib import pdfencrypt
from googletrans import Translator
import re


def save_image_correctly(img_bytes, img_ext, img_filename):
    image = Image.open(io.BytesIO(img_bytes))
    if image.mode == 'RGBA':
        image.save(img_filename, format=img_ext.upper())
    else:
        image.save(img_filename)


def extract_text_blocks(file_content):
    pdf_document = fitz.open(stream=io.BytesIO(file_content), filetype="pdf")
    page_text_blocks = []
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text_blocks = page.get_text("dict")["blocks"]
        page_text_blocks.append(text_blocks)
    return page_text_blocks

def translate_text_blocks(text_blocks, src='en', dest='fr'):
    translator = Translator()
    translated_blocks = []
    for page_blocks in text_blocks:
        page_translations = []
        for block in page_blocks:
            if 'lines' in list(block.keys()):
                for line in block['lines']:
                    for span in line['spans']:
                        text = span['text']
                        if text.strip():
                            translation = translator.translate(text, src=src, dest=dest).text
                            span['text'] = translation
                    page_translations.append(block)
        translated_blocks.append(page_translations)
    return translated_blocks

def clean_bullet_points(text):
    # Replace the problematic bullet point with a safer alternative
    cleaned_text = text.replace('■', '•')  # Replace black square box with bullet point
    return cleaned_text
