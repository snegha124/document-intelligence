# Document Intelligence System

AI-powered document intelligence system for extracting, validating and storing information from invoices and financial statements.

Live Application

Live Dashboard: https://document-intelligence-4mck.onrender.com

API Health: https://document-intelligence-4mck.onrender.com/api/v1/health

Swagger / OpenAPI: https://document-intelligence-4mck.onrender.com`/docs`

GitHub Repository: https://github.com/snegha124/document-intelligence

# Overview

The Document Intelligence System processes financial documents and converts their visible information into structured JSON data.

The application supports:

Invoice

Balance Sheet

Profit & Loss

Cash Flow

The system combines document validation, PDF/image processing, OCR, AI-based extraction, financial validation and database persistence.

Supported Documents

Invoice

Extracts information such as:

Invoice number

Invoice date

Due date

Vendor

Customer

Currency

Line items

Quantity

Unit price

Line total

Subtotal

Tax

Discount

Total

Payment/change information where present

Balance Sheet

Extracts:

Company name

Statement date

Currency

Unit

Assets

Liabilities

Equity

Line items

Total assets

Comparative-period values where present

Profit & Loss

Extracts:

Statement date

Currency

Unit

Income items

Expense items

Total income

Total expenses

Profit before minority interest

Minority interest

Attributable group profit

Comparative-period values

Other reported fields where present

Cash Flow

Extracts:

Statement date

Currency

Unit

Operating activities

Investing activities

Financing activities

Foreign exchange effect

Net cash change

Opening cash

Closing cash

Comparative-period values where present

Features

PDF, JPG, JPEG and PNG support

PDF validation with a maximum of 3 pages

Readability and file validation

OCR for scanned/image-based documents

Native PDF text extraction where available

AI-powered structured information extraction

Document-specific extraction schemas

Financial consistency validation

SQLite database persistence

REST API

Swagger/OpenAPI documentation

Web-based dashboard

Document result visualization

Latest-result retrieval for duplicate document names

Automated tests

Environment-variable based API key configuration

# Architecture

The main processing flow is:

User

|

v

Web Dashboard

|

v

FastAPI REST API

|

+--> File Validation

|

+--> PDF/Image Processing

\|       |

\|       +--> PyMuPDF

\|       +--> Pillow

\|       +--> Tesseract OCR

|

+--> Gemini AI Extraction

|

+--> Financial Validation

|

+--> SQLite Database

|

v

Structured JSON Result

|

v

Dashboard / REST API

# A visual architecture diagram is available at:

docs/architecture.png

## Technology Stack

Technology  Purpose

Python  Application development

FastAPI REST API backend

SQLAlchemy  Database ORM

SQLite  Prototype persistence

PyMuPDF PDF processing and native text extraction

Pillow  Image processing

Tesseract OCR   OCR for scanned/image documents

Google Gemini API   AI-based structured extraction

HTML    Frontend structure

CSS Frontend styling

JavaScript  Frontend interaction

Pytest  Automated testing

Render  Deployment

## Why These Technologies

FastAPI

FastAPI provides a lightweight Python REST API with automatic Swagger/OpenAPI documentation.

PyMuPDF

PyMuPDF is used to read PDF documents and extract native PDF text when available.

Tesseract OCR

Tesseract is used when documents contain scanned or image-based content that cannot be reliably read through native PDF text extraction.

Google Gemini

Gemini is used for document understanding and structured extraction of financial information from document content.

SQLAlchemy + SQLite

SQLAlchemy provides a clean database abstraction layer. SQLite keeps the prototype simple while still providing persistent structured storage during normal application operation.

HTML/CSS/JavaScript

A simple frontend was selected instead of a separate React application because the case study does not require a separate frontend framework.

## Document Processing

The application first validates the uploaded document.

For PDFs:

The PDF is opened and checked.

Each page is inspected for native text.

Native text is used when sufficient text is available.

OCR is used for pages that require image-based extraction.

The extracted content is passed to the document-specific AI extraction process.

For JPG/PNG/JPEG files:

The image is opened.

OCR is performed.

The OCR content is passed to the extraction process.

## AI Extraction

Google Gemini is used to convert document content into structured application schemas.

The extraction process is document-specific so that invoices and financial statements use different fields and validation rules.

The extraction instructions emphasize:

Extracting visible information from the document

Preserving financial values

Including comparative-period values where available

Returning null when information is missing

Avoiding invented values

Preserving meaningful financial line items

## Financial Validation

Financial validation is performed after extraction.

### Validation Tolerance

The application uses:

Absolute tolerance: 0.05

Relative tolerance: 0.5%

### Invoice Validation

The application checks relationships such as:

Quantity × Unit Price ≈ Line Total

and:

Subtotal + Tax − Discount ≈ Total

### Balance Sheet Validation

The application checks relationships such as:

Assets ≈ Liabilities + Equity

It also checks applicable line-item sums and reported totals.

### Profit & Loss Validation

The application checks:

Income components ≈ Total Income

Expense components ≈ Total Expenses

and applicable profit relationships, including minority interest and attributable group profit.

### Cash Flow Validation

The application checks:

Operating + Investing + Financing + FX ≈ Net Cash Change

and applicable opening/closing cash relationships.

Validation is performed independently for relevant reporting periods.

## REST API

### Process Document

POST /api/v1/documents/process

Uploads and processes a document.

### List Documents

GET /api/v1/documents

Returns persisted processed documents.

### Get Latest Result

GET /api/v1/documents/{document_name}

Returns the latest stored result for a document name when duplicate document names exist.

### Health Check

GET /api/v1/health

Returns API health information.

### Swagger

/docs

FastAPI automatically provides the interactive Swagger/OpenAPI interface.

Example API Response Structure

A processed document result contains information similar to:

{

"document_name": "example.pdf",

"document_type": "balance_sheet",

"status": "processed",

"extraction": {},

"validation": {}

}

The exact extraction fields depend on the document type.

## Database

The application uses SQLAlchemy with SQLite.

Stored information includes:

Document name

Document type

Processing status

Extraction JSON

Validation JSON

OCR text

Creation timestamp

The database model is located in:

backend/app/models/document.py

## Project Structure

**

document-intelligence/

```text

│

├── backend/

│   ├── app/

│   │   ├── api/

│   │   ├── core/

│   │   ├── models/

│   │   ├── repositories/

│   │   ├── schemas/

│   │   ├── services/

│   │   └── main.py

│   │

│   ├── tests/

│   └── requirements.txt

│

├── frontend/

│   ├── templates/

│   └── static/

│

├── sample_outputs/

│   ├── invoice.json

│   ├── balance_sheet.json

│   ├── profit_loss.json

│   └── cash_flow.json

│

├── docs/

│   ├── architecture.png

│   └── solution_presentation.pdf

│

├── README.md

├── .env.example

└── .gitignore

Sample Outputs

Example structured JSON outputs are included in:

sample_outputs/

Files included:

sample_outputs/invoice.json

sample_outputs/balance_sheet.json

sample_outputs/profit_loss.json

sample_outputs/cash_flow.json

Local Setup

Clone the repository

git clone https://github.com/snegha124/document-intelligence.git

cd document-intelligence

Create a virtual environment

Windows:

python -m venv venv

Activate:

.\venv\Scripts\Activate.ps1

Install dependencies

pip install -r backend/requirements.txt

Configure environment variables

Create a .env file or configure the environment variable:

GEMINI_API_KEY=your_gemini_api_key

The API key must not be committed to GitHub.

.env.example is provided as a template.

Run the application

uvicorn backend.app.main:app --reload

The application will be available at:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000`/docs`

Environment Variables

Variable    Purpose

GEMINI_API_KEY  Google Gemini API authentication

TESSERACT_CMD   Optional Tesseract executable path

Secrets should be configured through environment variables and should never be committed to source control.

Testing

Run the automated tests with:

pytest -q

The current test suite passes successfully with:

15 passed

The test suite covers core processing, extraction/validation behavior and API-related functionality.

Dataset

The development dataset contains financial statement PDFs and invoice images used to test the document-processing workflow.

The dataset is intentionally excluded from the public repository through .gitignore.

Deployment

The application is deployed on Render.

Live Dashboard

https://document-intelligence-4mck.onrender.com

Health Endpoint

https://document-intelligence-4mck.onrender.com/api/v1/health

Swagger

https://document-intelligence-4mck.onrender.com`/docs`

The deployment uses:

Build Command:

pip install -r backend/requirements.txt

and:

Start Command:

uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT

Security

API credentials are stored as environment variables.

Secrets are not included in source code.

.env files are excluded using .gitignore.

Local database files are excluded from Git.

Development datasets are excluded from Git.

Production deployments should use managed secret storage.

Known Limitations

SQLite is appropriate for the prototype but is not the preferred database for a production multi-instance deployment.

OCR accuracy depends on document quality, scan quality, resolution and layout.

Complex financial tables may require more specialized table extraction techniques.

LLM extraction can require confidence thresholds and human review for high-risk financial workflows.

The prototype does not implement full authentication and authorization.

Large document processing would benefit from asynchronous/background job processing.

Production Improvements

For a production version, the following improvements are recommended:

Replace SQLite with managed PostgreSQL.

Add authentication and role-based authorization.

Add rate limiting and request protection.

Add structured logging and monitoring.

Add background job processing for large documents.

Add document/file security scanning.

Add stronger table extraction and layout-aware document parsing.

Add extraction confidence thresholds.

Add human review for low-confidence financial results.

Version AI prompts and extraction schemas.

Add a larger labeled regression-test dataset.

Add encrypted object storage for uploaded documents.

Add centralized observability and alerting.

AI Assistant Usage Declaration

AI assistants were used during development for:

Coding assistance

Debugging

Architecture discussion

Extraction prompt development

Validation logic discussion

Documentation preparation

Presentation preparation

The implemented system and its architecture, OCR workflow, extraction prompts, validation rules, API design and deployment configuration should be understood and explainable by the candidate.

Deliverables

The repository includes:

Public GitHub repository

Live deployed application

REST API

Swagger/OpenAPI documentation

Architecture diagram

Solution presentation

Sample JSON outputs

README documentation

Automated tests

Environment-variable configuration

License

This project was created as an AI Engineer Internship case-study implementation.