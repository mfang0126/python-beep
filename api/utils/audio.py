# Audio processing utilities
import io
import os
import librosa
import numpy as np
from fastapi import UploadFile, HTTPException, Request
from pathlib import Path
from typing import Tuple, Optional
from scipy.signal import butter, filtfilt, fftconvolve, find_peaks, correlate
import logging

logger = logging.getLogger(__name__)

def validate_audio_file(file: UploadFile) -> bool:
    """Validate uploaded file is an audio file."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Please upload an audio file.")
    return True

async def load_audio_file(file: UploadFile, sr_target: int = 22050) -> Tuple[np.ndarray, int]:
    """Load audio file from upload."""
    try:
        contents = await file.read()
        y, sr = librosa.load(io.BytesIO(contents), sr=sr_target)
        
        if y.size == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty.")
            
        return y, sr
    except Exception as e:
        logger.error(f"Error loading audio file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Cannot read audio file: {str(e)}")

def load_template_file(template_path: str, sr_target: int = 22050) -> Tuple[np.ndarray, str]:
    """Load template audio file."""
    try:
        if not os.path.exists(template_path):
            raise HTTPException(status_code=400, detail="Template file not found.")
            
        y_template, sr = librosa.load(template_path, sr=sr_target)
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

def frequency_detection(y: np.ndarray, sr: int) -> list:
    """Detect beeps using frequency analysis."""
    try:
        # STFT parameters
        n_fft = 4096
        hop_length = n_fft // 4
        
        # Frequency analysis
        D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
        
        # Target frequency range
        target_freq_low = 1100
        target_freq_high = 1300
        target_freq_indices = np.where((freqs >= target_freq_low) & (freqs <= target_freq_high))[0]
        
        # Energy calculation
        energy_at_target_freq = np.sum(np.abs(D[target_freq_indices, :]), axis=0)
        threshold = np.mean(energy_at_target_freq) * 5
        
        # Peak detection
        beep_frames = np.where(energy_at_target_freq > threshold)[0]
        
        # Group consecutive frames
        if len(beep_frames) > 0:
            beep_groups = np.split(beep_frames, np.where(np.diff(beep_frames) != 1)[0] + 1)
            first_beep_frames = [group[0] for group in beep_groups]
        else:
            first_beep_frames = []
        
        # Convert to time
        beep_timestamps = librosa.frames_to_time(first_beep_frames, sr=sr, hop_length=hop_length)
        
        return beep_timestamps.tolist()
    except Exception as e:
        logger.error(f"Error in frequency detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Frequency detection failed: {str(e)}")

def template_matching(y_target: np.ndarray, y_template: np.ndarray, sr: int, 
                       threshold: float = 0.6, min_separation_s: float = 0.5, 
                       raw: bool = False) -> list:
    """Detect beeps using template matching."""
    try:
        min_dist = max(1, int(min_separation_s * sr))
        
        if raw:
            # Raw waveform correlation
            x = y_target.astype(np.float32)
            h = y_template.astype(np.float32)
            x /= (np.max(np.abs(x)) + 1e-8)
            h /= (np.max(np.abs(h)) + 1e-8)
            corr = correlate(x, h, mode='valid')
            height = float(threshold) * float(np.max(corr) if corr.size > 0 else 1.0)
            peaks, _ = find_peaks(corr, height=height, distance=min_dist)
            times = (peaks / float(sr)).tolist()
        else:
            # NCC mode with band-pass filtering
            nyq = 0.5 * sr
            band_low = 1100.0
            band_high = 1300.0
            low = max(1.0, band_low) / nyq
            high = min(sr/2 - 100.0, band_high) / nyq
            
            if not (0 < low < high < 1):
                raise HTTPException(status_code=400, detail="Invalid frequency band settings.")
            
            # Band-pass filter
            b, a = butter(N=4, Wn=[low, high], btype='band')
            
            def envelope(sig: np.ndarray) -> np.ndarray:
                if sig.ndim > 1:
                    sig = np.mean(sig, axis=1)
                fil = filtfilt(b, a, sig)
                env = np.abs(fil)
                win = max(1, int(sr * (10.0 / 1000.0)))  # 10ms smoothing
                kernel = np.ones(win, dtype=np.float32) / float(win)
                sm = fftconvolve(env, kernel, mode='same')
                return sm.astype(np.float32)
            
            env_target = envelope(y_target)
            env_tmpl = envelope(y_template)
            
            L = env_tmpl.size
            if L < 10:
                raise HTTPException(status_code=400, detail="Template too short.")
            if env_target.size <= L:
                raise HTTPException(status_code=400, detail="Target audio too short.")
            
            # Normalized cross-correlation
            tmpl_energy = float(np.sum(env_tmpl ** 2))
            if tmpl_energy == 0.0:
                raise HTTPException(status_code=400, detail="Template energy is zero.")
            
            numerator = fftconvolve(env_target, env_tmpl[::-1], mode='valid')
            ones = np.ones(L, dtype=np.float32)
            target_energy = fftconvolve(env_target.astype(np.float32) ** 2, ones, mode='valid')
            denom = np.sqrt(target_energy * tmpl_energy) + 1e-8
            ncc = numerator / denom
            
            peaks, _ = find_peaks(ncc, height=threshold, distance=min_dist)
            times = (peaks / float(sr)).tolist()
        
        return times
    except Exception as e:
        logger.error(f"Error in template matching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Template matching failed: {str(e)}")