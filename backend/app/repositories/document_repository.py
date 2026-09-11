import json

from sqlalchemy.orm import Session

from backend.app.models.document import Document


def create_document(
    db: Session,
    document_name: str,
    document_type: str,
    status: str,
    extraction_data: dict,
    validation_data: dict,
    ocr_text: str,
):
    document = Document(
        document_name=document_name,
        document_type=document_type,
        status=status,
        extraction_json=json.dumps(extraction_data),
        validation_json=json.dumps(validation_data),
        ocr_text=ocr_text,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def get_all_documents(db: Session):
    return (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .all()
    )


def get_document_by_name(
    db: Session,
    document_name: str
):
    return (
        db.query(Document)
        .filter(Document.document_name == document_name)
        .first()
    )