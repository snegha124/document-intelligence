\# Document Intelligence System



AI-powered document intelligence system for extracting information from invoices and financial statements.



\## Supported Documents



\- Invoice

\- Balance Sheet

\- Profit \& Loss

\- Cash Flow



\## Features



\- PDF, JPG, JPEG and PNG document support

\- PDF validation with a maximum of 3 pages

\- OCR for scanned/image-based documents

\- AI-powered structured information extraction

\- Financial consistency validation

\- SQLite database persistence

\- REST API with Swagger/OpenAPI documentation

\- Web-based dashboard

\- Document result visualization

\- Automated tests



\## Technology Stack



\- Python

\- FastAPI

\- SQLAlchemy

\- SQLite

\- Tesseract OCR

\- PyMuPDF

\- Pillow

\- Google Gemini API

\- HTML

\- CSS

\- JavaScript

\- Pytest



\## Project Structure



```text

document-intelligence/

├── backend/

│   ├── app/

│   │   ├── api/

│   │   ├── core/

│   │   ├── models/

│   │   ├── repositories/

│   │   ├── schemas/

│   │   ├── services/

│   │   └── main.py

│   │

│   ├── tests/

│   └── requirements.txt

│

├── frontend/

│   ├── templates/

│   └── static/

│

├── dataset/

│

├── sample\_outputs/

│

├── docs/

│

├── README.md

└── document\_intelligence.db

