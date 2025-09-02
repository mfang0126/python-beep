# Audio Beep Detection API Documentation

## Overview
FastAPI-based audio processing service that detects beep sounds in audio files using two distinct methods: frequency analysis and template matching.

## Base URL
```
http://localhost:8000
```

## Authentication
No authentication required.

## Response Format
All endpoints return JSON responses with appropriate HTTP status codes.

## Error Handling
- `400 Bad Request`: Invalid file type, missing template, or invalid parameters
- `500 Internal Server Error`: Audio processing failures

---

## API Endpoints

### 1. Detect Frequency Beeps
**POST** `/detect-frequency-beeps/`

Detects beep sounds using frequency band energy analysis.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: `file` (audio file)

**Response Model:**
```json
{
  "filename": "string",
  "detected_beep_timestamps": [number],
  "detected_beep_timestamps_mm_ss": ["string"]
}
```

**Description:**
- Analyzes audio using Short-Time Fourier Transform (STFT)
- Detects energy spikes in 1100-1300 Hz frequency range
- Uses dynamic threshold (5x average energy)
- Groups consecutive detections to avoid duplicates

**Example Response:**
```json
{
  "filename": "test_audio.mp3",
  "detected_beep_timestamps": [1.234, 5.678, 10.123],
  "detected_beep_timestamps_mm_ss": ["00:01.234", "00:05.678", "00:10.123"]
}
```

---

### 2. Detect Template Matches
**POST** `/detect-template-matches/`

Detects beep sounds using template matching with cross-correlation.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: 
  - `file` (audio file)
  - Optional query parameters (see Configuration)

**Response Model:**
```json
{
  "filename": "string",
  "template": "string",
  "sr": 22050,
  "threshold": 0.6,
  "min_separation_s": 0.5,
  "raw": false,
  "matches": [number],
  "matches_mm_ss": ["string"],
  "num_matches": 3
}
```

**Description:**
- Uses `beep_template.wav` as reference pattern
- Two processing modes:
  - **Raw Mode**: Direct waveform cross-correlation
  - **NCC Mode**: Band-pass filtering + envelope detection + normalized cross-correlation
- Configurable sensitivity and timing constraints

**Parameters:**
- `threshold`: NCC threshold (0-1), higher = stricter
- `min_separation_s`: Minimum time between detections (seconds)
- `sr_target`: Processing sample rate (Hz)
- `band_low`/`band_high`: Frequency band for filtering (Hz)
- `smooth_ms`: Envelope smoothing window (milliseconds)
- `raw`: Use raw correlation instead of filtered NCC
- `start_s`/`end_s`: Time range filtering (seconds)

**Example Response:**
```json
{
  "filename": "lecture.mp3",
  "template": "beep_template.wav",
  "sr": 22050,
  "threshold": 0.6,
  "min_separation_s": 0.5,
  "raw": false,
  "matches": [2.5, 15.3, 28.7],
  "matches_mm_ss": ["00:02.500", "00:15.300", "00:28.700"],
  "num_matches": 3
}
```

---

### 3. Generate Report
**POST** `/generate-report/`

Generates a text file report of detected beeps.

**Request:**
- Same parameters as `/detect-template-matches/`
- Additional optional parameter: `output_filename`

**Response Model:**
```json
{
  "output_path": "string",
  "count": 3,
  "params": {
    "raw": false,
    "threshold": 0.6,
    "min_separation_s": 0.5,
    "sr": 22050,
    "band_low": 1100.0,
    "band_high": 1300.0,
    "smooth_ms": 10.0,
    "start_s": null,
    "end_s": null
  },
  "sample_first_5": ["00:02.500", "00:15.300"],
  "sample_last_5": ["00:28.700"]
}
```

**Description:**
- Runs template matching detection
- Saves results to text file with metadata
- Returns file path and summary data

---

### 4. Health Check
**GET** `/`

Simple health check endpoint.

**Response:**
```json
{
  "status": "Audio Processing API is running!"
}
```

---

## Data Models

### FindBeepsResponse
```json
{
  "filename": "string",
  "detected_beep_timestamps": [number],
  "detected_beep_timestamps_mm_ss": ["string"]
}
```

### TemplateMatchResponse
```json
{
  "filename": "string",
  "template": "string",
  "sr": integer,
  "threshold": number,
  "min_separation_s": number,
  "raw": boolean,
  "matches": [number],
  "matches_mm_ss": ["string"],
  "num_matches": integer
}
```

### GenerateReportResponse
```json
{
  "output_path": "string",
  "count": integer,
  "params": object,
  "sample_first_5": ["string"],
  "sample_last_5": ["string"]
}
```

---

## Usage Examples

### cURL Examples

**Frequency Detection:**
```bash
curl -X POST "http://localhost:8000/detect-frequency-beeps/" \
  -F "file=@audio.mp3"
```

**Template Matching:**
```bash
curl -X POST "http://localhost:8000/detect-template-matches/" \
  -F "file=@lecture.mp3" \
  -d "threshold=0.7&min_separation_s=0.4&raw=false"
```

**Generate Report:**
```bash
curl -X POST "http://localhost:8000/generate-report/" \
  -F "file=@test.mp3" \
  -d "output_filename=my_report.txt"
```

### Python Examples

```python
import requests

# Frequency detection
with open('audio.mp3', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/detect-frequency-beeps/',
        files={'file': f}
    )
    result = response.json()
    print(f"Found {len(result['detected_beep_timestamps'])} beeps")

# Template matching with parameters
params = {
    'threshold': 0.7,
    'min_separation_s': 0.4,
    'raw': False
}
with open('lecture.mp3', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/detect-template-matches/',
        files={'file': f},
        data=params
    )
    result = response.json()
    print(f"Matches: {result['num_matches']}")
```

## Configuration

All parameters can be configured via:
1. Query parameters in HTTP requests
2. Environment variables (see Configuration Documentation)
3. Default values applied if neither provided

## File Requirements

- **Supported formats**: Any format supported by librosa (MP3, WAV, M4A, etc.)
- **Template file**: `beep_template.wav` must exist in project root
- **Size limits**: No explicit limits, subject to server memory constraints