from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import render_template, send_from_directory
import re
from collections import Counter
import json
import requests
import time
from functools import wraps
import os
import threading

app = Flask(__name__)
CORS(app)

# Simple in-memory cache
word_cache = {}
CACHE_SIZE_LIMIT = 1000  # Limit cache size to prevent memory issues

# Rate limiting variables
last_api_call_time = 0
api_call_lock = threading.Lock()
MIN_TIME_BETWEEN_CALLS = 1.0 / 9.5  # Minimum time between API calls (to stay under 9.5 requests/second)

# Fallback frequency data (small dataset for when API is unavailable)
FALLBACK_FREQUENCIES = {
    'the': 5.02, 'of': 3.88, 'and': 3.46, 'to': 2.48, 'a': 2.44, 'in': 2.42, 'is': 2.15, 
    'it': 1.89, 'you': 1.89, 'that': 1.85, 'he': 1.76, 'was': 1.73, 'for': 1.72, 'on': 1.64, 
    'are': 1.63, 'as': 1.54, 'with': 1.53, 'his': 1.49, 'they': 1.46, 'i': 1.40, 'at': 1.29, 
    'be': 1.28, 'this': 1.27, 'have': 1.25, 'from': 1.24, 'or': 1.21, 'had': 1.19, 'by': 1.18, 
    'not': 1.12, 'word': 1.06, 'but': 1.05, 'what': 1.05, 'some': 1.05, 'we': 1.02, 'can': 1.02, 
    'out': 1.01, 'other': 1.01, 'were': 1.01, 'all': 1.00, 'there': 0.99, 'when': 0.99, 'up': 0.98, 
    'use': 0.98, 'your': 0.97, 'how': 0.97, 'said': 0.95, 'an': 0.94, 'each': 0.93, 'she': 0.93, 
    'which': 0.93, 'do': 0.92, 'their': 0.90, 'time': 0.88, 'if': 0.87, 'will': 0.87, 'way': 0.86, 
    'about': 0.85, 'many': 0.85, 'then': 0.85, 'them': 0.84, 'would': 0.84, 'write': 0.83, 'like': 0.83, 
    'so': 0.83, 'these': 0.83, 'her': 0.82, 'long': 0.80, 'make': 0.79, 'thing': 0.79, 'see': 0.79, 
    'him': 0.78, 'two': 0.78, 'has': 0.77, 'look': 0.77, 'more': 0.77, 'day': 0.77, 'could': 0.76, 
    'go': 0.76, 'come': 0.75, 'did': 0.75, 'my': 0.75, 'sound': 0.74, 'no': 0.74, 'most': 0.74, 
    'number': 0.74, 'who': 0.74, 'over': 0.74, 'know': 0.73, 'water': 0.73, 'than': 0.72, 'call': 0.72, 
    'first': 0.71, 'people': 0.71, 'may': 0.71, 'down': 0.70, 'side': 0.70, 'been': 0.69, 'now': 0.69, 
    'find': 0.68, 'any': 0.67, 'new': 0.67, 'work': 0.67, 'part': 0.66, 'take': 0.66, 'get': 0.66, 
    'place': 0.65, 'made': 0.65, 'live': 0.65, 'where': 0.65, 'after': 0.64, 'back': 0.64, 'little': 0.64, 
    'only': 0.64, 'round': 0.64, 'man': 0.64, 'year': 0.63, 'came': 0.63, 'show': 0.63, 'every': 0.63, 
    'good': 0.62, 'me': 0.62, 'give': 0.62, 'our': 0.62, 'under': 0.62, 'name': 0.61, 'very': 0.61, 
    'through': 0.61, 'just': 0.61, 'form': 0.60, 'sentence': 0.60, 'great': 0.59, 'think': 0.59, 
    'say': 0.59, 'help': 0.59, 'low': 0.59, 'line': 0.58, 'differ': 0.58, 'turn': 0.58, 'cause': 0.58, 
    'much': 0.58, 'mean': 0.58, 'before': 0.57, 'move': 0.57, 'right': 0.57, 'boy': 0.56, 'old': 0.56, 
    'too': 0.56, 'same': 0.56, 'tell': 0.56, 'does': 0.56, 'set': 0.56, 'three': 0.55, 'want': 0.55, 
    'air': 0.55, 'well': 0.55, 'also': 0.54, 'play': 0.54, 'small': 0.54, 'end': 0.54, 'put': 0.54, 
    'home': 0.54, 'read': 0.53, 'hand': 0.53, 'port': 0.53, 'large': 0.53, 'spell': 0.53, 'add': 0.53, 
    'even': 0.53, 'land': 0.53, 'here': 0.53, 'must': 0.53, 'big': 0.52, 'high': 0.52, 'such': 0.52, 
    'follow': 0.52, 'act': 0.52, 'why': 0.52, 'ask': 0.52, 'men': 0.51, 'change': 0.51, 'went': 0.51, 
    'light': 0.51, 'kind': 0.51, 'off': 0.51, 'need': 0.51, 'house': 0.51, 'picture': 0.51, 'try': 0.50, 
    'us': 0.50, 'again': 0.50, 'animal': 0.50, 'point': 0.50, 'mother': 0.50, 'world': 0.50, 'near': 0.50, 
    'build': 0.50, 'self': 0.50, 'earth': 0.50, 'father': 0.49, 'head': 0.49, 'stand': 0.49, 'own': 0.49, 
    'page': 0.49, 'should': 0.49, 'country': 0.49, 'found': 0.49, 'answer': 0.49, 'school': 0.49, 
    'grow': 0.49, 'study': 0.49, 'still': 0.49, 'learn': 0.49, 'plant': 0.48, 'cover': 0.48, 'food': 0.48, 
    'sun': 0.48, 'four': 0.48, 'between': 0.48, 'state': 0.48, 'keep': 0.48, 'eye': 0.48, 'never': 0.48, 
    'last': 0.48, 'let': 0.48, 'thought': 0.48, 'city': 0.47, 'tree': 0.47, 'cross': 0.47, 'farm': 0.47, 
    'hard': 0.47, 'start': 0.47, 'might': 0.47, 'story': 0.47, 'saw': 0.47, 'far': 0.47, 'sea': 0.47, 
    'draw': 0.46, 'left': 0.46, 'late': 0.46, 'run': 0.46, 'don\'t': 0.46, 'while': 0.46, 'press': 0.46, 
    'close': 0.46, 'night': 0.46, 'real': 0.46, 'life': 0.46, 'few': 0.46, 'north': 0.46, 'open': 0.46, 
    'seem': 0.46, 'together': 0.46, 'next': 0.45, 'white': 0.45, 'children': 0.45, 'begin': 0.45, 
    'got': 0.45, 'walk': 0.45, 'example': 0.45, 'ease': 0.45, 'paper': 0.45, 'group': 0.45, 'often': 0.45, 
    'always': 0.45, 'music': 0.45, 'those': 0.44, 'both': 0.44, 'mark': 0.44, 'book': 0.44, 'letter': 0.44, 
    'until': 0.44, 'mile': 0.44, 'river': 0.44, 'car': 0.44, 'feet': 0.44, 'care': 0.44, 'second': 0.44, 
    'enough': 0.44, 'plain': 0.44, 'girl': 0.44, 'usual': 0.44, 'young': 0.44, 'ready': 0.44, 'above': 0.43, 
    'ever': 0.43, 'red': 0.43, 'list': 0.43, 'though': 0.43, 'feel': 0.43, 'talk': 0.43, 'bird': 0.43, 
    'soon': 0.43, 'body': 0.43, 'dog': 0.43, 'family': 0.43, 'direct': 0.43, 'leave': 0.43, 'song': 0.43, 
    'measure': 0.43, 'door': 0.43, 'product': 0.42, 'black': 0.42, 'short': 0.42, 'numeral': 0.42, 
    'class': 0.42, 'wind': 0.42, 'question': 0.42, 'happen': 0.42, 'complete': 0.42, 'ship': 0.42, 
    'area': 0.42, 'half': 0.42, 'rock': 0.42, 'order': 0.42, 'fire': 0.42, 'south': 0.42, 'problem': 0.41, 
    'piece': 0.41, 'told': 0.41, 'knew': 0.41, 'pass': 0.41, 'since': 0.41, 'top': 0.41, 'whole': 0.41, 
    'king': 0.41, 'space': 0.41, 'heard': 0.41, 'best': 0.41, 'hour': 0.41, 'better': 0.41, 'during': 0.41, 
    'hundred': 0.41, 'five': 0.41, 'remember': 0.40, 'step': 0.40, 'early': 0.40, 'hold': 0.40, 'west': 0.40, 
    'ground': 0.40, 'interest': 0.40, 'reach': 0.40, 'fast': 0.40, 'verb': 0.40, 'sing': 0.40, 'listen': 0.40, 
    'six': 0.40, 'table': 0.39, 'travel': 0.39, 'less': 0.39, 'morning': 0.39, 'ten': 0.39, 'simple': 0.39, 
    'several': 0.39, 'vowel': 0.39, 'toward': 0.39, 'war': 0.39, 'lay': 0.39, 'against': 0.39, 'pattern': 0.39, 
    'slow': 0.39, 'center': 0.39, 'love': 0.39, 'person': 0.39, 'money': 0.39, 'serve': 0.39, 'appear': 0.39, 
    'road': 0.39, 'map': 0.39, 'rain': 0.38, 'rule': 0.38, 'govern': 0.38, 'pull': 0.38, 'cold': 0.38, 
    'notice': 0.38, 'voice': 0.38, 'unit': 0.38, 'power': 0.38, 'town': 0.38, 'fine': 0.38, 'certain': 0.38, 
    'fly': 0.38, 'fall': 0.38, 'lead': 0.38, 'cry': 0.38, 'dark': 0.38, 'machine': 0.38, 'note': 0.38, 
    'wait': 0.38, 'plan': 0.38, 'figure': 0.38, 'star': 0.38, 'box': 0.38, 'noun': 0.38, 'field': 0.37, 
    'rest': 0.37, 'correct': 0.37, 'able': 0.37, 'pound': 0.37, 'done': 0.37, 'beauty': 0.37, 'drive': 0.37, 
    'stood': 0.37, 'contain': 0.37, 'front': 0.37, 'teach': 0.37, 'week': 0.37, 'final': 0.37, 'gave': 0.37, 
    'green': 0.37, 'oh': 0.37, 'quick': 0.37, 'develop': 0.37, 'ocean': 0.37, 'warm': 0.37, 'free': 0.37, 
    'minute': 0.37, 'strong': 0.37, 'special': 0.37, 'mind': 0.36, 'behind': 0.36, 'clear': 0.36, 'tail': 0.36, 
    'produce': 0.36, 'fact': 0.36, 'street': 0.36, 'inch': 0.36, 'multiply': 0.36, 'nothing': 0.36, 
    'course': 0.36, 'stay': 0.36, 'wheel': 0.36, 'full': 0.36, 'force': 0.36, 'blue': 0.36, 'object': 0.36, 
    'decide': 0.36, 'surface': 0.36, 'deep': 0.36, 'moon': 0.36, 'island': 0.36, 'foot': 0.36, 'system': 0.36, 
    'busy': 0.36, 'test': 0.36, 'record': 0.36, 'boat': 0.36, 'common': 0.35, 'gold': 0.35, 'possible': 0.35, 
    'plane': 0.35, 'stead': 0.35, 'dry': 0.35, 'wonder': 0.35, 'laugh': 0.35, 'thousands': 0.35, 
    'ago': 0.35, 'ran': 0.35, 'check': 0.35, 'game': 0.35, 'shape': 0.35, 'equate': 0.35, 'hot': 0.35, 
    'miss': 0.35, 'brought': 0.35, 'heat': 0.35, 'snow': 0.35, 'tire': 0.35, 'bring': 0.35, 'yes': 0.35, 
    'distant': 0.35, 'fill': 0.35, 'east': 0.35, 'paint': 0.35, 'language': 0.35, 'among': 0.34
}

def wait_for_rate_limit():
    """Ensure we don't exceed 9.5 API requests per second"""
    global last_api_call_time
    with api_call_lock:
        time_since_last_call = time.time() - last_api_call_time
        if time_since_last_call < MIN_TIME_BETWEEN_CALLS:
            sleep_time = MIN_TIME_BETWEEN_CALLS - time_since_last_call
            time.sleep(sleep_time)
        last_api_call_time = time.time()

def get_frequency_from_api(word):
    """Get word frequency from Datamuse API (frequency per million words) with caching"""
    word_lower = word.lower()
    
    # Check cache first
    if word_lower in word_cache:
        return word_cache[word_lower]
    
    try:
        import requests
        # Enforce rate limiting before making API call
        wait_for_rate_limit()
        
        # Datamuse API call to get word frequency
        url = f"https://api.datamuse.com/words?sp={word_lower}&qe=sp&md=f&max=1"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Check if the response has the expected structure
                first_result = data[0]
                if 'tags' in first_result:
                    # Look for the frequency tag (format: f:frequency_per_million)
                    freq_tags = [tag for tag in first_result['tags'] if tag.startswith('f:')]
                    if freq_tags:
                        # Extract the frequency value (after the 'f:' prefix)
                        freq = float(freq_tags[0][2:])  # Remove 'f:' prefix and convert to float
                        # Add to cache before returning
                        if len(word_cache) < CACHE_SIZE_LIMIT:
                            word_cache[word_lower] = freq
                        return freq  # Frequency per million words
                # If no frequency tag found or tags not available, check for 'freq' field directly
                elif 'freq' in first_result:
                    freq = float(first_result['freq'])
                    # Add to cache before returning
                    if len(word_cache) < CACHE_SIZE_LIMIT:
                        word_cache[word_lower] = freq
                    return freq
            # If no data returned or structure not as expected, use fallback
            freq = FALLBACK_FREQUENCIES.get(word_lower, 0.1)
            if len(word_cache) < CACHE_SIZE_LIMIT:
                word_cache[word_lower] = freq
            return freq
        else:
            # If API call fails, use fallback
            if os.getenv('FLASK_ENV') != 'production':
                print(f"API request failed with status code: {response.status_code}")
            freq = FALLBACK_FREQUENCIES.get(word_lower, 0.1)
            if len(word_cache) < CACHE_SIZE_LIMIT:
                word_cache[word_lower] = freq
            return freq
    except Exception as e:
        # If any error occurs, use fallback
        if os.getenv('FLASK_ENV') != 'production':
            print(f"Error fetching frequency for '{word}': {e}")
            import traceback
            traceback.print_exc()
        freq = FALLBACK_FREQUENCIES.get(word_lower, 0.1)
        if len(word_cache) < CACHE_SIZE_LIMIT:
            word_cache[word_lower] = freq
        return freq

def get_word_frequency(word):
    """Get the frequency of a word using API if available, fallback otherwise."""
    return get_frequency_from_api(word)


def cleanup_cache():
    """Periodically clean up the cache to manage memory"""
    global word_cache
    if len(word_cache) > CACHE_SIZE_LIMIT:
        # Keep only the most recently used entries
        items = list(word_cache.items())[-CACHE_SIZE_LIMIT//2:]  # Keep half of the limit
        word_cache = dict(items)

@app.route('/analyze', methods=['POST'])
def analyze_text():
    data = request.json
    text = data.get('text', '')
    
    # Extract words and their positions in the original text
    tokens = re.finditer(r'\b\w+\b|\s+|[^\w\s]', text)
    results = []
    
    for match in tokens:
        token = match.group()
        start_pos = match.start()
        
        if re.match(r'\w+', token):  # If it's a word
            freq = get_word_frequency(token)
            # Map frequency to color: low freq (rare) = red, high freq (common) = green
            import math
            
            # Use logarithmic scale to handle the wide range of frequencies from Datamuse API
            if freq > 0:
                log_freq = math.log(freq)
            else:
                log_freq = math.log(0.00001)
            
            # Define the log frequency range based on observed Datamuse data
            # Most common English words have frequencies between ~0.001 and ~10000
            log_min = math.log(0.001)  # Adjusted for more realistic minimum
            log_max = math.log(10000.0)  # Adjusted for more realistic maximum
            
            # Calculate the log range
            log_range = log_max - log_min
            
            # Normalize to 0-1 range with clamping
            if log_range > 0:
                normalized_freq = max(0.0, min(1.0, (log_freq - log_min) / log_range))
            else:
                normalized_freq = 0.5
            
            # Apply an inverse transformation to emphasize differences at the extremes
            # This will make very rare words more red and very common words more green
            # Using a sigmoid-like function to enhance the contrast
            if normalized_freq <= 0.5:
                # Enhance the lower half (rare words) - make them more red
                normalized_freq = normalized_freq * 0.7
            else:
                # Enhance the upper half (common words) - make them more green
                normalized_freq = 0.35 + (normalized_freq - 0.5) * 1.3
            
            # Clamp again after transformation
            normalized_freq = max(0.0, min(1.0, normalized_freq))
            
            # Convert to HSL: red (0°) for rare words, green (120°) for common words
            # This creates a clear red-to-green color gradient
            hue = 120 * normalized_freq  # Goes from 0 (red) to 120 (green)
            saturation = 100
            lightness = 50
            
            color = f'hsl({hue:.1f}, {saturation}%, {lightness}%)'
            
            # Determine rarity category based on frequency
            if freq <= 0.1:
                rarity = "Very Rare"
            elif freq <= 1:
                rarity = "Rare"
            elif freq <= 10:
                rarity = "Uncommon"
            elif freq <= 100:
                rarity = "Common"
            else:
                rarity = "Very Common"
            
            results.append({
                'token': token,
                'color': color,
                'frequency': freq,
                'rarity': rarity,
                'position': start_pos
            })
        else:  # If it's not a word (space, punctuation)
            results.append({
                'token': token,
                'color': None,
                'frequency': None,
                'position': start_pos
            })
    
    # Clean up cache periodically to manage memory
    cleanup_cache()
    
    return jsonify(results)

# Route to serve the main HTML page
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Route to serve static files (CSS, JS)
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
