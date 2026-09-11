import io

import pymupdf
from PIL import Image


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}

MAX_PDF_PAGES = 3


def validate_document(
    filename: str,
    file_bytes: bytes
) -> dict:
    """
    Validate an uploaded document.

    Returns:
        {
            "valid": True/False,
            ...
        }
    """

    # ---------------------------------------------------------
    # 1. Filename validation
    # ---------------------------------------------------------

    if not filename:

        return {
            "valid": False,
            "error": "Filename is missing",
        }

    # ---------------------------------------------------------
    # 2. File extension validation
    # ---------------------------------------------------------

    extension = "." + filename.lower().split(".")[-1]

    if extension not in ALLOWED_EXTENSIONS:

        return {
            "valid": False,
            "error": (
                "Unsupported file type. "
                "Allowed: PDF, JPG, JPEG, PNG"
            ),
        }

    # ---------------------------------------------------------
    # 3. Empty file validation
    # ---------------------------------------------------------

    if not file_bytes:

        return {
            "valid": False,
            "error": "File is empty",
        }

    # ---------------------------------------------------------
    # 4. PDF validation
    # ---------------------------------------------------------

    if extension == ".pdf":

        try:

            pdf = pymupdf.open(
                stream=file_bytes,
                filetype="pdf",
            )

            page_count = len(pdf)

            pdf.close()

            # No pages
            if page_count == 0:

                return {
                    "valid": False,
                    "error": "PDF contains no pages",
                }

            # More than 3 pages
            if page_count > MAX_PDF_PAGES:

                return {
                    "valid": False,
                    "error": (
                        "PDF must contain a maximum of 3 pages"
                    ),
                }

            return {
                "valid": True,
                "page_count": page_count,
            }

        except Exception:

            return {
                "valid": False,
                "error": (
                    "The document could not be read "
                    "or is corrupted"
                ),
            }

    # ---------------------------------------------------------
    # 5. Image validation
    # ---------------------------------------------------------

    try:

        image = Image.open(
            io.BytesIO(file_bytes)
        )

        image.verify()

        return {
            "valid": True,
            "page_count": 1,
        }

    except Exception:

        return {
            "valid": False,
            "error": (
                "The document could not be read "
                "or is corrupted"
            ),
        }