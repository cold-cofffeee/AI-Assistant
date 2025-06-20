from flask import Flask, render_template, request, jsonify
import requests
import json
import hashlib
import os
from datetime import datetime, timedelta
import re

app = Flask(__name__)

# Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'your_api_')
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
CACHE_FILE = 'cache.json'

def load_cache():
    """Load cache from JSON file"""
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_cache(cache_data):
    """Save cache to JSON file"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=2)

def get_cache_key(text, feature):
    """Generate cache key from text and feature"""
    combined = f"{feature}:{text}"
    return hashlib.md5(combined.encode()).hexdigest()

def is_cache_valid(timestamp):
    """Check if cache entry is less than 24 hours old"""
    cache_time = datetime.fromisoformat(timestamp)
    return datetime.now() - cache_time < timedelta(hours=24)

def call_gemini_api(prompt):
    """Make API call to Gemini"""
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(GEMINI_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except requests.RequestException as e:
        return f"API Error: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Response parsing error: {str(e)}"

def get_ai_response(text, feature, prompt_template):
    """Get AI response with caching"""
    # Check cache first
    cache = load_cache()
    cache_key = get_cache_key(text, feature)
    
    if cache_key in cache and is_cache_valid(cache[cache_key]['timestamp']):
        return cache[cache_key]['response']
    
    # Make API call
    prompt = prompt_template.format(text=text)
    response = call_gemini_api(prompt)
    
    # Save to cache
    cache[cache_key] = {
        'response': response,
        'timestamp': datetime.now().isoformat()
    }
    save_cache(cache)
    
    return response

@app.route('/')
def index():
    """Main page with feature selection"""
    return render_template('index.html')

@app.route('/summarizer')
def summarizer():
    """Text summarizer page"""
    return render_template('summarizer.html')

@app.route('/api/summarize', methods=['POST'])
def api_summarize():
    """API endpoint for text summarization"""
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    if len(text) < 50:
        return jsonify({'error': 'Text too short to summarize'}), 400
    
    prompt_template = """Please provide a concise summary of the following text. 
    Keep it clear and informative, highlighting the main points:

    {text}"""
    
    summary = get_ai_response(text, 'summarizer', prompt_template)
    return jsonify({'summary': summary})

@app.route('/grammar')
def grammar():
    """Grammar checker page"""
    return render_template('grammar.html')

@app.route('/api/grammar', methods=['POST'])
def api_grammar():
    """API endpoint for grammar checking"""
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    prompt_template = """Please check the following text for grammar, spelling, and style issues. 
    Provide specific suggestions for improvement. Format your response as:
    
    CORRECTIONS:
    - List specific issues found
    - Suggest improvements
    
    IMPROVED TEXT:
    [Provide the corrected version]
    
    Text to check:
    {text}"""
    
    suggestions = get_ai_response(text, 'grammar', prompt_template)
    return jsonify({'suggestions': suggestions})

@app.route('/ideas')
def ideas():
    """Idea generator page"""
    return render_template('ideas.html')

@app.route('/api/ideas', methods=['POST'])
def api_ideas():
    """API endpoint for idea generation"""
    data = request.get_json()
    topic = data.get('topic', '').strip()
    
    if not topic:
        return jsonify({'error': 'No topic provided'}), 400
    
    prompt_template = """Generate 5 creative and practical ideas related to the topic: "{text}"
    
    Please format each idea as:
    IDEA X: [Title]
    [2-3 sentence description]
    
    Make sure the ideas are diverse, actionable, and relevant to the topic."""
    
    ideas_text = get_ai_response(topic, 'ideas', prompt_template)
    
    # Parse ideas into structured format
    ideas = []
    idea_blocks = re.split(r'IDEA \d+:', ideas_text)[1:]  # Split by "IDEA X:" and remove first empty element
    
    for i, block in enumerate(idea_blocks, 1):
        lines = block.strip().split('\n')
        title = lines[0].strip()
        description = ' '.join(line.strip() for line in lines[1:] if line.strip())
        ideas.append({
            'title': title,
            'description': description
        })
    
    return jsonify({'ideas': ideas})

@app.route('/todo')
def todo():
    """Smart to-do list page"""
    return render_template('todo.html')

@app.route('/api/todo', methods=['POST'])
def api_todo():
    """API endpoint for to-do list generation"""
    data = request.get_json()
    goal = data.get('goal', '').strip()
    
    if not goal:
        return jsonify({'error': 'No goal provided'}), 400
    
    prompt_template = """Create a structured to-do list for the following goal: "{text}"
    
    Please format the response as:
    TASK: [Task description] | TIME: [Estimated time]
    
    Provide 5-8 specific, actionable tasks with realistic time estimates.
    Make sure tasks are ordered logically and break down the goal into manageable steps."""
    
    todo_text = get_ai_response(goal, 'todo', prompt_template)
    
    # Parse tasks into structured format
    tasks = []
    lines = todo_text.split('\n')
    
    for line in lines:
        if 'TASK:' in line and 'TIME:' in line:
            parts = line.split('|')
            task = parts[0].replace('TASK:', '').strip()
            time_estimate = parts[1].replace('TIME:', '').strip() if len(parts) > 1 else '30 minutes'
            tasks.append({
                'task': task,
                'time': time_estimate
            })
    
    return jsonify({'tasks': tasks})

if __name__ == '__main__':
    # Create cache file if it doesn't exist
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'w') as f:
            json.dump({}, f)
    
    app.run(debug=True)