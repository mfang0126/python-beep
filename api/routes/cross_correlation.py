# Lightweight cross-correlation detection using only SciPy
import io
import numpy as np
from fastapi import UploadFile, HTTPException, Request
from pathlib import Path
from typing import Tuple, Optional
from scipy.signal import correlate, find_peaks
import soundfile as sf
import logging

logger = logging.getLogger(__name__)

async def load_audio_lightweight(file: UploadFile, sr_target: int = 22050) -> Tuple[np.ndarray, int]:
    """Load audio file using soundfile only (no librosa)."""
    try:
        contents = await file.read()
        y, sr = sf.read(io.BytesIO(contents))
        
        # Resample if needed
        if sr != sr_target:
            # Simple linear interpolation for resampling
            original_length = len(y)
            target_length = int(original_length * sr_target / sr)
            y = np.interp(
                np.linspace(0, original_length, target_length),
                np.arange(original_length),
                y
            )
            sr = sr_target
        
        if y.size == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty.")
            
        return y, sr
    except Exception as e:
        logger.error(f"Error loading audio file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Cannot read audio file: {str(e)}")

def load_template_lightweight(template_path: str, sr_target: int = 22050) -> Tuple[np.ndarray, str]:
    """Load template audio file using soundfile only."""
    try:
        if not Path(template_path).exists():
            raise HTTPException(status_code=400, detail="Template file not found.")
            
        y_template, sr = sf.read(template_path)
        
        # Resample if needed
        if sr != sr_target:
            original_length = len(y_template)
            target_length = int(original_length * sr_target / sr)
            y_template = np.interp(
                np.linspace(0, original_length, target_length),
                np.arange(original_length),
                y_template
            )
            sr = sr_target
        
        template_name = Path(template_path).name
        
        if y_template.size == 0:
            raise HTTPException(status_code=400, detail="Template file is empty.")
            
        return y_template, template_name
    except Exception as e:
        logger.error(f"Error loading template file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Cannot read template file: {str(e)}")

def format_mm_ss(time_seconds: float) -> str:
    """Format time as MM:SS.mmm string."""
    if time_seconds is None or (isinstance(time_seconds, float) and np.isnan(time_seconds)):
        return "00:00.000"
    minutes = int(time_seconds // 60)
    seconds = time_seconds - minutes * 60
    return f"{minutes:02d}:{seconds:06.3f}"

def cross_correlation_detection(y_target: np.ndarray, y_template: np.ndarray, 
                              sr: int, threshold: float = 0.5, 
                              min_separation_s: float = 0.5) -> list:
    """Detect beeps using simple cross-correlation (lightweight version)."""
    try:
        min_dist = max(1, int(min_separation_s * sr))
        
        # Normalize signals
        y_target_norm = y_target.astype(np.float32)
        y_template_norm = y_template.astype(np.float32)
        
        # Remove DC component and normalize
        y_target_norm = y_target_norm - np.mean(y_target_norm)
        y_template_norm = y_template_norm - np.mean(y_template_norm)
        
        # Normalize amplitude
        target_rms = np.sqrt(np.mean(y_target_norm**2))
        template_rms = np.sqrt(np.mean(y_template_norm**2))
        
        if target_rms > 0:
            y_target_norm = y_target_norm / target_rms
        if template_rms > 0:
            y_template_norm = y_template_norm / template_rms
        
        # Compute cross-correlation
        correlation = correlate(y_target_norm, y_template_norm, mode='valid')
        
        # Find peaks
        correlation_threshold = threshold * np.max(correlation)
        peaks, properties = find_peaks(correlation, height=correlation_threshold, distance=min_dist)
        
        # Convert to time
        times = (peaks / float(sr)).tolist()
        
        return times
    except Exception as e:
        logger.error(f"Error in cross-correlation detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cross-correlation failed: {str(e)}")

async def detect_cross_correlation_beeps(request: Request):
    """Detect beeps using lightweight cross-correlation (SciPy only)."""
    form = await request.form()
    file = form.get("file")
    
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    
    # Simple validation
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Please upload an audio file.")
    
    try:
        # Get parameters
        threshold = float(form.get("threshold", 0.5))
        min_separation_s = float(form.get("min_separation_s", 0.5))
        sr_target = int(form.get("sr_target", 22050))
        
        # Load audio files (lightweight version)
        y_target, _ = await load_audio_lightweight(file, sr_target)
        y_template, template_name = await load_template_lightweight("static/beep_template.wav", sr_target)
        
        # Detect beeps using cross-correlation
        times = cross_correlation_detection(y_target, y_template, sr_target, threshold, min_separation_s)
        
        return {
            "filename": file.filename or "unknown",
            "template": template_name,
            "sr": sr_target,
            "threshold": threshold,
            "min_separation_s": min_separation_s,
            "method": "cross_correlation",
            "matches": times,
            "matches_mm_ss": [format_mm_ss(t) for t in times],
            "num_matches": len(times),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in cross-correlation detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")