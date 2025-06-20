# AI Writing Assistant

A Flask-based web application that provides four AI-powered writing tools using Google's Gemini API:

- 🔍 **Text Summarizer**: Condense long articles into concise summaries
- 📝 **Grammar & Style Checker**: Get AI-powered writing improvement suggestions
- 💡 **Idea Generator**: Generate creative ideas for any topic
- 📆 **Smart To-Do List**: Create structured task lists with time estimates

## Features

- **Clean, Modern UI**: Simple and user-friendly interface built with HTML, CSS, and JavaScript
- **AI-Powered**: Uses Google Gemini 2.0 Flash model for intelligent text processing
- **Smart Caching**: 24-hour cache system to reduce API calls and improve performance
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Interaction**: Dynamic loading states and error handling
- **Interactive To-Do Lists**: Checkboxes with progress tracking

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
   │   └── todo.html
   ├── static/
   │   ├── style.css
   │   └── script.js
   ├── cache.json
   └── README.md
   ```

2. **Install required Python packages**:
   ```bash
   pip install flask requests
   ```

3. **Get your Gemini API key**:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key for the next step

4. **Set up your API key**:
   
   **Option A: Environment Variable (Recommended)**
   ```bash
   # On Windows
   set GEMINI_API_KEY=your-actual-api-key-here
   
   # On macOS/Linux
   export GEMINI_API_KEY=your-actual-api-key-here
   ```
   
   **Option B: Direct in Code**
   - Open `app.py`
   - Replace `'your-gemini-api-key-here'` with your actual API key on line 11

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

## Technical Details

### Caching System
- All API responses are cached for 24 hours
- Cache keys are generated using MD5 hashes of input text + feature type
- Significantly reduces API calls and improves response time
- Cache is stored in `cache.json` file

### API Integration
- Uses Google Gemini 2.0 Flash model
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
└── todo.html       # To-do list generator interface
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
   - Make sure Flask and requests are installed: `pip install flask requests`
   - Check Python version compatibility

3. **Cache Issues**:
   - Delete `cache.json` and restart the application
   - Check file permissions for cache.json

4. **Network Errors**:
   - Verify internet connection
   - Check if Gemini API is accessible from your network
   - Review firewall settings

### Debug Mode
The application runs in debug mode by default. To disable for production:
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

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the Gemini API documentation
3. Ensure all setup steps were followed correctly

Happy writing! 🚀