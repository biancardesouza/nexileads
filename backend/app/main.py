import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, leads, novos_leads

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NexiLeads API")

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def adicionar_headers_seguranca(request: Request, call_next):
    """Headers básicos de hardening HTTP — o navegador só aplica HSTS de
    verdade sobre HTTPS, então em dev local (HTTP) ele é ignorado, sem efeito
    colateral."""
    resposta = await call_next(request)
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "DENY"
    resposta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resposta.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return resposta


app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(novos_leads.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
