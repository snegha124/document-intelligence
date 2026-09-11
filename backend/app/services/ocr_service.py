import io
import os

import pymupdf
import pytesseract
from PIL import Image


TESSERACT_PATH = os.getenv(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def ocr_image(image: Image.Image) -> str:
    """Run Tesseract OCR on an image."""
    return pytesseract.image_to_string(
        image,
        config="--psm 6"
    )


def extract_text_from_document(
    filename: str,
    file_bytes: bytes
) -> dict:
    """
    Extract text from PDF or image documents.

    For PDFs:
    - Try native PDF text extraction first.
    - If there is little/no text, render each page and use OCR.

    For images:
    - Run OCR directly.
    """

    extension = "." + filename.lower().split(".")[-1]

    if extension == ".pdf":
        pdf = pymupdf.open(
            stream=file_bytes,
            filetype="pdf"
        )

        pages = []
        used_ocr = False

        for page_number, page in enumerate(pdf, start=1):

            native_text = page.get_text("text").strip()

            if len(native_text) >= 20:
                pages.append({
                    "page_number": page_number,
                    "text": native_text,
                    "method": "native_text"
                })
                continue

            # Scanned/image-based PDF page
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(3, 3),
                alpha=False
            )

            image = Image.open(
                io.BytesIO(pixmap.tobytes("png"))
            )

            text = ocr_image(image)

            pages.append({
                "page_number": page_number,
                "text": text,
                "method": "ocr"
            })

            used_ocr = True

        pdf.close()

        return {
            "pages": pages,
            "used_ocr": used_ocr
        }

    # JPG / JPEG / PNG
    image = Image.open(
        io.BytesIO(file_bytes)
    )

    text = ocr_image(image)

    return {
        "pages": [
            {
                "page_number": 1,
                "text": text,
                "method": "ocr"
            }
        ],
        "used_ocr": True
    }