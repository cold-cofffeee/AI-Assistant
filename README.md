# AI Tool Suite

AI Tool Suite is a single Flask app that combines AI writing utilities and video processing tools in one dashboard.

## Tools Included

- Text Summarizer
- Grammar & Style Checker
- Idea Generator
- Smart To-Do List
- Fake Profile Generator
- Premium Video Compressor
- Unique Frame Extractor (SSIM)
- Motion Frame Extractor
- Processing History (time-limited ZIP downloads)

## Quick Start

1. Install dependencies:

```bash
pip install flask requests faker python-dotenv opencv-python scikit-image numpy
```

2. Create your environment file:

```bash
Copy-Item .env.example .env
```

3. Set your keys/config in `.env`:

```env
GEMINI_API_KEY=your-real-gemini-key
GEMINI_MODEL=gemini-flash-latest
FLASK_DEBUG=false
PROCESSING_RETENTION_MINUTES=60
FFMPEG_PATH=
```

4. Run the app:

```bash
python app.py
```

5. Open:

```text
http://localhost:5000
```

## Documentation

This project intentionally keeps only two documentation files:

- `README.md` (overview + quick start)
- `GUIDE.md` (complete setup, operations, troubleshooting, deployment guidance)

For detailed instructions, see `GUIDE.md`.