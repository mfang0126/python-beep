# Configuration and Setup Guide

## Environment Configuration

The Audio Beep Detection API supports flexible configuration through environment variables, query parameters, and default values. This guide covers all configuration options and setup procedures.

## Configuration Hierarchy

Parameters are resolved in this order of priority:

1. **Query Parameters** (highest priority)
2. **Environment Variables** (medium priority)  
3. **Hard-coded Defaults** (lowest priority)

## Environment Variables

### Detection Parameters

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BEEP_THRESHOLD` | float | 0.6 | Detection threshold (0.0 - 1.0) |
| `BEEP_MIN_SEP` | float | 0.5 | Minimum separation between detections (seconds) |
| `BEEP_SR` | int | 11025 | Processing sample rate (Hz) |
| `BEEP_RAW` | bool | false | Use raw correlation mode instead of NCC |

### Signal Processing Parameters

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BEEP_BAND_LOW` | float | 1100.0 | Lower frequency bound for band-pass filter (Hz) |
| `BEEP_BAND_HIGH` | float | 1300.0 | Upper frequency bound for band-pass filter (Hz) |
| `BEEP_SMOOTH_MS` | float | 10.0 | Envelope smoothing window size (milliseconds) |

### Time Range Filtering

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BEEP_START_S` | float | null | Start time for analysis (seconds) |
| `BEEP_END_S` | float | null | End time for analysis (seconds) |

### File Paths

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEFAULT_TEMPLATE_PATH` | string | `./beep_template.wav` | Path to beep template file |

## Setup Instructions

### 1. Environment File Setup

Create a `.env` file in the project root:

```bash
# .env file for Audio Beep Detection API

# === Detection Parameters ===
# Higher values = stricter detection (fewer false positives)
BEEP_THRESHOLD=0.6

# Minimum time between beep detections in seconds
BEEP_MIN_SEP=0.5

# Audio processing sample rate (lower = faster, higher = more accurate)
BEEP_SR=22050

# Use raw correlation mode (true) or filtered NCC mode (false)
BEEP_RAW=false

# === Signal Processing Parameters ===
# Frequency range for band-pass filtering (Hz)
BEEP_BAND_LOW=1100.0
BEEP_BAND_HIGH=1300.0

# Envelope smoothing window size in milliseconds
BEEP_SMOOTH_MS=10.0

# === Time Range Filtering ===
# Optional: Limit analysis to specific time range
# BEEP_START_S=10.0
# BEEP_END_S=300.0

# === File Paths ===
# Path to your beep template file
DEFAULT_TEMPLATE_PATH=/Users/freedom/CCL/python-beep/beep_template.wav
```

### 2. Template File Setup

The template file is crucial for template matching detection:

```bash
# Create or place your beep template file
cp your_beep_sound.wav beep_template.wav

# Or specify custom path in .env
# DEFAULT_TEMPLATE_PATH=/custom/path/to/template.wav
```

**Template File Requirements:**
- **Format**: WAV format recommended
- **Content**: Clear, isolated beep sound
- **Duration**: 0.1 - 2 seconds optimal
- **Quality**: High signal-to-noise ratio
- **Consistency**: Should match the beeps you want to detect

### 3. Server Configuration

#### Development Server

```bash
# Basic development server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# With custom host and port
python -m uvicorn main:app --reload --host 192.168.1.100 --port 8080

# With log level
python -m uvicorn main:app --reload --log-level debug
```

#### Production Server

```bash
# Production configuration
python -m uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  --access-log \
  --error-log
```

## Configuration Examples

### Example 1: High Sensitivity Detection

```bash
# .env for detecting faint beeps
BEEP_THRESHOLD=0.3
BEEP_MIN_SEP=0.2
BEEP_SR=44100
BEEP_RAW=false
BEEP_BAND_LOW=800.0
BEEP_BAND_HIGH=1600.0
```

### Example 2: Fast Processing

```bash
# .env for quick processing with lower accuracy
BEEP_THRESHOLD=0.8
BEEP_MIN_SEP=1.0
BEEP_SR=8000
BEEP_RAW=true
BEEP_BAND_LOW=1000.0
BEEP_BAND_HIGH=1400.0
```

### Example 3: Specific Frequency Range

```bash
# .env for targeting specific beep frequencies
BEEP_THRESHOLD=0.7
BEEP_BAND_LOW=2000.0
BEEP_BAND_HIGH=2500.0
BEEP_SMOOTH_MS=5.0
```

## Parameter Tuning Guide

### Threshold (`BEEP_THRESHOLD`)

**Range**: 0.0 - 1.0

| Value | Effect | Use Case |
|-------|--------|----------|
| 0.1 - 0.3 | Very sensitive | Faint beeps, noisy environments |
| 0.4 - 0.6 | Balanced | General purpose detection |
| 0.7 - 0.9 | Strict | Clean audio, specific beeps |
| 0.9 - 1.0 | Very strict | High confidence only |

### Sample Rate (`BEEP_SR`)

**Common Values**: 8000, 11025, 22050, 44100

| Rate | Effect | Use Case |
|------|--------|----------|
| 8000 | Fast, low quality | Quick scans, long files |
| 11025 | Balanced | Default, good compromise |
| 22050 | Good quality | Most applications |
| 44100 | High quality | Precision detection |

### Frequency Band (`BEEP_BAND_LOW`/`BEEP_BAND_HIGH`)

**Typical Beep Frequencies**:
- Standard beeps: 800-1200 Hz
- High-pitched beeps: 1200-2000 Hz
- Low-pitched beeps: 400-800 Hz

### Minimum Separation (`BEEP_MIN_SEP`)

**Range**: 0.1 - 5.0 seconds

| Value | Effect | Use Case |
|-------|--------|----------|
| 0.1 - 0.3 | Close beeps | Rapid beeps, timers |
| 0.4 - 0.8 | Normal | General detection |
| 1.0 - 2.0 | Spaced beeps | Quiz answers, markers |
| 3.0+ | Very spaced | Hourly chimes, alerts |

## System Requirements

### Minimum Requirements
- **Python**: 3.8+
- **Memory**: 1GB RAM
- **Storage**: 100MB for dependencies
- **CPU**: Single core

### Recommended Requirements
- **Python**: 3.9+
- **Memory**: 4GB RAM
- **Storage**: 1GB free space
- **CPU**: Multi-core for concurrent processing

### Large File Processing
- **Memory**: 8GB+ RAM for large audio files
- **CPU**: Fast processor for real-time processing
- **Storage**: SSD for faster file I/O

## Deployment Configuration

### Docker Setup

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Systemd Service

```ini
# /etc/systemd/system/beep-api.service
[Unit]
Description=Audio Beep Detection API
After=network.target

[Service]
Type=exec
User=apiuser
WorkingDirectory=/path/to/python-beep
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Increase timeout for large file uploads
        client_max_body_size 100M;
        proxy_read_timeout 300s;
    }
}
```

## Testing Configuration

### Test Environment Setup

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx

# Create test configuration
cp .env .env.test
# Modify .env.test with test-specific values
```

### Configuration Validation

```python
# test_config.py
import os
from dotenv import load_dotenv

def test_configuration():
    load_dotenv()
    
    # Test required environment variables
    assert os.getenv('BEEP_THRESHOLD') is not None
    assert os.getenv('DEFAULT_TEMPLATE_PATH') is not None
    
    # Test template file exists
    template_path = os.getenv('DEFAULT_TEMPLATE_PATH')
    assert os.path.exists(template_path)
    
    # Test parameter ranges
    threshold = float(os.getenv('BEEP_THRESHOLD'))
    assert 0.0 <= threshold <= 1.0
    
    print("Configuration validation passed!")
```

## Troubleshooting

### Common Configuration Issues

**Template File Not Found**
```bash
# Check template path
echo $DEFAULT_TEMPLATE_PATH
ls -la "$DEFAULT_TEMPLATE_PATH"

# Fix: Update path in .env
DEFAULT_TEMPLATE_PATH=/correct/path/to/beep_template.wav
```

**Invalid Parameter Values**
```bash
# Check parameter ranges
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
threshold = float(os.getenv('BEEP_THRESHOLD', 0.6))
print(f'Threshold: {threshold} (valid: {0.0 <= threshold <= 1.0})')
"
```

**Permission Issues**
```bash
# Check file permissions
ls -la beep_template.wav
chmod 644 beep_template.wav

# Check directory permissions
ls -ld .
chmod 755 .
```

### Performance Tuning

**Memory Issues with Large Files**
```bash
# Reduce sample rate
BEEP_SR=8000

# Use raw mode (faster but less accurate)
BEEP_RAW=true

# Increase minimum separation
BEEP_MIN_SEP=1.0
```

**Slow Processing**
```bash
# Lower sample rate
BEEP_SR=11025

# Use raw correlation mode
BEEP_RAW=true

# Reduce frequency band width
BEEP_BAND_LOW=1150.0
BEEP_BAND_HIGH=1250.0
```

## Security Considerations

### File Upload Security
- Validate file types and sizes
- Use virus scanning for uploaded files
- Implement rate limiting
- Use secure temporary file handling

### Network Security
- Use HTTPS in production
- Implement authentication if needed
- Use firewall rules
- Monitor access logs

### Environment Variable Security
- Don't commit sensitive values to version control
- Use secret management for production
- Restrict file permissions
- Use environment-specific configurations

## Backup and Recovery

### Configuration Backup
```bash
# Backup configuration files
cp .env .env.backup
cp beep_template.wav beep_template.wav.backup

# Create configuration archive
tar -czf config_backup.tar.gz .env beep_template.wav requirements.txt
```

### Recovery Process
```bash
# Restore from backup
tar -xzf config_backup.tar.gz
source .env
```

## Monitoring and Logging

### Log Configuration
```bash
# Enable detailed logging
python -m uvicorn main:app --log-level debug --access-log

# Custom log format
python -m uvicorn main:app --log-config logging_config.ini
```

### Performance Monitoring
```bash
# Monitor resource usage
top -p $(pgrep -f uvicorn)

# Monitor API responses
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/"
```

This configuration guide provides comprehensive setup instructions for deploying and optimizing the Audio Beep Detection API in various environments.