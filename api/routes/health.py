# Health check endpoints
from fastapi import Request
import os
from ..utils.config import get_settings
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