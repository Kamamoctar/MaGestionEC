from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, utilisateurs, directions, postes, courriers, flux, bpmn

app = FastAPI(
    title="GEC — Gestion Électronique des Courriers",
    version="0.1.0",
    description="API REST pour la gestion électronique des courriers (PWA autonome).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(utilisateurs.router)
app.include_router(directions.router)
app.include_router(postes.router)
app.include_router(courriers.router)
app.include_router(flux.router)
app.include_router(bpmn.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
