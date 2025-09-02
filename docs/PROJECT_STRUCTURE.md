# Project Structure Documentation

## Directory Structure

```
python-beep/
├── main.py                 # Main FastAPI application
├── requirements.txt        # Python dependencies
├── beep_template.wav      # Reference beep template for matching
├── beeps_mandarin_matches.txt  # Sample output file
├── uvicorn.log           # Server logs (generated)
├── docs/                 # Documentation directory
│   └── API_DOCUMENTATION.md
└── README.md            # Project overview
```

## Core Components

### 1. main.py - Main Application
**File**: `/main.py`  
**Lines**: 580 lines  
**Purpose**: FastAPI application with audio processing endpoints

#### Key Classes:
- `FindBeepsResponse` - Response model for frequency detection
- `TemplateMatchResponse` - Response model for template matching
- `GenerateReportResponse` - Response model for report generation

#### Key Functions:
- `_format_mm_ss()` - Time formatting utility
- `_get_env_*()` - Environment variable helpers
- `detect_frequency_beeps()` - Frequency-based beep detection
- `detect_template_matches()` - Template matching detection
- `generate_report()` - Report generation endpoint

#### Endpoints:
- `POST /detect-frequency-beeps/` - Frequency analysis detection
- `POST /detect-template-matches/` - Template matching detection
- `POST /generate-report/` - Text report generation
- `GET /` - Health check

### 2. requirements.txt - Dependencies
**File**: `/requirements.txt`  
**Purpose**: Python package dependencies

#### Core Dependencies:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `librosa` - Audio processing library
- `numpy` - Numerical computing
- `scipy` - Signal processing
- `python-dotenv` - Environment variable management

### 3. beep_template.wav - Reference Template
**File**: `/beep_template.wav`  
**Purpose**: Reference beep sound for template matching
**Usage**: Used by `/detect-template-matches/` and `/generate-report/`

### 4. beeps_mandarin_matches.txt - Sample Output
**File**: `/beeps_mandarin_matches.txt`  
**Purpose**: Example output from template matching
**Format**: Text file with metadata and timestamps

## Audio Processing Architecture

### Detection Methods

#### 1. Frequency Analysis (`/detect-frequency-beeps/`)
```
Audio Input → STFT → Frequency Band Analysis → Energy Threshold → Peak Detection → Output
```

**Key Components:**
- STFT (Short-Time Fourier Transform)
- Frequency band filtering (1100-1300 Hz)
- Dynamic threshold calculation
- Peak grouping and deduplication

#### 2. Template Matching (`/detect-template-matches/`)
```
Audio Input → Template Loading → Processing Mode Selection → Cross-Correlation → Peak Detection → Output
```

**Processing Modes:**
- **Raw Mode**: Direct waveform correlation
- **NCC Mode**: Band-pass → Envelope → Normalized Cross-Correlation

### Signal Processing Pipeline

#### For Template Matching (NCC Mode):
```
Audio → Band-pass Filter → Envelope Detection → Smoothing → Cross-Correlation → Peak Detection
```

**Key Signal Processing Functions:**
- `butter()` - Butterworth filter design
- `filtfilt()` - Zero-phase filtering
- `fftconvolve()` - Fast convolution
- `find_peaks()` - Peak detection

## Data Flow

### Request Processing:
1. **File Upload** → Multipart form data handling
2. **Parameter Validation** → Query params → Environment vars → Defaults
3. **Audio Loading** → librosa.load() with sample rate conversion
4. **Signal Processing** → Method-specific processing pipeline
5. **Response Generation** → JSON serialization with timestamps

### Configuration Hierarchy:
1. **Query Parameters** (highest priority)
2. **Environment Variables** (medium priority)
3. **Hard-coded Defaults** (lowest priority)

## Configuration System

### Environment Variables:
- `BEEP_THRESHOLD` - Detection threshold (0-1)
- `BEEP_MIN_SEP` - Minimum separation (seconds)
- `BEEP_SR` - Sample rate (Hz)
- `BEEP_BAND_LOW`/`BEEP_BAND_HIGH` - Frequency range (Hz)
- `BEEP_SMOOTH_MS` - Smoothing window (milliseconds)
- `BEEP_RAW` - Use raw correlation mode
- `BEEP_START_S`/`BEEP_END_S` - Time range filtering
- `DEFAULT_TEMPLATE_PATH` - Template file path

### Helper Functions:
- `_get_env_float()` - Float environment variable parsing
- `_get_env_int()` - Integer environment variable parsing
- `_get_env_bool()` - Boolean environment variable parsing
- `_get_env_optional_float()` - Optional float parsing

## Error Handling

### Exception Types:
- `HTTPException` - Client errors (400, 500)
- `ValueError` - Parameter validation
- `FileNotFoundError` - Missing template file
- `RuntimeError` - Audio processing failures

### Error Response Format:
```json
{
  "detail": "Error message describing the issue"
}
```

## File I/O Operations

### Input Files:
- **Audio Files**: Any format supported by librosa
- **Template File**: WAV format (beep_template.wav)

### Output Files:
- **JSON Responses**: API endpoint responses
- **Text Reports**: Generated report files
- **Log Files**: uvicorn server logs

### File Paths:
- **Template**: Configurable via `DEFAULT_TEMPLATE_PATH`
- **Reports**: Project root or specified path
- **Logs**: Same directory as application

## Performance Considerations

### Memory Usage:
- Audio files loaded into memory for processing
- Large files may impact performance
- No explicit file size limits

### Processing Speed:
- Frequency analysis: Faster, simpler
- Template matching: More computationally intensive
- NCC mode: Slower but more accurate

### Optimization:
- FFT-based convolution for speed
- Configurable sample rates for performance trade-off
- Peak distance parameters to reduce false positives

## Extensibility

### Adding New Detection Methods:
1. Create new response model class
2. Implement detection function
3. Add new endpoint
4. Update documentation

### Configuration Expansion:
- Add new environment variables
- Update parameter parsing functions
- Modify default values

### Audio Format Support:
- Limited by librosa capabilities
- Add format-specific handling if needed