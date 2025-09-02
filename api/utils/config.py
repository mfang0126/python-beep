# Configuration utilities
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Detection Parameters
    beep_threshold: float = 0.6
    beep_min_sep: float = 0.5
    beep_sr: int = 22050
    beep_raw: bool = False
    
    # Signal Processing Parameters
    beep_band_low: float = 1100.0
    beep_band_high: float = 1300.0
    beep_smooth_ms: float = 10.0
    
    # Time Range Filtering
    beep_start_s: Optional[float] = None
    beep_end_s: Optional[float] = None
    
    # File Paths
    default_template_path: str = "/var/task/static/beep_template.wav"
    
    class Config:
        env_prefix = "BEEP_"
        case_sensitive = False

def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

def get_env_float(name: str, default_value: float) -> float:
    """Get float environment variable."""
    try:
        return float(os.getenv(name, default_value))
    except Exception:
        return default_value

def get_env_int(name: str, default_value: int) -> int:
    """Get integer environment variable."""
    try:
        return int(os.getenv(name, default_value))
    except Exception:
        return default_value

def get_env_bool(name: str, default_value: bool) -> bool:
    """Get boolean environment variable."""
    val = os.getenv(name)
    if val is None:
        return default_value
    return str(val).lower() in {"1", "true", "yes", "on"}

def get_env_optional_float(name: str) -> Optional[float]:
    """Get optional float environment variable."""
    val = os.getenv(name)
    if val is None or val == "":
        return None
    try:
        return float(val)
    except Exception:
        return None