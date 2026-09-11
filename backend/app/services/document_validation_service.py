import io

import pymupdf
from PIL import Image


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_PDF_PAGES = 3


def validate_document(filename: str, file_bytes: bytes) -> dict:

    if not filename:
        return {
            "valid": False,
            "error": "Filename is missing"
        }

    extension = "." + filename.lower().split(".")[-1]

    if extension not in ALLOWED_EXTENSIONS:
        return {
            "valid": False,
            "error": (
                "Unsupported file type. "
                "Allowed: PDF, JPG, JPEG, PNG"
            )
        }

    if not file_bytes:
        return {
            "valid": False,
            "error": "File is empty"
        }

    try:

        # PDF validation
        if extension == ".pdf":

            pdf = pymupdf.open(
                stream=file_bytes,
                filetype="pdf"
            )

            page_count = len(pdf)

            pdf.close()

            if page_count == 0:
                return {
                    "valid": False,
                    "error": "PDF contains no pages"
                }

            if page_count > MAX_PDF_PAGES:
                return {
                    "valid": False,
                    "error": "PDF must contain a maximum of 3 pages"
                }

            return {
                "valid": True,
                "page_count": page_count
            }

        # Image validation
        image = Image.open(
            io.BytesIO(file_bytes)
        )

        image.verify()

        return {
            "valid": True,
            "page_count": 1
        }

    except Exception:
        return {
            "valid": False,
            "error": (
                "The document could not be read "
                "or is corrupted"
            )
        }