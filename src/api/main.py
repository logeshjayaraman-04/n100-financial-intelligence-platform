import logging
import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.companies import router as companies_router
from src.api.routers.screener import router as screener_router
from src.api.routers.sectors import router as sectors_router
from src.api.routers.peers import router as peers_router
from src.api.routers.valuation import router as valuation_router
from src.api.routers.portfolio import router as portfolio_router
from src.api.routers.documents import router as documents_router


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "db" / "n100.db"

VERSION = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="N100 Financial Intelligence Platform API",
    description=(
        "REST API for N100 financial intelligence, screening, "
        "sectors, peers, valuation, portfolio statistics, and documents."
    ),
    version=VERSION,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    elapsed = time.perf_counter() - start

    logger.info(
        "%s %s -> %s (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )

    return response


def get_db_row_counts():
    tables = [
        "companies",
        "financial_ratios",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "sectors",
        "peer_groups",
        "peer_percentiles",
        "market_cap",
        "prosandcons",
    ]

    counts = {}

    conn = sqlite3.connect(DB_PATH)

    try:
        for table in tables:
            row = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()

            counts[table] = row[0]

    finally:
        conn.close()

    return counts


@app.get("/api/v1/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "version": VERSION,
        "db_row_counts": get_db_row_counts(),
        "uptime": "running",
    }


app.include_router(
    companies_router,
    prefix="/api/v1/companies",
)

app.include_router(
    screener_router,
    prefix="/api/v1",
)

app.include_router(
    sectors_router,
    prefix="/api/v1",
)

app.include_router(
    peers_router,
    prefix="/api/v1",
)

app.include_router(
    valuation_router,
    prefix="/api/v1",
)

app.include_router(
    portfolio_router,
    prefix="/api/v1",
)

app.include_router(
    documents_router,
    prefix="/api/v1",
)