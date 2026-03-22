from flask import Flask, render_template, request, jsonify, send_file
import requests
import json
import hashlib
import os
from datetime import datetime, timedelta
import re
import random
import tempfile
import shutil
import subprocess
import zipfile
import uuid
from pathlib import Path
from faker import Faker
from werkzeug.utils import secure_filename

try:
    import cv2
    import numpy as np
    from skimage.metrics import structural_similarity as ssim
    CV_PACKAGES_AVAILABLE = True
except ImportError:
    CV_PACKAGES_AVAILABLE = False

def load_local_env():
    """Load environment variables from .env file if available."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        return
    except Exception:
        pass

    env_path = '.env'
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, 'r', encoding='utf-8') as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass

load_local_env()

app = Flask(__name__)
fake = Faker()

# Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-flash-latest').strip()
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
CACHE_FILE = 'cache.json'
MAX_INPUT_LENGTH = 10000
PROCESSING_ROOT = 'processing'
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
VIDEO_MAX_UPLOAD_MB = int(os.environ.get('VIDEO_MAX_UPLOAD_MB', '500'))
PROCESSING_RETENTION_MINUTES = int(os.environ.get('PROCESSING_RETENTION_MINUTES', '60'))
PROCESSING_HISTORY_FILE = os.path.join(PROCESSING_ROOT, 'history.json')

app.config['MAX_CONTENT_LENGTH'] = VIDEO_MAX_UPLOAD_MB * 1024 * 1024
app.config['JSON_SORT_KEYS'] = False

os.makedirs(PROCESSING_ROOT, exist_ok=True)

if not os.path.exists(PROCESSING_HISTORY_FILE):
    with open(PROCESSING_HISTORY_FILE, 'w', encoding='utf-8') as history_file:
        json.dump([], history_file)

@app.after_request
def apply_security_headers(response):
    """Attach common security headers for browser protection."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

@app.errorhandler(413)
def request_entity_too_large(_error):
    return jsonify({'error': 'Request payload too large'}), 413

@app.errorhandler(500)
def internal_server_error(_error):
    return jsonify({'error': 'Internal server error'}), 500

def is_allowed_video(filename):
    return Path(filename).suffix.lower() in VIDEO_EXTENSIONS

def create_job_dirs():
    cleanup_expired_processing_jobs()
    job_id = str(uuid.uuid4())
    job_root = os.path.join(PROCESSING_ROOT, job_id)
    uploads_dir = os.path.join(job_root, 'uploads')
    output_dir = os.path.join(job_root, 'output')
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    return job_id, job_root, uploads_dir, output_dir

def create_zip_from_directory(source_dir, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for root, _, files in os.walk(source_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                arc_name = os.path.relpath(file_path, source_dir)
                archive.write(file_path, arc_name)

def load_processing_history():
    try:
        with open(PROCESSING_HISTORY_FILE, 'r', encoding='utf-8') as history_file:
            history = json.load(history_file)
            if isinstance(history, list):
                return history
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_processing_history(history_items):
    with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as temp_file:
        json.dump(history_items, temp_file, indent=2)
        temp_path = temp_file.name
    os.replace(temp_path, PROCESSING_HISTORY_FILE)

def register_processing_job(tool, job_id, total_files, successful_files):
    created_at = datetime.now()
    expires_at = created_at + timedelta(minutes=PROCESSING_RETENTION_MINUTES)

    history = load_processing_history()
    history.insert(0, {
        'job_id': job_id,
        'tool': tool,
        'total_files': total_files,
        'successful_files': successful_files,
        'created_at': created_at.isoformat(),
        'expires_at': expires_at.isoformat(),
        'download_url': f'/api/download/{job_id}'
    })
    save_processing_history(history)

def cleanup_expired_processing_jobs():
    history = load_processing_history()
    now = datetime.now()

    active_history = []
    for item in history:
        expires_at_raw = item.get('expires_at')
        job_id = item.get('job_id')

        if not expires_at_raw or not job_id:
            continue

        try:
            expires_at = datetime.fromisoformat(expires_at_raw)
        except ValueError:
            continue

        if expires_at > now:
            active_history.append(item)
            continue

        job_root = os.path.join(PROCESSING_ROOT, secure_filename(job_id))
        if os.path.exists(job_root):
            shutil.rmtree(job_root, ignore_errors=True)

    if len(active_history) != len(history):
        save_processing_history(active_history)

def calculate_frame_similarity(frame_a, frame_b):
    gray_a = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)

    if gray_a.shape != gray_b.shape:
        h = min(gray_a.shape[0], gray_b.shape[0])
        w = min(gray_a.shape[1], gray_b.shape[1])
        gray_a = cv2.resize(gray_a, (w, h))
        gray_b = cv2.resize(gray_b, (w, h))

    return float(ssim(gray_a, gray_b))

def video_is_static(cap, sample_frames=8, motion_threshold=30):
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames < sample_frames + 1:
        return True

    sample_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(sample_indices[0]))
    ok, reference_frame = cap.read()
    if not ok:
        return True

    reference_gray = cv2.cvtColor(reference_frame, cv2.COLOR_BGR2GRAY)
    height, width = reference_gray.shape
    changed_pixel_total = 0

    for frame_index in sample_indices[1:]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(reference_gray, gray)
        changed_pixel_total += int(np.sum(diff > 10))

    percentage_changed = (changed_pixel_total / ((sample_frames - 1) * height * width)) * 100
    return percentage_changed < motion_threshold

def load_cache():
    """Load cache from JSON file"""
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_cache(cache_data):
    """Save cache to JSON file"""
    with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as temp_file:
        json.dump(cache_data, temp_file, indent=2)
        temp_path = temp_file.name

    os.replace(temp_path, CACHE_FILE)

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
    if not GEMINI_API_KEY:
        return "API configuration error: GEMINI_API_KEY is missing"

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
        'Content-Type': 'application/json',
        'X-goog-api-key': GEMINI_API_KEY
    }
    
    try:
        response = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except requests.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else None
        if status_code in [401, 403]:
            return "API error: invalid or unauthorized API key"
        if status_code == 429:
            return "API error: rate limit reached, please try again later"
        return "API error: request to Gemini failed"
    except requests.RequestException:
        return "API error: failed to reach Gemini service"
    except (KeyError, IndexError, ValueError):
        return "API error: invalid response from Gemini service"

def get_ai_response(text, feature, prompt_template):
    """Get AI response with caching"""
    if len(text) > MAX_INPUT_LENGTH:
        return f"Input too long. Maximum allowed length is {MAX_INPUT_LENGTH} characters."

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
    data = request.get_json(silent=True) or {}
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
    data = request.get_json(silent=True) or {}
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
    data = request.get_json(silent=True) or {}
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

@app.route('/video-compressor')
def video_compressor():
    """Video compressor page"""
    return render_template('video_compressor.html')

@app.route('/frame-extractor-unique')
def frame_extractor_unique():
    """Unique-frame extractor page"""
    return render_template('frame_extractor_unique.html')

@app.route('/frame-extractor-motion')
def frame_extractor_motion():
    """Motion-based frame extractor page"""
    return render_template('frame_extractor_motion.html')

@app.route('/processing-history')
def processing_history_page():
    """Processing history page"""
    return render_template('processing_history.html')

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
    data = request.get_json(silent=True) or {}
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

@app.route('/api/video-compress', methods=['POST'])
def api_video_compress():
    """Compress uploaded videos using FFmpeg"""
    if shutil.which('ffmpeg') is None:
        return jsonify({'error': 'FFmpeg not found. Install FFmpeg and add it to your PATH.'}), 400

    files = request.files.getlist('videos')
    if not files:
        return jsonify({'error': 'Please upload at least one video file'}), 400

    preset_name = (request.form.get('preset') or 'balanced').strip().lower()
    preset_map = {
        'maximum': {'crf': '28', 'preset': 'slow'},
        'balanced': {'crf': '23', 'preset': 'medium'},
        'fast': {'crf': '20', 'preset': 'fast'}
    }
    selected_preset = preset_map.get(preset_name, preset_map['balanced'])

    job_id, _, uploads_dir, output_dir = create_job_dirs()

    results = []
    compressed_count = 0

    for file in files:
        if not file or not file.filename:
            continue
        if not is_allowed_video(file.filename):
            results.append({'file': file.filename, 'status': 'error', 'message': 'Unsupported video format'})
            continue

        safe_name = secure_filename(file.filename)
        input_path = os.path.join(uploads_dir, safe_name)
        stem = Path(safe_name).stem
        output_name = f"{stem}_compressed.mp4"
        output_path = os.path.join(output_dir, output_name)
        file.save(input_path)

        command = [
            'ffmpeg', '-y', '-i', input_path,
            '-c:v', 'libx265',
            '-preset', selected_preset['preset'],
            '-crf', selected_preset['crf'],
            '-c:a', 'aac', '-b:a', '128k',
            output_path
        ]

        process = subprocess.run(command, capture_output=True, text=True)
        if process.returncode != 0 or not os.path.exists(output_path):
            results.append({'file': safe_name, 'status': 'error', 'message': 'Compression failed'})
            continue

        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(output_path)
        reduction = max(0.0, ((original_size - compressed_size) / original_size) * 100) if original_size > 0 else 0.0

        compressed_count += 1
        results.append({
            'file': safe_name,
            'status': 'ok',
            'original_mb': round(original_size / (1024 * 1024), 2),
            'compressed_mb': round(compressed_size / (1024 * 1024), 2),
            'reduction_percent': round(reduction, 2)
        })

    if compressed_count == 0:
        return jsonify({'error': 'No files were compressed successfully', 'results': results}), 400

    zip_path = os.path.join(PROCESSING_ROOT, job_id, 'results.zip')
    create_zip_from_directory(output_dir, zip_path)
    register_processing_job('Premium Video Compressor', job_id, len(files), compressed_count)

    return jsonify({
        'message': f'{compressed_count} file(s) compressed successfully',
        'results': results,
        'download_url': f'/api/download/{job_id}'
    })

@app.route('/api/frame-extract-unique', methods=['POST'])
def api_frame_extract_unique():
    """Extract only unique frames using SSIM similarity check"""
    if not CV_PACKAGES_AVAILABLE:
        return jsonify({'error': 'opencv-python, scikit-image, and numpy are required for this tool.'}), 400

    files = request.files.getlist('videos')
    if not files:
        return jsonify({'error': 'Please upload at least one video file'}), 400

    threshold_raw = request.form.get('threshold', '0.95').strip()
    try:
        similarity_threshold = float(threshold_raw)
    except ValueError:
        return jsonify({'error': 'Threshold must be a number between 0.5 and 0.999'}), 400

    if similarity_threshold < 0.5 or similarity_threshold > 0.999:
        return jsonify({'error': 'Threshold must be between 0.5 and 0.999'}), 400

    job_id, _, uploads_dir, output_dir = create_job_dirs()
    summary = []
    processed = 0

    for file in files:
        if not file or not file.filename:
            continue
        if not is_allowed_video(file.filename):
            summary.append({'file': file.filename, 'status': 'error', 'message': 'Unsupported video format'})
            continue

        safe_name = secure_filename(file.filename)
        input_path = os.path.join(uploads_dir, safe_name)
        file.save(input_path)

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            summary.append({'file': safe_name, 'status': 'error', 'message': 'Could not open video'})
            continue

        video_stem = Path(safe_name).stem
        video_output_dir = os.path.join(output_dir, video_stem)
        os.makedirs(video_output_dir, exist_ok=True)

        frame_index = 0
        saved_count = 0
        previous_saved = None

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame_index += 1
            if previous_saved is None:
                saved_count += 1
                out_path = os.path.join(video_output_dir, f'{video_stem}_{saved_count}.png')
                cv2.imwrite(out_path, frame)
                previous_saved = frame.copy()
                continue

            similarity = calculate_frame_similarity(frame, previous_saved)
            if similarity < similarity_threshold:
                saved_count += 1
                out_path = os.path.join(video_output_dir, f'{video_stem}_{saved_count}.png')
                cv2.imwrite(out_path, frame)
                previous_saved = frame.copy()

        cap.release()
        processed += 1
        summary.append({
            'file': safe_name,
            'status': 'ok',
            'frames_saved': saved_count,
            'threshold': similarity_threshold
        })

    if processed == 0:
        return jsonify({'error': 'No videos were processed successfully', 'results': summary}), 400

    zip_path = os.path.join(PROCESSING_ROOT, job_id, 'results.zip')
    create_zip_from_directory(output_dir, zip_path)
    register_processing_job('Unique Frame Extractor', job_id, len(files), processed)

    return jsonify({
        'message': f'{processed} video(s) processed',
        'results': summary,
        'download_url': f'/api/download/{job_id}'
    })

@app.route('/api/frame-extract-motion', methods=['POST'])
def api_frame_extract_motion():
    """Extract one frame for static videos or many for dynamic videos"""
    if not CV_PACKAGES_AVAILABLE:
        return jsonify({'error': 'opencv-python and numpy are required for this tool.'}), 400

    files = request.files.getlist('videos')
    if not files:
        return jsonify({'error': 'Please upload at least one video file'}), 400

    threshold_raw = request.form.get('motion_threshold', '30').strip()
    interval_raw = request.form.get('frame_interval', '1').strip()

    try:
        motion_threshold = float(threshold_raw)
    except ValueError:
        return jsonify({'error': 'Motion threshold must be a number'}), 400

    try:
        frame_interval = int(interval_raw)
    except ValueError:
        return jsonify({'error': 'Frame interval must be an integer'}), 400

    if frame_interval < 1 or frame_interval > 120:
        return jsonify({'error': 'Frame interval must be between 1 and 120'}), 400

    job_id, _, uploads_dir, output_dir = create_job_dirs()
    summary = []
    processed = 0

    for file in files:
        if not file or not file.filename:
            continue
        if not is_allowed_video(file.filename):
            summary.append({'file': file.filename, 'status': 'error', 'message': 'Unsupported video format'})
            continue

        safe_name = secure_filename(file.filename)
        input_path = os.path.join(uploads_dir, safe_name)
        file.save(input_path)

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            summary.append({'file': safe_name, 'status': 'error', 'message': 'Could not open video'})
            continue

        video_stem = Path(safe_name).stem
        video_output_dir = os.path.join(output_dir, video_stem)
        os.makedirs(video_output_dir, exist_ok=True)

        static_video = video_is_static(cap, sample_frames=8, motion_threshold=motion_threshold)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        saved_count = 0
        mode = 'static'

        if static_video:
            ok, frame = cap.read()
            if ok:
                saved_count = 1
                out_path = os.path.join(video_output_dir, f'{video_stem}_frame.jpg')
                cv2.imwrite(out_path, frame)
        else:
            mode = 'dynamic'
            frame_index = 0
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                if frame_index % frame_interval == 0:
                    out_path = os.path.join(video_output_dir, f'{video_stem}_frame{saved_count:04d}.jpg')
                    cv2.imwrite(out_path, frame)
                    saved_count += 1
                frame_index += 1

        cap.release()
        processed += 1
        summary.append({
            'file': safe_name,
            'status': 'ok',
            'mode': mode,
            'frames_saved': saved_count,
            'frame_interval': frame_interval
        })

    if processed == 0:
        return jsonify({'error': 'No videos were processed successfully', 'results': summary}), 400

    zip_path = os.path.join(PROCESSING_ROOT, job_id, 'results.zip')
    create_zip_from_directory(output_dir, zip_path)
    register_processing_job('Motion Frame Extractor', job_id, len(files), processed)

    return jsonify({
        'message': f'{processed} video(s) processed',
        'results': summary,
        'download_url': f'/api/download/{job_id}'
    })

@app.route('/api/processing-history', methods=['GET'])
def api_processing_history():
    """Return currently active processing history items."""
    cleanup_expired_processing_jobs()
    history = load_processing_history()
    return jsonify({
        'retention_minutes': PROCESSING_RETENTION_MINUTES,
        'items': history
    })

@app.route('/api/processing-history', methods=['DELETE'])
def api_clear_processing_history():
    """Delete all processing history and generated job files immediately."""
    history = load_processing_history()

    for item in history:
        job_id = item.get('job_id')
        if not job_id:
            continue
        job_root = os.path.join(PROCESSING_ROOT, secure_filename(job_id))
        if os.path.exists(job_root):
            shutil.rmtree(job_root, ignore_errors=True)

    save_processing_history([])
    return jsonify({'message': 'Processing history cleared successfully'})

@app.route('/api/download/<job_id>', methods=['GET'])
def api_download(job_id):
    """Download generated ZIP file for a processing job"""
    cleanup_expired_processing_jobs()
    safe_job_id = secure_filename(job_id)
    zip_path = os.path.join(PROCESSING_ROOT, safe_job_id, 'results.zip')

    if not os.path.exists(zip_path):
        return jsonify({'error': 'Result file not found'}), 404

    return send_file(zip_path, as_attachment=True, download_name=f'{safe_job_id}_results.zip')

@app.route('/api/todo', methods=['POST'])
def api_todo():
    """API endpoint for to-do list generation"""
    data = request.get_json(silent=True) or {}
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
    
    flask_debug = os.environ.get('FLASK_DEBUG', 'false').strip().lower() == 'true'
    app.run(debug=flask_debug)