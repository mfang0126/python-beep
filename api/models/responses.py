# Response models
from pydantic import BaseModel, Field
from typing import List, Optional

class FindBeepsResponse(BaseModel):
    filename: str
    detected_beep_timestamps: List[float] = Field(..., description="Detected timestamps (seconds)")
    detected_beep_timestamps_mm_ss: List[str] = Field(..., description="Detected timestamps (MM:SS.mmm)")

class TemplateMatchResponse(BaseModel):
    filename: str
    template: str
    sr: int
    threshold: float
    min_separation_s: float
    raw: bool
    matches: List[float]
    matches_mm_ss: List[str]
    num_matches: int

class GenerateReportResponse(BaseModel):
    output_path: str
    count: int
    params: dict
    sample_first_5: List[str]
    sample_last_5: List[str]

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    template_available: bool