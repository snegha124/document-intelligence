from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.database import Base, engine
from backend.app.models.document import Document
from backend.app.api.routes.documents import router as documents_router


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Document Intelligence API",
    version="1.0.0",
    description="AI-powered document intelligence system"
)


# Serve frontend static files
app.mount(
    "/static",
    StaticFiles(directory="frontend/static"),
    name="static"
)


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse("frontend/templates/dashboard.html")


@app.get("/document-result.html", include_in_schema=False)
def document_result():
    return FileResponse("frontend/templates/document_result.html")


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Document Intelligence API is running"
    }


app.include_router(documents_router)