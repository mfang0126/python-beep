# 📡 Audio Beep Detection API - Complete Documentation

## 🎯 Overview

This API detects beep sounds in audio files using two different methods:
1. **Frequency Analysis** - Detects beeps in specific frequency ranges
2. **Template Matching** - Finds matches using a reference beep template

## 🚀 Quick Start

### Running the Server
```bash
# Using uvicorn (recommended)
uvicorn main:app --host 0.0.0.0 --port 8000

# Using uv run
uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Using python
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Check if server is running
curl http://localhost:8000/

# Interactive API docs
open http://localhost:8000/docs
```

## 🔧 Endpoints

### 1. Health Check
```
GET /
```
Returns server status.

### 2. Frequency Detection
```
POST /detect-frequency-beeps/
```
Detects beeps using frequency analysis.

**Parameters:**
- `file` (required): Audio file to analyze
- `target_freq_low` (optional): Lower frequency bound (default: 1100 Hz)
- `target_freq_high` (optional): Upper frequency bound (default: 1300 Hz)
- `threshold_multiplier` (optional): Sensitivity multiplier (default: 5.0)
- `n_fft` (optional): FFT window size (default: 4096)
- `hop_length` (optional): STFT hop length (default: n_fft // 4)

### 3. Template Matching
```
POST /detect-template-matches/
```
Detects beeps using template matching.

**Parameters:**
- `file` (required): Audio file to analyze
- `threshold` (optional): NCC threshold 0-1 (default: 0.7)
- `min_separation_s` (optional): Minimum time between beeps in seconds (default: 0.4)
- `sr_target` (optional): Target sample rate (default: 22050 Hz)
- `band_low` (optional): Lower filter frequency (default: 1100 Hz)
- `band_high` (optional): Upper filter frequency (default: 1300 Hz)
- `smooth_ms` (optional): Smoothing window in milliseconds (default: 10 ms)
- `raw` (optional): Use raw correlation (default: false)
- `start_s` (optional): Start time in seconds
- `end_s` (optional): End time in seconds

## 📊 Detection Methods

### Method 1: Frequency Analysis (STFT)

**How it works:**
1. **Load Audio**: Uses librosa to load the audio file
2. **STFT Transform**: Applies Short-Time Fourier Transform
3. **Frequency Filtering**: Focuses on 1100-1300 Hz range (typical beep frequencies)
4. **Energy Calculation**: Computes energy in target frequency range
5. **Peak Detection**: Finds energy peaks above threshold (5x average)
6. **Grouping**: Groups consecutive detections to avoid duplicates

**Best for:**
- Detecting beeps of varying frequencies
- Quick scanning with good sensitivity
- Audio with consistent beep characteristics

**Response Format:**
```json
{
  "filename": "audio.mp3",
  "detected_beep_timestamps": [0.682, 0.789, 1.472, ...],
  "detected_beep_timestamps_mm_ss": ["00:00.682", "00:00.789", "00:01.472", ...]
}
```

### Method 2: Template Matching (Cross-Correlation)

**How it works:**
1. **Template Loading**: Loads reference beep template (`beep_template.wav`)
2. **Audio Loading**: Loads target audio file
3. **Preprocessing** (if raw=false):
   - Band-pass filtering (1100-1300 Hz)
   - Envelope extraction
   - Smoothing
4. **Cross-Correlation**: Computes normalized cross-correlation
5. **Peak Detection**: Finds correlation peaks above threshold
6. **Time Conversion**: Converts sample indices to timestamps

**Best for:**
- Finding exact matches to a known beep pattern
- High-precision detection
- Audio with consistent beep characteristics

**Response Format:**
```json
{
  "filename": "audio.mp3",
  "template": "beep_template.wav",
  "sr": 22050,
  "threshold": 0.7,
  "min_separation_s": 0.4,
  "raw": true,
  "matches": [9.050, 50.335, 71.172, ...],
  "matches_mm_ss": ["00:09.050", "00:50.335", "01:11.172", ...],
  "num_matches": 32
}
```

## 🎮 Usage Examples

### Using cURL
```bash
# Frequency detection
curl -X POST "http://localhost:8000/detect-frequency-beeps/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3;type=audio/mpeg"

# Template matching with custom parameters
curl -X POST "http://localhost:8000/detect-template-matches/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3;type=audio/mpeg" \
  -F "threshold=0.8" \
  -F "min_separation_s=0.5"
```

### Using Python
```python
import requests

# Frequency detection
with open('audio.mp3', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/detect-frequency-beeps/',
        files=files
    )
    result = response.json()
    print(f"Found {len(result['detected_beep_timestamps'])} beeps")

# Template matching
with open('audio.mp3', 'rb') as f:
    files = {'file': f}
    data = {
        'threshold': 0.8,
        'min_separation_s': 0.5
    }
    response = requests.post(
        'http://localhost:8000/detect-template-matches/',
        files=files,
        data=data
    )
    result = response.json()
    print(f"Found {result['num_matches']} matches")
```

## ⚙️ Configuration

### Environment Variables
```bash
# Template Matching Settings
BEEP_THRESHOLD=0.7              # NCC threshold (0-1)
BEEP_MIN_SEP=0.5                # Minimum separation (seconds)
BEEP_SR=22050                   # Sample rate
BEEP_BAND_LOW=1100              # Lower frequency bound
BEEP_BAND_HIGH=1300             # Upper frequency bound
BEEP_SMOOTH_MS=10               # Smoothing window (ms)
BEEP_RAW=false                  # Use raw correlation
DEFAULT_TEMPLATE_PATH="./beep_template.wav"  # Template file path

# Frequency Detection Settings
TARGET_FREQ_LOW=1100            # Default low frequency
TARGET_FREQ_HIGH=1300           # Default high frequency
THRESHOLD_MULTIPLIER=5.0        # Sensitivity multiplier
```

### File Structure
```
python-beep/
├── main.py                     # Main FastAPI application
├── beep_template.wav           # Reference beep template
├── requirements.txt            # Python dependencies
├── api/                        # Modular API structure (optional)
│   ├── main.py
│   ├── routes/
│   ├── utils/
│   └── models/
└── docs/                       # Documentation
```

## 📈 Performance Notes

### Frequency Detection
- **Speed**: Moderate (1-20 seconds depending on file length)
- **Sensitivity**: High (detects various beep frequencies)
- **Accuracy**: Good for general beep detection
- **Use Cases**: Quick scans, varied beep types

### Template Matching
- **Speed**: Fast (1-5 seconds)
- **Sensitivity**: Configurable via threshold
- **Accuracy**: Excellent for exact pattern matching
- **Use Cases**: Precise detection, consistent beep patterns

## 🔍 Troubleshooting

### Common Issues

1. **"请上传一个音频文件"**
   - Solution: Add `;type=audio/mpeg` to curl command
   - Ensure file has proper audio MIME type

2. **"默认模板文件不存在"**
   - Solution: Ensure `beep_template.wav` exists in project root
   - Check file permissions

3. **Empty Results**
   - Adjust threshold parameters
   - Check frequency ranges match your beeps
   - Verify audio quality

4. **Processing Time**
   - Large files take longer to process
   - Template matching is generally faster
   - Consider segmenting very long audio files

### Optimization Tips

1. **For Frequency Detection**:
   - Adjust `target_freq_low/high` to match your beep frequencies
   - Tune `threshold_multiplier` for sensitivity
   - Use appropriate `n_fft` for your audio

2. **For Template Matching**:
   - Create a good template from your actual beeps
   - Adjust `threshold` for precision/sensitivity trade-off
   - Use `raw=true` for simple correlation, `raw=false` for filtered

## 🧪 Testing

The API has been tested with:
- **MP3 files** ✅
- **WAV files** ✅
- **Mandarin audio with beeps** ✅
- **Various audio lengths** ✅

### Test Results Summary
- **Test File**: `Audio File of Test ID 369100 - Mandarin.mp3`
- **Frequency Detection**: 412 beeps found
- **Template Matching**: 32 beeps found
- **Processing Time**: ~19 seconds (frequency), ~1 second (template)

## 📚 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔮 Future Enhancements

Potential improvements:
- Support for more audio formats (FLAC, AAC, etc.)
- Real-time streaming audio processing
- Additional detection algorithms (ML-based)
- Batch processing for multiple files
- Audio visualization and spectrogram views
- Export results to various formats (CSV, JSON, XML)

---

**Created**: 2025-09-02  
**Version**: 1.0.0  
**Framework**: FastAPI with librosa audio processing