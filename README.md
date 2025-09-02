# Audio Beep Detection API

A FastAPI-based service for detecting beep sounds in audio files using advanced signal processing techniques. This API provides two distinct detection methods: frequency analysis and template matching.

## Features

- **Dual Detection Methods**: Frequency analysis and template matching
- **Configurable Parameters**: Environment variables and query parameters
- **Multiple Audio Formats**: Support for all formats handled by librosa
- **Real-time Processing**: Fast audio processing with optimized algorithms
- **Comprehensive API**: RESTful endpoints with JSON responses
- **Flexible Output**: Timestamps in seconds and MM:SS format

## Detection Methods

### 1. Frequency Analysis (`/detect-frequency-beeps/`)
- Uses Short-Time Fourier Transform (STFT) for frequency analysis
- Detects energy spikes in the 1100-1300 Hz range
- Dynamic threshold calculation based on average energy
- Fast and efficient for general beep detection

### 2. Template Matching (`/detect-template-matches/`)
- Uses cross-correlation with a reference beep template
- Two processing modes: Raw waveform and Normalized Cross-Correlation (NCC)
- More accurate for detecting specific beep patterns
- Configurable sensitivity and timing constraints

## Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone or download the project:**
   ```bash
   cd /path/to/your/project
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare template file:**
   - Ensure `beep_template.wav` exists in the project root
   - This should be a clear sample of the beep sound you want to detect

4. **Run the server:**
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Test the API:**
   ```bash
   curl http://localhost:8000/
   # Response: {"status":"Audio Processing API is running!"}
   ```

## Usage Examples

### Basic Frequency Detection

```bash
# Detect beeps using frequency analysis
curl -X POST "http://localhost:8000/detect-frequency-beeps/" \
  -F "file=@your_audio.mp3"
```

### Template Matching with Custom Parameters

```bash
# Detect beeps using template matching with custom settings
curl -X POST "http://localhost:8000/detect-template-matches/" \
  -F "file=@lecture.mp3" \
  -d "threshold=0.7&min_separation_s=0.4&raw=false"
```

### Generate Text Report

```bash
# Create a text report of detected beeps
curl -X POST "http://localhost:8000/generate-report/" \
  -F "file=@recording.wav" \
  -d "output_filename=beep_report.txt"
```

### Python Client Example

```python
import requests
import json

# Example 1: Basic frequency detection
with open('audio.mp3', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/detect-frequency-beeps/',
        files={'file': f}
    )
    result = response.json()
    print(f"Found {len(result['detected_beep_timestamps'])} beeps")
    for ts in result['detected_beep_timestamps_mm_ss']:
        print(f"  Beep at {ts}")

# Example 2: Template matching with parameters
params = {
    'threshold': 0.7,
    'min_separation_s': 0.4,
    'raw': False,
    'band_low': 1000,
    'band_high': 1500
}
with open('lecture.mp3', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/detect-template-matches/',
        files={'file': f},
        data=params
    )
    result = response.json()
    print(f"Template: {result['template']}")
    print(f"Matches: {result['num_matches']}")
    print(f"Confidence: High threshold detection")
```

## API Endpoints

### `POST /detect-frequency-beeps/`
Detect beeps using frequency analysis.

**Response:**
```json
{
  "filename": "audio.mp3",
  "detected_beep_timestamps": [1.234, 5.678],
  "detected_beep_timestamps_mm_ss": ["00:01.234", "00:05.678"]
}
```

### `POST /detect-template-matches/`
Detect beeps using template matching.

**Parameters:**
- `threshold`: Detection threshold (0-1)
- `min_separation_s`: Minimum time between detections (seconds)
- `raw`: Use raw correlation instead of filtered NCC
- `band_low`/`band_high`: Frequency range for filtering (Hz)
- `sr_target`: Processing sample rate (Hz)

**Response:**
```json
{
  "filename": "lecture.mp3",
  "template": "beep_template.wav",
  "sr": 22050,
  "threshold": 0.6,
  "min_separation_s": 0.5,
  "raw": false,
  "matches": [2.5, 15.3],
  "matches_mm_ss": ["00:02.500", "00:15.300"],
  "num_matches": 2
}
```

### `POST /generate-report/`
Generate a text file report of detected beeps.

### `GET /`
Health check endpoint.

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Detection Parameters
BEEP_THRESHOLD=0.6
BEEP_MIN_SEP=0.5
BEEP_SR=22050
BEEP_RAW=false

# Frequency Filtering
BEEP_BAND_LOW=1100.0
BEEP_BAND_HIGH=1300.0
BEEP_SMOOTH_MS=10.0

# Time Range Filtering
BEEP_START_S=
BEEP_END_S=

# File Paths
DEFAULT_TEMPLATE_PATH=/path/to/beep_template.wav
```

### Parameter Priority

1. **Query Parameters** (highest priority)
2. **Environment Variables** 
3. **Hard-coded Defaults** (lowest priority)

## Audio Requirements

### Supported Formats
- MP3, WAV, M4A, FLAC, and other formats supported by librosa
- Mono or stereo audio files
- Various sample rates (automatically converted)

### Template File
- **File**: `beep_template.wav`
- **Format**: WAV format recommended
- **Content**: Clear sample of the beep sound to detect
- **Duration**: Short duration (0.1-2 seconds typical)

## Technical Details

### Signal Processing

#### Frequency Analysis Method
1. **STFT**: Short-Time Fourier Transform for frequency analysis
2. **Band Filtering**: Focus on 1100-1300 Hz frequency range
3. **Energy Calculation**: Sum energy in target frequency band
4. **Threshold Detection**: Dynamic threshold (5x average energy)
5. **Peak Grouping**: Combine consecutive detections

#### Template Matching Method
1. **Template Loading**: Load reference beep sound
2. **Processing Mode Selection**: Raw or NCC mode
3. **Cross-Correlation**: Find similar patterns in audio
4. **Peak Detection**: Identify correlation peaks above threshold
5. **Time Conversion**: Convert sample indices to timestamps

### Performance Considerations

- **Memory**: Audio files loaded into memory for processing
- **Speed**: Frequency analysis is faster than template matching
- **Accuracy**: Template matching is more accurate for specific patterns
- **Sample Rate**: Lower sample rates improve processing speed

## Troubleshooting

### Common Issues

**Template File Not Found**
```
Error: "默认模板文件不存在。请创建 beep_template.wav。"
```
**Solution**: Ensure `beep_template.wav` exists in the project root

**Invalid Audio File**
```
Error: "无法读取音频或音频为空。"
```
**Solution**: Check file format and ensure it's a valid audio file

**Parameter Out of Range**
```
Error: "带通频段设置不合理，请调整 band_low/band_high。"
```
**Solution**: Adjust frequency band parameters to valid range

### Performance Optimization

1. **Reduce Sample Rate**: Lower `sr_target` for faster processing
2. **Use Raw Mode**: Set `raw=true` for faster template matching
3. **Adjust Threshold**: Higher threshold reduces false positives
4. **Increase Minimum Separation**: Reduces duplicate detections

## Development

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Code Structure

- `main.py`: Main FastAPI application
- `requirements.txt`: Python dependencies
- `beep_template.wav`: Reference template file
- `docs/`: Documentation directory

### Adding New Features

1. Create new response model classes
2. Implement detection functions
3. Add new API endpoints
4. Update documentation
5. Add tests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the API documentation in `docs/API_DOCUMENTATION.md`
- Examine the project structure in `docs/PROJECT_STRUCTURE.md`

## Changelog

### Version 1.0.0
- Initial release
- Frequency analysis detection method
- Template matching detection method
- RESTful API endpoints
- Comprehensive documentation