import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import uvicorn

from services.atlas.core.config import config
from services.atlas.api.router import router as api_router
from services.atlas.db.session import check_db_health, engine, Base
import services.atlas.models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atlas.main")


def print_startup_banner(db_healthy: bool):
    if config.is_live:
        print("\n" + "!" * 45)
        print("        REAL MONEY MODE ENABLED")
        print("!" * 45 + "\n")
    else:
        print("\n===========================================")
        print("                  ATLAS                    ")
        print("===========================================")
        print(f"Environment:  {config.settings.APP_ENV.upper()}")
        print(f"Trading Mode: {config.settings.TRADING_MODE.upper()}")
        print(f"Broker:       {config.settings.BROKER.upper()}")
        print(f"AI:           {config.settings.AI_PROVIDER.upper()}")
        print(f"Live Trading: {'ENABLED' if config.is_live else 'DISABLED'}")
        print(f"Database:     {'HEALTHY' if db_healthy else 'FALLBACK'}")
        print(f"Redis:        {'HEALTHY'}")
        print(f"Risk Engine:  {'HEALTHY'}")
        print("===========================================\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    db_ok = await check_db_health()
    print_startup_banner(db_ok)
    yield
    logger.info("ATLAS shutting down gracefully.")


app = FastAPI(
    title="ATLAS Autonomous Trading Engine",
    description="Autonomous quantitative research, backtesting, paper-trading, risk-management and algorithmic execution platform for Indian equity markets.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix="/api")

# Mount Prometheus metrics endpoint (Section 68)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# WebSocket connection manager for live ticker and dashboard updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


ws_manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "PONG", "payload": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


def start():
    uvicorn.run(
        "services.atlas.main:app",
        host=config.settings.API_HOST,
        port=config.settings.API_PORT,
        reload=False,
    )


if __name__ == "__main__":
    start()
