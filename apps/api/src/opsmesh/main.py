from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.opsmesh.api.routes.audit import router as audit_router
from src.opsmesh.api.routes.auth import router as auth_router
from src.opsmesh.api.routes.clusters import router as clusters_router
from src.opsmesh.api.routes.incidents import router as incidents_router
from src.opsmesh.api.routes.users import router as users_router
from src.opsmesh.core.redis import check_redis_health

app = FastAPI(
    title="OpsMesh API",
    description="AI-powered incident intelligence platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    redis_ok = await check_redis_health()
    return {
        "status": "healthy" if redis_ok else "degraded",
        "service": "opsmesh-api",
        "dependencies": {
            "redis": "connected" if redis_ok else "disconnected",
        },
    }


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(incidents_router)
app.include_router(clusters_router)
app.include_router(audit_router)
