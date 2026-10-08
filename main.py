import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers.scout import router as scout_router

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pravasi_trail")

# Initialize FastAPI application
app = FastAPI(title="PravasiTrail", version="1.0.0")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Scout router with /api prefix
app.include_router(scout_router)

# Ensure static directory exists
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

from fastapi.responses import FileResponse

@app.get("/trails")
async def get_trails():
    return FileResponse(STATIC_DIR / "trails.html")

@app.get("/weather")
async def get_weather():
    return FileResponse(STATIC_DIR / "weather.html")

@app.get("/mobus")
async def get_mobus():
    return FileResponse(STATIC_DIR / "mobus.html")

@app.get("/odia")
async def get_odia():
    return FileResponse(STATIC_DIR / "odia.html")

# Mount StaticFiles at root /
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
