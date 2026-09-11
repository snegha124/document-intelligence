import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from google.genai.errors import ClientError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db

from backend.app.services.document_validation_service import validate_document
from backend.app.services.ocr_service import extract_text_from_document


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


router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"]
)


def handle_gemini_error(exc: ClientError):
    if (
        getattr(exc, "code", None) == 429
        or "RESOURCE_EXHAUSTED" in str(exc)
        or "429" in str(exc)
    ):
        raise HTTPException(
            status_code=429,
            detail=(
                "Gemini API quota exceeded. "
                "Please try again later or check your Gemini API plan/quota."
            )
        )

    raise HTTPException(
        status_code=502,
        detail="Gemini API request failed."
    )


@router.post("/process")
async def process_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
):

    # ---------------------------------------------------------
    # 1. Read uploaded file
    # ---------------------------------------------------------
    file_bytes = await file.read()

    # ---------------------------------------------------------
    # 2. Validate document
    # ---------------------------------------------------------
    validation_result = validate_document(
        filename=file.filename,
        file_bytes=file_bytes
    )

    if not validation_result["valid"]:
        raise HTTPException(
            status_code=400,
            detail=validation_result["error"]
        )

    # ---------------------------------------------------------
    # 3. OCR / text extraction
    # ---------------------------------------------------------
    ocr_result = extract_text_from_document(
        filename=file.filename,
        file_bytes=file_bytes
    )

    ocr_text = "\n".join(
        page["text"]
        for page in ocr_result["pages"]
    )

    # ---------------------------------------------------------
    # 4. Normalize document type
    # ---------------------------------------------------------
    document_type_lower = document_type.lower().strip()

    # ---------------------------------------------------------
    # 5. Invoice
    # ---------------------------------------------------------
    if document_type_lower == "invoice":

        try:
            invoice = extract_invoice(ocr_text)
        except ClientError as exc:
            handle_gemini_error(exc)

        financial_validation = validate_invoice(invoice)

        extraction_data = invoice.model_dump()
        validation_data = financial_validation

        create_document(
            db=db,
            document_name=file.filename,
            document_type="Invoice",
            status="processed",
            extraction_data=extraction_data,
            validation_data=validation_data,
            ocr_text=ocr_text,
        )

        return {
            "message": "Document processed successfully",
            "filename": file.filename,
            "document_type": document_type,
            "validation": validation_result,
            "ocr": ocr_result,
            "extraction": extraction_data,
            "financial_validation": validation_data,
        }

    # ---------------------------------------------------------
    # 6. Balance Sheet
    # ---------------------------------------------------------
    if document_type_lower in {
        "balance sheet",
        "balance_sheet"
    }:

        try:
            balance_sheet = extract_balance_sheet(ocr_text)
        except ClientError as exc:
            handle_gemini_error(exc)

        financial_validation = validate_balance_sheet(
            balance_sheet
        )

        extraction_data = balance_sheet.model_dump()
        validation_data = financial_validation

        create_document(
            db=db,
            document_name=file.filename,
            document_type="Balance Sheet",
            status="processed",
            extraction_data=extraction_data,
            validation_data=validation_data,
            ocr_text=ocr_text,
        )

        return {
            "message": "Document processed successfully",
            "filename": file.filename,
            "document_type": document_type,
            "validation": validation_result,
            "ocr": ocr_result,
            "extraction": extraction_data,
            "financial_validation": validation_data,
        }

    # ---------------------------------------------------------
    # 7. Profit & Loss
    # ---------------------------------------------------------
    if document_type_lower in {
        "profit & loss",
        "profit and loss",
        "profit_loss",
        "p&l"
    }:

        try:
            profit_loss = extract_profit_loss(ocr_text)
        except ClientError as exc:
            handle_gemini_error(exc)

        financial_validation = validate_profit_loss(
            profit_loss
        )

        extraction_data = profit_loss.model_dump()
        validation_data = financial_validation

        create_document(
            db=db,
            document_name=file.filename,
            document_type="Profit & Loss",
            status="processed",
            extraction_data=extraction_data,
            validation_data=validation_data,
            ocr_text=ocr_text,
        )

        return {
            "message": "Document processed successfully",
            "filename": file.filename,
            "document_type": document_type,
            "validation": validation_result,
            "ocr": ocr_result,
            "extraction": extraction_data,
            "financial_validation": validation_data,
        }

    # ---------------------------------------------------------
    # 8. Cash Flow
    # ---------------------------------------------------------
    if document_type_lower in {
        "cash flow",
        "cash flows",
        "cash_flow",
        "cash_flows"
    }:

        try:
            cash_flow = extract_cash_flow(ocr_text)
        except ClientError as exc:
            handle_gemini_error(exc)

        extraction_data = cash_flow.model_dump()

        financial_validation = validate_cash_flow(
        cash_flow
        )

        validation_data = financial_validation

        create_document(
            db=db,
            document_name=file.filename,
            document_type="Cash Flow",
            status="processed",
            extraction_data=extraction_data,
            validation_data=validation_data,
            ocr_text=ocr_text,
        )

        return {
            "message": "Document processed successfully",
            "filename": file.filename,
            "document_type": document_type,
            "validation": validation_result,
            "ocr": ocr_result,
            "extraction": extraction_data,
            "financial_validation": validation_data,
        }

    # ---------------------------------------------------------
    # 9. Unsupported document type
    # ---------------------------------------------------------
    raise HTTPException(
        status_code=400,
        detail=(
            "Unsupported document type. "
            "Currently supported: Invoice, Balance Sheet, "
            "Profit & Loss, Cash Flow"
        )
    )


# =============================================================
# GET ALL DOCUMENTS
# =============================================================

@router.get("")
def list_documents(
    db: Session = Depends(get_db)
):
    documents = get_all_documents(db)

    return [
        {
            "id": document.id,
            "document_name": document.document_name,
            "document_type": document.document_type,
            "status": document.status,
            "created_at": document.created_at,
        }
        for document in documents
    ]


# =============================================================
# GET DOCUMENT BY NAME
# =============================================================

@router.get("/{document_name}")
def get_document(
    document_name: str,
    db: Session = Depends(get_db)
):
    document = get_document_by_name(db, document_name)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "id": document.id,
        "document_name": document.document_name,
        "document_type": document.document_type,
        "status": document.status,
        "created_at": document.created_at.isoformat()
        if document.created_at else None,
        "extraction": json.loads(document.extraction_json)
        if document.extraction_json else None,
        "validation": json.loads(document.validation_json)
        if document.validation_json else None,
        "ocr_text": document.ocr_text
    }