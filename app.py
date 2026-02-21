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

def get_filtered_article(max_attempts=50):
    print(f"--- Starting Search for Article ---")
    for attempt in range(max_attempts):
        try:
            response = requests.get(WIKI_RANDOM_URL, timeout=5)
            data = response.json()
            title = data.get("title", "")
            extract = data.get("extract", "")

            # DEBUG PRINT: See what we are getting
            print(f"Attempt {attempt}: Found '{title}'")

            if not is_valid_title(title):
                print(f"   REJECTED: Title too long or has special chars")
                continue

            if not extract or len(extract) < 100:
                print(f"   REJECTED: Extract too short")
                continue

            # If we got here, it passed!
            sentences = [s.strip() + "." for s in re.split(r"\.\s+", extract) if len(s.strip()) > 5]
            masked_sentences = [mask_title_in_sentence(title, s) for s in sentences]
            
            print(f"✅ SUCCESS: Selected '{title}'")
            return {"title": title, "sentences": masked_sentences}

        except Exception as e:
            print(f"   ERROR on attempt {attempt}: {e}")
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