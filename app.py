from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import re
import time

app = Flask(__name__)
# Adjust CORS to be specific if you deploy, but this is fine for dev
CORS(app)

WIKI_RANDOM_URL = "https://en.wikipedia.org/api/rest_v1/page/random/summary"

def is_valid_title(title):
    """Keep it simple: Max 4 words, and ignore 'List of...' pages."""
    if not title or len(title.split()) > 4:
        return False
    if title.startswith("List of"): # 'List of' articles aren't fun for this game
        return False
    return True

def mask_title_in_sentence(title, sentence):
    """Replaces words from the title with underscores in the sentence."""
    # Sort title words by length (longest first) to avoid partial replacement issues
    title_words = sorted(title.split(), key=len, reverse=True)
    
    masked_sentence = sentence
    for word in title_words:
        if len(word) < 2: continue # Don't mask single letters like 'a'
        # Use regex to find whole words only
        word_regex = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        masked_sentence = word_regex.sub('_' * len(word), masked_sentence)

    return masked_sentence

def is_valid_title(title):
    # Allow almost everything, just avoid internal Wikipedia pages
    if not title or ":" in title: # Rejects 'Category:Science' or 'File:Image.jpg'
        return False
    # Relax word count to 6 words
    if len(title.split()) > 6:
        return False
    return True

def get_filtered_article(max_attempts=50):
    for attempt in range(max_attempts):
        try:
            # We add a User-Agent to prevent Wikipedia from thinking we are a bot
            headers = {'User-Agent': 'WikiGuessGame/1.0'}
            response = requests.get(WIKI_RANDOM_URL, headers=headers, timeout=5)
            
            if response.status_code != 200:
                continue

            data = response.json()
            title = data.get("title", "")
            extract = data.get("extract", "")

            # LOGGING: See exactly what is happening in Render Logs
            print(f"Checking: {title}")

            if not is_valid_title(title):
                continue

            if not extract or len(extract) < 50: # Very low bar for length
                continue

            # CLEANUP: Remove parentheses and citations like [1] or (born 1980)
            clean_extract = re.sub(r'\([^)]*\)', '', extract)
            clean_extract = re.sub(r'\[[0-9]*\]', '', clean_extract)
            
            # SPLITTING: Split into sentences
            sentences = [s.strip() + "." for s in re.split(r"\.\s+", clean_extract) if len(s.strip()) > 5]
            
            if not sentences:
                continue

            # MASKING: Only use the first 4 sentences
            masked_sentences = [mask_title_in_sentence(title, s) for s in sentences[:4]]
            
            return {"title": title, "sentences": masked_sentences}

        except Exception as e:
            print(f"Error on attempt {attempt}: {e}")
            continue

    return {"error": "No suitable articles found after 50 tries."}
    
@app.route("/get_article", methods=["GET"])
def get_article():
    article = get_filtered_article()
    
    # FIX: Corrected the print statement to use the dictionary keys
    if "title" in article:
        print(f"✅ Found article: {article['title']}")
    else:
        print("❌ Failed to find article")
        
    return jsonify(article)

@app.route("/check_guess", methods=["POST"])
def check_guess():
    data = request.json
    if not data or "guess" not in data or "title" not in data:
        return jsonify({"error": "Missing data"}), 400
        
    correct = data["guess"].strip().lower() == data["title"].strip().lower()
    return jsonify({"correct": correct})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)