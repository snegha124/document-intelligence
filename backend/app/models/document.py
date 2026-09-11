from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from backend.app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    document_name = Column(
        String(255),
        nullable=False,
        index=True
    )

    document_type = Column(
        String(100),
        nullable=False
    )

    status = Column(
        String(50),
        nullable=False,
        default="processed"
    )

    extraction_json = Column(
        Text,
        nullable=True
    )

    validation_json = Column(
        Text,
        nullable=True
    )

    ocr_text = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )