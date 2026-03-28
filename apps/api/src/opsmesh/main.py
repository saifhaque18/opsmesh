from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/api/v1/incidents")
async def list_incidents():
    """Placeholder — will be replaced with real DB queries in Week 2."""
    return {
        "incidents": [],
        "total": 0,
        "message": "Incident ingestion coming in Week 2",
    }
