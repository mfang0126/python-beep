# Detection endpoints
from fastapi import Request, HTTPException, UploadFile, File
from typing import Optional
import os
import io
from pathlib import Path

from ..models.responses import FindBeepsResponse, TemplateMatchResponse, GenerateReportResponse
from ..utils.audio import (
    validate_audio_file, load_audio_file, load_template_file, 
    format_mm_ss, frequency_detection, template_matching
)
from ..utils.config import get_settings, get_env_float, get_env_int, get_env_bool, get_env_optional_float
import logging

logger = logging.getLogger(__name__)

async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    template_available = os.path.exists(settings.default_template_path)
    
    return {
        "status": "healthy",
        "service": "Audio Beep Detection API",
        "version": "1.0.0",
        "template_available": template_available
    }

async def detect_frequency_beeps(request: Request):
    """Detect beeps using frequency analysis."""
    form = await request.form()
    file = form.get("file")
    
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    
    validate_audio_file(file)
    
    try:
        # Load audio
        y, sr = await load_audio_file(file)
        
        # Detect beeps
        timestamps = frequency_detection(y, sr)
        
        return FindBeepsResponse(
            filename=file.filename or "unknown",
            detected_beep_timestamps=timestamps,
            detected_beep_timestamps_mm_ss=[format_mm_ss(t) for t in timestamps],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in frequency detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

async def detect_template_matches(request: Request):
    """Detect beeps using template matching."""
    form = await request.form()
    file = form.get("file")
    
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    
    validate_audio_file(file)
    
    try:
        # Get parameters
        settings = get_settings()
        
        # Query parameters
        threshold = float(form.get("threshold", settings.beep_threshold))
        min_separation_s = float(form.get("min_separation_s", settings.beep_min_sep))
        sr_target = int(form.get("sr_target", settings.beep_sr))
        raw = form.get("raw", str(settings.beep_raw)).lower() == "true"
        
        # Load audio files
        y_target, _ = await load_audio_file(file, sr_target)
        y_template, template_name = load_template_file(settings.default_template_path, sr_target)
        
        # Detect matches
        times = template_matching(y_target, y_template, sr_target, threshold, min_separation_s, raw)
        
        return TemplateMatchResponse(
            filename=file.filename or "unknown",
            template=template_name,
            sr=sr_target,
            threshold=threshold,
            min_separation_s=min_separation_s,
            raw=raw,
            matches=times,
            matches_mm_ss=[format_mm_ss(t) for t in times],
            num_matches=len(times),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in template matching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

async def generate_report(request: Request):
    """Generate a text report of detected beeps."""
    form = await request.form()
    file = form.get("file")
    
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    
    validate_audio_file(file)
    
    try:
        # Get parameters
        settings = get_settings()
        
        # Query parameters
        threshold = float(form.get("threshold", settings.beep_threshold))
        min_separation_s = float(form.get("min_separation_s", settings.beep_min_sep))
        sr_target = int(form.get("sr_target", settings.beep_sr))
        raw = form.get("raw", str(settings.beep_raw)).lower() == "true"
        output_filename = form.get("output_filename", f"beeps_report_{'raw' if raw else 'ncc'}.txt")
        
        # Load audio files
        y_target, _ = await load_audio_file(file, sr_target)
        y_template, template_name = load_template_file(settings.default_template_path, sr_target)
        
        # Detect matches
        times = template_matching(y_target, y_template, sr_target, threshold, min_separation_s, raw)
        
        # Generate report
        if not output_filename.startswith("/"):
            output_filename = f"/tmp/{output_filename}"
        
        with open(output_filename, "w", encoding="utf-8") as w:
            w.write(f"filename={file.filename}\n")
            w.write(f"template={template_name}\n")
            w.write(f"raw={raw} threshold={threshold} min_separation_s={min_separation_s} sr={sr_target} band=[{settings.beep_band_low},{settings.beep_band_high}] smooth_ms={settings.beep_smooth_ms}\n")
            for t in times:
                w.write(format_mm_ss(t) + "\n")
        
        return GenerateReportResponse(
            output_path=output_filename,
            count=len(times),
            params={
                "raw": raw,
                "threshold": threshold,
                "min_separation_s": min_separation_s,
                "sr": sr_target,
                "band_low": settings.beep_band_low,
                "band_high": settings.beep_band_high,
                "smooth_ms": settings.beep_smooth_ms,
            },
            sample_first_5=[format_mm_ss(t) for t in times[:5]],
            sample_last_5=[format_mm_ss(t) for t in times[-5:]],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in report generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")