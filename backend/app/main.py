"""FastAPI application for Bangla Fake News Detector."""

import hashlib
import json
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Literal

from fastapi import FastAPI, Request, HTTPException, Security, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.app.model import BanglaFakeNewsModel
from backend.app.preprocess import bangla_ratio, count_words
from backend.app.settings import settings


# Configure privacy-safe logging: NO article text in logs
logger = logging.getLogger("fake_news_api")
logger.setLevel(logging.INFO)
# Clear existing handlers if any to avoid duplication
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# State containers
ml_model: Optional[BanglaFakeNewsModel] = None
band_cutoffs: dict = {"strong_cutoff": 0.70, "some_cutoff": 0.40}


def load_bands():
    global band_cutoffs
    bands_path = Path(settings.bands_file)
    if bands_path.exists():
        with open(bands_path, "r", encoding="utf-8") as f:
            band_cutoffs = json.load(f)
    else:
        logger.warning(f"bands.json not found at {bands_path}, using defaults")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ml_model
    load_bands()
    model_dir = Path(settings.model_dir)
    if model_dir.exists() and (model_dir / "config.json").exists():
        logger.info(f"Loading model from {model_dir}")
        ml_model = BanglaFakeNewsModel(model_dir)

        # Check threshold parity with bands.json
        threshold = ml_model.threshold_fake
        some_cutoff = float(band_cutoffs.get("some_cutoff", 0.40))
        if abs(threshold - some_cutoff) > 1e-4:
            logger.warning(
                f"Warning: threshold_fake ({threshold}) differs from some_cutoff ({some_cutoff}) in bands.json!"
            )
    else:
        logger.warning(f"Model directory not found or incomplete at {model_dir}")

    yield


# Rate Limiter setup
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# CORS setup
origins = [orig.strip() for orig in settings.cors_allowed_origins.split(",") if orig.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security: Optional API Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    if settings.api_key:
        if not api_key or api_key != settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key"
            )
    return api_key


# Custom error handlers ensuring privacy & status code specifications
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Malformed JSON or missing fields"}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Internal server error encountered", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "The analysis server returned an error. Try again later."}
    )


# Request and Response schemas
class PredictRequest(BaseModel):
    headline: str = Field(default="", description="Headline of article (can be empty)")
    content: str = Field(..., min_length=1, description="Body content of article (must be non-empty)")


class PredictResponse(BaseModel):
    band: Literal["strong", "some", "none", "too_short", "not_bangla"]
    p_fake: Optional[float]
    threshold: float
    model_version: str
    word_count: int
    truncated: bool
    latency_ms: int


@app.get("/health")
async def health():
    model_version = ml_model.model_version if ml_model else "v1"
    threshold = ml_model.threshold_fake if ml_model else 0.40
    return {
        "status": "ok",
        "model_version": model_version,
        "threshold": threshold
    }


@app.post("/predict", response_model=PredictResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def predict(
    request: Request,
    payload: PredictRequest,
    api_key: Optional[str] = Security(verify_api_key)
):
    start_time = time.perf_counter()

    headline = payload.headline or ""
    content = payload.content

    # Character count limit check: HTTP 413 when headline + content is over 20,000 characters
    total_chars = len(headline) + len(content)
    if total_chars > 20000:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Payload exceeds maximum length of 20,000 characters"
        )

    # Word count on content
    words_in_content = count_words(content)

    # Hash for logging and privacy (SHA-256)
    combined_raw = f"{headline}\n{content}".encode("utf-8")
    content_sha256 = hashlib.sha256(combined_raw).hexdigest()

    threshold = ml_model.threshold_fake if ml_model else 0.40
    model_ver = ml_model.model_version if ml_model else "v1"

    # Rule 1: not_bangla: fewer than 50% of the letters in headline + content are Bangla
    ratio = bangla_ratio(f"{headline} {content}")
    if ratio < 0.50:
        latency = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            f"sha256={content_sha256} score=null band=not_bangla latency_ms={latency} status=200"
        )
        return PredictResponse(
            band="not_bangla",
            p_fake=None,
            threshold=threshold,
            model_version=model_ver,
            word_count=words_in_content,
            truncated=False,
            latency_ms=latency
        )

    # Rule 2: too_short: fewer than 40 words in content
    if words_in_content < 40:
        latency = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            f"sha256={content_sha256} score=null band=too_short latency_ms={latency} status=200"
        )
        return PredictResponse(
            band="too_short",
            p_fake=None,
            threshold=threshold,
            model_version=model_ver,
            word_count=words_in_content,
            truncated=False,
            latency_ms=latency
        )

    # Rule 3: Run model and determine band
    if ml_model is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model is not initialized"
        )

    p_fake, truncated = ml_model.predict(headline, content)

    strong_cutoff = float(band_cutoffs.get("strong_cutoff", 0.70))
    some_cutoff = float(band_cutoffs.get("some_cutoff", 0.40))

    if p_fake >= strong_cutoff:
        band = "strong"
    elif p_fake >= some_cutoff:
        band = "some"
    else:
        band = "none"

    latency = int((time.perf_counter() - start_time) * 1000)
    logger.info(
        f"sha256={content_sha256} score={p_fake:.4f} band={band} latency_ms={latency} status=200"
    )

    return PredictResponse(
        band=band,
        p_fake=p_fake,
        threshold=threshold,
        model_version=model_ver,
        word_count=words_in_content,
        truncated=truncated,
        latency_ms=latency
    )

