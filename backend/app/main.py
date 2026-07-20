from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import admin, auth, leads, novos_leads
from .routers.auth import UPLOAD_DIR

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Faro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(novos_leads.router)
app.include_router(admin.router)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
