from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx

# Import your settings, database init, and routers
from core.config import settings
from core.database import init_db
from modules.router import router as backend_router
# from app.modules.simulator.router import router as simulator_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    await init_db()
    
    app.state.http_client = httpx.AsyncClient(
        base_url=settings.qkd_api_url,
        timeout=10.0
    )
    
    yield
        
    await app.state.http_client.aclose()

app = FastAPI(
    title="QKD Voting API", 
    lifespan=lifespan
)

app.include_router(backend_router)
