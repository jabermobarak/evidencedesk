"""FastAPI app factory; importing this module does not create files or download models."""

import hmac
from importlib.resources import files

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from .config import Settings
from .schemas import Answer, Question
from .service import EvidenceService
from .store import Store


def create_app(settings=None):
    settings = settings or Settings.from_env()
    service = EvidenceService(Store(settings.database), settings)
    app = FastAPI(title="EvidenceDesk", version="0.1.0", description="Evidence-first document QA")
    app.state.service = service

    def authorize(request: Request):
        if settings.api_token:
            supplied = request.headers.get("Authorization", "")
            if not hmac.compare_digest(supplied.encode(), f"Bearer {settings.api_token}".encode()):
                raise HTTPException(status_code=401, detail="A valid bearer token is required")

    auth = [Depends(authorize)]

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path == "/":
            ancestors = ("https://colab.research.google.com https://*.googleusercontent.com"
                         if settings.allow_colab_embed else "'none'")
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                f"img-src 'self' data:; connect-src 'self'; frame-ancestors {ancestors}"
            )
        return response

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/api/config", dependencies=auth)
    def config():
        return {"embedding_model": settings.embedding_model or "TF-IDF (offline lexical baseline)",
                "llm_model": settings.llm_model or None, "max_upload_bytes": settings.max_upload_bytes}

    @app.get("/api/documents", dependencies=auth)
    def documents():
        return [{"id": d["id"], "title": d["title"], "pages": len(d["pages"]), "chars": d["chars"]}
                for d in service.store.documents()]

    @app.post("/api/documents", status_code=201, dependencies=auth)
    async def upload(file: UploadFile):
        try:
            payload = await file.read(settings.max_upload_bytes + 1)
        finally:
            await file.close()
        try:
            return await run_in_threadpool(service.add_file, file.filename or "document.txt", payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/documents/{ident}", dependencies=auth)
    def delete(ident: str):
        if not service.delete(ident):
            raise HTTPException(status_code=404, detail="Document not found")
        return {"deleted": ident}

    @app.post("/api/demo", dependencies=auth)
    def demo():
        try:
            return {"documents": service.load_demo()}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/ask", response_model=Answer, dependencies=auth)
    def ask(question: Question):
        try:
            return service.ask(question)
        except (ImportError, OSError, RuntimeError) as exc:
            raise HTTPException(status_code=503, detail="Retrieval backend could not initialize; check server logs and model configuration") from exc

    @app.get("/api/metrics", dependencies=auth)
    def metrics():
        return service.store.metrics()

    static = files("evidencedesk").joinpath("static")
    app.mount("/static", StaticFiles(directory=str(static)), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(str(static.joinpath("index.html")))

    return app
