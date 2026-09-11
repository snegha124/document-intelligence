from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.document import Document


client = TestClient(app)


def create_test_document():
    db = SessionLocal()

    # Remove an older test record if it exists
    db.query(Document).filter(
        Document.document_name == "api_test_document.jpg"
    ).delete()

    document = Document(
        document_name="api_test_document.jpg",
        document_type="Invoice",
        status="processed",
        extraction_json='{"document_type": "Invoice"}',
        validation_json='{"overall_status": "passed"}',
        ocr_text="API test OCR text"
    )

    db.add(document)
    db.commit()
    db.close()


def remove_test_document():
    db = SessionLocal()

    db.query(Document).filter(
        Document.document_name == "api_test_document.jpg"
    ).delete()

    db.commit()
    db.close()


def test_health_endpoint():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_list_documents():
    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_existing_document():
    create_test_document()

    try:
        response = client.get(
            "/api/v1/documents/api_test_document.jpg"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["document_name"] == "api_test_document.jpg"
        assert data["document_type"] == "Invoice"
        assert data["status"] == "processed"

        assert data["extraction"]["document_type"] == "Invoice"
        assert data["validation"]["overall_status"] == "passed"

    finally:
        remove_test_document()


def test_get_missing_document():
    response = client.get(
        "/api/v1/documents/document_that_does_not_exist.jpg"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Document not found"


def test_invalid_file_type():
    response = client.post(
        "/api/v1/documents/process",
        data={
            "document_type": "Invoice"
        },
        files={
            "file": (
                "test.txt",
                b"This is not a supported document.",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert "Unsupported file type" in data["detail"]