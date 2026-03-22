# AI Tool Suite - Guidance

## 1) Prerequisites

- Python 3.8+
- Gemini API key
- FFmpeg available using one of these methods:
  - `FFMPEG_PATH` set in `.env`
  - Local binary in `bin/ffmpeg(.exe)` or `ffmpeg/bin/ffmpeg(.exe)`
  - System install available via PATH

## 2) Install Dependencies

```bash
pip install flask requests faker python-dotenv opencv-python scikit-image numpy
```

Optional fallback binary helper:

```bash
pip install imageio-ffmpeg
```

## 3) Environment Configuration

Copy template:

```bash
Copy-Item .env.example .env
```

Recommended `.env`:

```env
GEMINI_API_KEY=your-real-gemini-key
GEMINI_MODEL=gemini-flash-latest
FLASK_DEBUG=false
PROCESSING_RETENTION_MINUTES=60
VIDEO_MAX_UPLOAD_MB=500
FFMPEG_PATH=
```

## 4) Run Locally

```bash
python app.py
```

Open `http://localhost:5000`.

## 5) Feature Notes

### AI tools (summarizer, grammar, ideas, todo)
- Responses are cached in `cache.json` for 24 hours.
- Cache entries include: `tool`, `query`, `response`, `timestamp`.

### Fake Profile Generator
- Uses Faker.
- Supports age/gender/country/count filters.
- Also cached via `cache.json`.

### Premium Video Compressor
- Uses FFmpeg H.265 (`libx265`) + AAC.
- Output is bundled as ZIP.
- FFmpeg resolution order:
  1. `FFMPEG_PATH`
  2. Local bundled binary (`bin/`, `ffmpeg/bin/`)
  3. System PATH
  4. Optional `imageio-ffmpeg` fallback

### Unique Frame Extractor
- Uses OpenCV + SSIM to save visually distinct frames only.
- Output: PNG frames inside ZIP.

### Motion Frame Extractor
- Detects static vs dynamic videos using sampled frame-difference.
- Static: representative frame
- Dynamic: interval-based frame extraction
- Output: JPG frames inside ZIP.

### Processing History
- Page: `/processing-history`
- Keeps recent processing jobs downloadable for limited time.
- Controlled by `PROCESSING_RETENTION_MINUTES`.
- Includes “Delete All History Now” action.

## 6) Security Guidance

- Never commit `.env`.
- Keep `FLASK_DEBUG=false` in production.
- Rotate keys if exposed.
- Avoid committing sensitive cache artifacts.
- Prefer HTTPS and reverse proxy in production.

## 7) Troubleshooting

### Gemini errors
- Confirm `GEMINI_API_KEY` in `.env`.
- Restart app after `.env` edits.
- Check API key permissions and quota.

### FFmpeg not found
- Set `FFMPEG_PATH` to exact binary, or install/add to PATH.
- Windows quick install: `choco install ffmpeg`

### OpenCV/SSIM unavailable
- Install dependencies:
  ```bash
  pip install opencv-python scikit-image numpy
  ```

### Large upload rejected
- Increase `VIDEO_MAX_UPLOAD_MB` in `.env`.

## 8) GitHub/Deployment Checklist

- `.env` excluded from repository
- `.env.example` present and updated
- `FLASK_DEBUG=false`
- API keys not present in `cache.json` or tracked files
- FFmpeg strategy selected (`FFMPEG_PATH`, local binary, or PATH install)

## 9) Docs Policy

This repository keeps only two docs by design:

- `README.md`
- `GUIDE.md`
