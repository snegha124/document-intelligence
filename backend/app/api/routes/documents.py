import json

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
)

from google.genai.errors import ClientError

from sqlalchemy.orm import Session

from backend.app.core.database import get_db

from backend.app.services.document_validation_service import (
    validate_document,
)

from backend.app.services.ocr_service import (
    extract_text_from_document,
)

from backend.app.services.extraction_service import (
    extract_invoice,
    extract_balance_sheet,
    extract_profit_loss,
    extract_cash_flow,
)

from backend.app.services.financial_validation_service import (
    validate_invoice,
    validate_balance_sheet,
    validate_profit_loss,
    validate_cash_flow,
)

from backend.app.repositories.document_repository import (
    create_document,
    get_all_documents,
    get_document_by_name,
)


# =============================================================
# ROUTER
# =============================================================

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)


# =============================================================
# GEMINI ERROR HANDLER
# =============================================================

def handle_gemini_error(
    error: Exception,
):
    """
    Convert Gemini API errors into useful HTTP responses.
    """

    error_text = str(error)

    if isinstance(
        error,
        ClientError,
    ):

        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
        ):

            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota exceeded. "
                    "Please try again later or check "
                    "your Gemini API plan/quota."
                ),
            )

        raise HTTPException(
            status_code=502,
            detail=(
                f"Gemini API error: {error_text}"
            ),
        )

    raise error


# =============================================================
# PROCESS DOCUMENT
# =============================================================

@router.post("/process")
async def process_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Upload, validate, OCR, extract and financially
    validate a document.
    """

    # ---------------------------------------------------------
    # 1. Validate document type
    # ---------------------------------------------------------

    allowed_document_types = {
        "Invoice",
        "Balance Sheet",
        "Profit & Loss",
        "Cash Flow",
    }

    if document_type not in allowed_document_types:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported document type. "
                "Allowed: Invoice, Balance Sheet, "
                "Profit & Loss, Cash Flow"
            ),
        )

    # ---------------------------------------------------------
    # 2. Read uploaded file
    # ---------------------------------------------------------

    file_bytes = await file.read()

    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # ---------------------------------------------------------
    # 3. Validate document
    # ---------------------------------------------------------

    try:

        validation_result = validate_document(
            filename=file.filename,
            file_bytes=file_bytes,
        )

        if not validation_result.get(
            "valid",
            False,
        ):

            raise HTTPException(
                status_code=400,
                detail=validation_result.get(
                    "error",
                    "Document validation failed",
                ),
            )

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Document validation failed: "
                f"{str(error)}"
            ),
        )

    # ---------------------------------------------------------
    # 4. OCR / text extraction
    # ---------------------------------------------------------

    try:

        ocr_result = extract_text_from_document(
            filename=file.filename,
            file_bytes=file_bytes,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"OCR/text extraction failed: "
                f"{str(error)}"
            ),
        )

    # ---------------------------------------------------------
    # 5. Combine OCR page text
    # ---------------------------------------------------------

    pages = ocr_result.get(
        "pages",
        [],
    )

    ocr_text_parts = []

    for page in pages:

        page_number = page.get(
            "page_number"
        )

        text = page.get(
            "text",
            "",
        )

        ocr_text_parts.append(
            f"--- Page {page_number} ---\n{text}"
        )

    ocr_text = "\n\n".join(
        ocr_text_parts
    )

    if not ocr_text.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "No readable text could be "
                "extracted from the document."
            ),
        )

    # ---------------------------------------------------------
    # 6. Gemini extraction + financial validation
    # ---------------------------------------------------------

    try:

        # =====================================================
        # INVOICE
        # =====================================================

        if document_type == "Invoice":

            invoice = extract_invoice(
                ocr_text
            )

            invoice_data = (
                invoice.model_dump()
            )

            extraction_data = {
                "document_type": "Invoice",
                "invoice": invoice_data,
            }

            validation_data = (
                validate_invoice(
                    invoice
                )
            )

        # =====================================================
        # BALANCE SHEET
        # =====================================================

        elif document_type == "Balance Sheet":

            # IMPORTANT:
            # Send both OCR text and the original file.
            # This allows Gemini to inspect the actual
            # table image and column alignment.

            balance_sheet = extract_balance_sheet(
                ocr_text,
                file_bytes=file_bytes,
                filename=file.filename,
            )

            balance_sheet_data = (
                balance_sheet.model_dump()
            )

            extraction_data = {
                "document_type": "Balance Sheet",
                "balance_sheet": balance_sheet_data,
            }

            validation_data = (
                validate_balance_sheet(
                    balance_sheet
                )
            )

        # =====================================================
        # PROFIT & LOSS
        # =====================================================

        elif document_type == "Profit & Loss":

            profit_loss = extract_profit_loss(
                ocr_text
            )

            profit_loss_data = (
                profit_loss.model_dump()
            )

            extraction_data = {
                "document_type": "Profit & Loss",
                "profit_loss": profit_loss_data,
            }

            validation_data = (
                validate_profit_loss(
                    profit_loss
                )
            )

        # =====================================================
        # CASH FLOW
        # =====================================================

        elif document_type == "Cash Flow":

            cash_flow = extract_cash_flow(
                ocr_text
            )

            cash_flow_data = (
                cash_flow.model_dump()
            )

            extraction_data = {
                "document_type": "Cash Flow",
                "cash_flow": cash_flow_data,
            }

            validation_data = (
                validate_cash_flow(
                    cash_flow
                )
            )

        else:

            raise HTTPException(
                status_code=400,
                detail="Unsupported document type.",
            )

    except HTTPException:
        raise

    except ClientError as error:

        handle_gemini_error(
            error
        )

    except Exception as error:

        handle_gemini_error(
            error
        )

    # ---------------------------------------------------------
    # 7. Determine validation status
    # ---------------------------------------------------------

    overall_status = (
        validation_data.get(
            "overall_status",
            "failed",
        )
    )

    # The document itself was successfully processed.
    # Financial validation can independently be passed,
    # failed, or not_checkable.

    status = "processed"

    # ---------------------------------------------------------
    # 8. Save result in database
    # ---------------------------------------------------------

    try:

        document = create_document(
            db=db,
            document_name=file.filename,
            document_type=document_type,
            status=status,
            extraction_data=extraction_data,
            validation_data=validation_data,
            ocr_text=ocr_text,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Database save failed: "
                f"{str(error)}"
            ),
        )

    # ---------------------------------------------------------
    # 9. Return result
    # ---------------------------------------------------------

    return {
        "id": document.id,
        "document_name": document.document_name,
        "document_type": document.document_type,
        "status": document.status,
        "validation_status": overall_status,
        "created_at": (
            document.created_at.isoformat()
            if document.created_at
            else None
        ),
        "extraction": extraction_data,
        "validation": validation_data,
        "ocr_text": ocr_text,
    }


# =============================================================
# GET ALL DOCUMENTS
# =============================================================

@router.get("")
def list_documents(
    db: Session = Depends(get_db),
):
    """
    Return all processed documents.
    """

    documents = get_all_documents(
        db
    )

    return [
        {
            "id": document.id,
            "document_name": document.document_name,
            "document_type": document.document_type,
            "status": document.status,
            "created_at": (
                document.created_at.isoformat()
                if document.created_at
                else None
            ),
        }
        for document in documents
    ]


# =============================================================
# GET ONE DOCUMENT
# =============================================================

@router.get("/{document_name}")
def get_document(
    document_name: str,
    db: Session = Depends(get_db),
):
    """
    Return complete information for one
    processed document.
    """

    document = get_document_by_name(
        db,
        document_name,
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return {
        "id": document.id,
        "document_name": document.document_name,
        "document_type": document.document_type,
        "status": document.status,
        "created_at": (
            document.created_at.isoformat()
            if document.created_at
            else None
        ),
        "extraction": (
            json.loads(
                document.extraction_json
            )
            if document.extraction_json
            else None
        ),
        "validation": (
            json.loads(
                document.validation_json
            )
            if document.validation_json
            else None
        ),
        "ocr_text": document.ocr_text,
    }