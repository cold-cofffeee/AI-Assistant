from flask import Flask, render_template, request, jsonify
import requests
import json
import hashlib
import os
from datetime import datetime, timedelta
import re
import random
from faker import Faker

app = Flask(__name__)
fake = Faker()

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

def get_cached_response(cache_key):
    """Return cached response if entry exists and is valid"""
    cache = load_cache()
    entry = cache.get(cache_key)

    if entry and 'timestamp' in entry and is_cache_valid(entry['timestamp']):
        return entry.get('response')

    return None

def save_cached_response(cache_key, tool, query, response):
    """Store response and metadata in cache"""
    cache = load_cache()
    cache[cache_key] = {
        'tool': tool,
        'query': query,
        'response': response,
        'timestamp': datetime.now().isoformat()
    }
    save_cache(cache)

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
    cache_key = get_cache_key(text, feature)

    cached_response = get_cached_response(cache_key)
    if cached_response is not None:
        return cached_response
    
    # Make API call
    prompt = prompt_template.format(text=text)
    response = call_gemini_api(prompt)
    
    save_cached_response(cache_key, feature, text, response)
    
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

@app.route('/fake-profile')
def fake_profile():
    """Fake profile generator page"""
    return render_template('fake_profile.html')

def build_fake_profile(age=None, gender=None, country=None):
    """Generate a single fake profile"""
    selected_gender = gender if gender in ['male', 'female'] else random.choice(['male', 'female'])
    selected_age = age if age and age > 0 else random.randint(18, 70)
    children_count = random.randint(0, 3)

    return {
        'name': fake.name_male() if selected_gender == 'male' else fake.name_female(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'address': {
            'street': fake.street_address(),
            'city': fake.city(),
            'state': fake.state(),
            'zip': fake.zipcode(),
            'country': country if country else fake.country()
        },
        'geo': {
            'lat': float(fake.latitude()),
            'lng': float(fake.longitude())
        },
        'dob': fake.date_of_birth(minimum_age=selected_age, maximum_age=selected_age).isoformat(),
        'gender': selected_gender,
        'education': random.choice(['High School', "Bachelor's", "Master's", 'PhD']),
        'family': {
            'spouse': fake.name(),
            'children': [fake.first_name() for _ in range(children_count)]
        }
    }

@app.route('/api/fake-profile', methods=['POST'])
def api_fake_profile():
    """API endpoint for fake profile generation"""
    data = request.get_json() or {}
    age = data.get('age')
    gender = (data.get('gender') or '').strip().lower()
    country = (data.get('country') or '').strip()
    count = data.get('count', 1)

    try:
        age = int(age) if age not in [None, ''] else None
    except (TypeError, ValueError):
        return jsonify({'error': 'Age must be a valid number'}), 400

    if age is not None and (age < 1 or age > 100):
        return jsonify({'error': 'Age must be between 1 and 100'}), 400

    if gender and gender not in ['male', 'female']:
        return jsonify({'error': 'Gender must be male or female'}), 400

    try:
        count = int(count)
    except (TypeError, ValueError):
        return jsonify({'error': 'Count must be a valid number'}), 400

    if count < 1 or count > 20:
        return jsonify({'error': 'Count must be between 1 and 20'}), 400

    cache_payload = {
        'age': age,
        'gender': gender if gender else None,
        'country': country if country else None,
        'count': count
    }
    cache_text = json.dumps(cache_payload, sort_keys=True)
    cache_key = get_cache_key(cache_text, 'fake_profile')

    cached_profiles = get_cached_response(cache_key)
    if cached_profiles is not None:
        return jsonify({'profiles': cached_profiles})

    profiles = [build_fake_profile(age=age, gender=gender if gender else None, country=country if country else None) for _ in range(count)]
    save_cached_response(cache_key, 'fake_profile', cache_payload, profiles)

    return jsonify({'profiles': profiles})

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