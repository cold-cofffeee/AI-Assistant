# AI Tool Suite

A Flask-based web application that combines AI writing/productivity tools with video processing utilities:

- 🔍 **Text Summarizer**: Condense long articles into concise summaries
- 📝 **Grammar & Style Checker**: Get AI-powered writing improvement suggestions
- 💡 **Idea Generator**: Generate creative ideas for any topic
- 📆 **Smart To-Do List**: Create structured task lists with time estimates
- 🧑 **Fake Profile Generator**: Generate realistic mock user profiles for testing and demos
- 🎬 **Premium Video Compressor**: Compress one or more videos with FFmpeg presets and ZIP download
- 🖼️ **Unique Frame Extractor**: Extract only visually distinct frames using SSIM thresholding
- 📽️ **Motion Frame Extractor**: Detect static/dynamic videos and extract representative/interval frames
- 🕘 **Processing History**: View recent processing jobs and re-download ZIP outputs before expiry

## Features

- **Clean, Modern UI**: Simple and user-friendly interface built with HTML, CSS, and JavaScript
- **AI-Powered**: Uses Google Gemini (`gemini-flash-latest` by default) for intelligent text processing
- **Smart Caching**: 24-hour cache system to reduce API calls and improve performance
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Interaction**: Dynamic loading states and error handling
- **Interactive To-Do Lists**: Checkboxes with progress tracking
- **Fake Data Generation**: Configurable profile generation by age, gender, country, and count
- **Video Processing**: Multi-file upload, processing summary, and ZIP result downloads

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- Google Gemini API key

### Installation

1. **Clone or download the project files**:
   ```
   project/
   ├── app.py
   ├── templates/
   │   ├── index.html
   │   ├── summarizer.html
   │   ├── grammar.html
   │   ├── ideas.html
   │   ├── todo.html
   │   ├── fake_profile.html
   │   ├── video_compressor.html
   │   ├── frame_extractor_unique.html
   │   └── frame_extractor_motion.html
   ├── static/
   │   ├── style.css
   │   └── script.js
   ├── cache.json
   └── README.md
   ```

2. **Install required Python packages**:
   ```bash
   pip install flask requests faker python-dotenv opencv-python scikit-image numpy
   ```

3. **Install FFmpeg** (required for video compression):
   - Download from https://ffmpeg.org/download.html and add to PATH
   - Or use package manager (e.g., `choco install ffmpeg` on Windows)

4. **Create your local environment file**:
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env
   ```

5. **Set your API key in `.env`**:
   ```env
   GEMINI_API_KEY=your-real-gemini-key
   GEMINI_MODEL=gemini-flash-latest
   FLASK_DEBUG=false
   PROCESSING_RETENTION_MINUTES=60
   ```

6. **Get your Gemini API key**:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key for the next step

7. **(Optional) Environment variable setup instead of `.env`**:
   ```bash
   # On Windows
   set GEMINI_API_KEY=your-actual-api-key-here
   
   # On macOS/Linux
   export GEMINI_API_KEY=your-actual-api-key-here
   ```

### Running the Application

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Start using the tools**:
   - Click on any feature card to access that tool
   - Enter your text/topic and click the action button
   - View results and interact with the generated content

## Usage Guide

### Text Summarizer
1. Navigate to the summarizer page
2. Paste or type your long text (minimum 50 characters)
3. Click "Summarize Text"
4. View the AI-generated summary

### Grammar & Style Checker
1. Go to the grammar checker page
2. Enter your text to be reviewed
3. Click "Check Grammar & Style"
4. Review suggestions and corrections

### Idea Generator
1. Access the idea generator
2. Enter a topic or keyword
3. Click "Generate Ideas"
4. Browse through 5 creative ideas presented as cards

### Smart To-Do List
1. Open the to-do list generator
2. Enter your goal (e.g., "Study for exams next week")
3. Click "Generate To-Do List"
4. Check off tasks as you complete them
5. View progress statistics

### Fake Profile Generator
1. Open the fake profile generator page
2. Optionally set age, gender, and country
3. Set the number of profiles (1-20)
4. Click "Generate Profiles"
5. Review the generated profile objects

### Premium Video Compressor
1. Open the video compressor page
2. Upload one or more videos
3. Choose preset (Maximum / Balanced / Fast)
4. Run compression and download ZIP results

### Unique Frame Extractor
1. Open unique frame extractor
2. Upload videos and set similarity threshold
3. Extract visually unique frames
4. Download ZIP containing extracted PNG files

### Motion Frame Extractor
1. Open motion frame extractor
2. Upload videos and set motion threshold + frame interval
3. Process static/dynamic detection and extraction
4. Download ZIP containing extracted JPG files

### Processing History
1. Open Processing History from the home page
2. Review recent video-processing jobs
3. Download ZIP outputs before their retention window expires

## Technical Details

### Caching System
- All API responses are cached for 24 hours
- Cache keys are generated using MD5 hashes of input text + feature type
- Significantly reduces API calls and improves response time
- Cache is stored in `cache.json` file

### API Integration
- Uses Google Gemini model endpoint with `X-goog-api-key` header
- RESTful API endpoints for each feature
- Proper error handling and user feedback
- Input validation and sanitization

### File Structure
```
app.py              # Main Flask application
templates/          # HTML templates
├── index.html      # Main landing page
├── summarizer.html # Text summarizer interface
├── grammar.html    # Grammar checker interface
├── ideas.html      # Idea generator interface
├── todo.html       # To-do list generator interface
├── fake_profile.html # Fake profile generator interface
├── video_compressor.html # Video compression interface
├── frame_extractor_unique.html # SSIM-based frame extraction interface
└── frame_extractor_motion.html # Motion-based frame extraction interface
static/             # Static assets
├── style.css       # Main stylesheet
└── script.js       # JavaScript utilities
cache.json          # API response cache
README.md           # This file
```

## Customization

### Styling
- Edit `static/style.css` to modify colors, fonts, and layout
- The design uses CSS Grid and Flexbox for responsive layouts
- Color scheme can be easily changed by modifying CSS variables

### AI Prompts
- Modify prompts in `app.py` to adjust AI behavior
- Each feature has its own prompt template
- Experiment with different prompt styles for better results

### Features
- Add new tools by creating new routes and templates
- Follow the existing pattern for consistency
- Don't forget to add caching for new features

## Troubleshooting

### Common Issues

1. **API Key Error**:
   - Ensure your Gemini API key is correctly set
   - Check that the API key has proper permissions
   - Verify the environment variable is set correctly

2. **Import Errors**:
   - Make sure all dependencies are installed: `pip install flask requests faker python-dotenv opencv-python scikit-image numpy`
   - Check Python version compatibility

3. **FFmpeg Errors (Video Compressor)**:
   - Install FFmpeg and ensure `ffmpeg` works from terminal
   - Verify FFmpeg is added to your PATH

4. **Missing Processing History Entries**:
   - History includes only successful video processing jobs
   - Items auto-expire based on `PROCESSING_RETENTION_MINUTES`
   - Expired job folders and links are cleaned up automatically

5. **Cache Issues**:
   - Delete `cache.json` and restart the application
   - Check file permissions for cache.json

6. **Network Errors**:
   - Verify internet connection
   - Check if Gemini API is accessible from your network
   - Review firewall settings

### Debug Mode
Debug mode is controlled by `FLASK_DEBUG` in `.env` (recommended `false` for production):
```python
app.run(debug=False)
```

## Performance Tips

1. **Cache Management**: The cache automatically expires after 24 hours, but you can manually clear it by deleting `cache.json`

2. **API Rate Limits**: Be mindful of Gemini API rate limits. The caching system helps reduce API calls.

3. **Text Length**: Very long texts may take longer to process. Consider adding character limits if needed.

## Security Notes

- Never commit your API key to version control
- Use environment variables for sensitive configuration
- Consider implementing rate limiting for production use
- Validate and sanitize all user inputs

### Before Hosting on GitHub

- Ensure `.env` is not committed (it's ignored via `.gitignore`)
- Use `.env.example` as the only committed env template
- Keep `FLASK_DEBUG=false` for production
- Rotate API keys immediately if they were ever exposed in commits or screenshots
- Avoid committing `cache.json` if it may contain sensitive generated content

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the Gemini API documentation
3. Ensure all setup steps were followed correctly

Happy writing! 🚀