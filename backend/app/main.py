from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, leads, novos_leads

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NexiLeads API")

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


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
