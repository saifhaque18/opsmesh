from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.opsmesh.api.routes.incidents import router as incidents_router

app = FastAPI(
    title="OpsMesh API",
    description="AI-powered incident intelligence platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "opsmesh-api"}


app.include_router(incidents_router)
