# Vercel Main Entry Point
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from routes.detect import detect_frequency_beeps, detect_template_matches, generate_report
from routes.health import health_check
from utils.config import get_settings
from utils.audio import validate_audio_file

# Initialize FastAPI app
app = FastAPI(
    title="Audio Beep Detection API - Vercel",
    description="FastAPI-based audio processing service deployed on Vercel"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration
settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/api/health")
async def health():
    return await health_check()

# Legacy health check for backward compatibility
@app.get("/")
async def root():
    return await health_check()

# API Routes
@app.post("/api/detect-frequency-beeps")
async def api_detect_frequency_beeps(request: Request):
    """
    Detect beeps using frequency analysis.
    """
    try:
        return await detect_frequency_beeps(request)
    except Exception as e:
        logger.error(f"Error in frequency detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/api/detect-template-matches")
async def api_detect_template_matches(request: Request):
    """
    Detect beeps using template matching.
    """
    try:
        return await detect_template_matches(request)
    except Exception as e:
        logger.error(f"Error in template matching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/api/generate-report")
async def api_generate_report(request: Request):
    """
    Generate a text report of detected beeps.
    """
    try:
        return await generate_report(request)
    except Exception as e:
        logger.error(f"Error in report generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

# Legacy route support for backward compatibility
@app.post("/detect-frequency-beeps/")
async def legacy_detect_frequency_beeps(request: Request):
    return await api_detect_frequency_beeps(request)

@app.post("/detect-template-matches/")
async def legacy_detect_template_matches(request: Request):
    return await api_detect_template_matches(request)

@app.post("/generate-report/")
async def legacy_generate_report(request: Request):
    return await api_generate_report(request)

# Error handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found. Available endpoints: /api/health, /api/detect-frequency-beeps, /api/detect-template-matches, /api/generate-report"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

# For Vercel serverless function
handler = app