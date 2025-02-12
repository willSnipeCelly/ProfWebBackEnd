from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import re
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://wkeiideas.com/projects/wkeiipedia"}})

WIKI_RANDOM_URL = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
WIKI_PAGEVIEWS_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{}/monthly/20240101/20250101"

def is_valid_title(title):
    """Checks if the title meets requirements (4 words max, no special characters)."""
    if len(title.split()) > 4:
        return False
    if re.search(r"[^a-zA-Z0-9\s]", title):  # Exclude special characters
        return False
    return True

def get_page_views(title):
    """Fetches the page views for a given Wikipedia article title."""
    formatted_title = title.replace(" ", "_")  # URL-friendly format
    url = WIKI_PAGEVIEWS_URL.format(formatted_title)
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            total_views = sum(item["views"] for item in data["items"])
            return total_views
    return 0  # If API fails, assume low views

def mask_title_in_sentence(title, sentence):
    """Replaces words from the title with underscores in the sentence."""
    title_words = title.split()
    
    for word in title_words:
        word_regex = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        sentence = word_regex.sub('_' * len(word), sentence)

    return sentence

def get_filtered_article():
    """Fetches and filters a Wikipedia article until it meets all conditions."""
    while True:
        response = requests.get(WIKI_RANDOM_URL)
        if response.status_code != 200:
            time.sleep(1)  # Wait and retry in case of API failure
            continue

        data = response.json()
        title = data.get("title", "")

        if not is_valid_title(title):
            continue  # Skip invalid titles
        
        views = get_page_views(title)
        if views < 1000:
            continue  # Skip unpopular articles

        sentences = re.split(r"(?<=\.)\s", data.get("extract", ""))  # Split into sentences
        if len(sentences) < 3:
            continue  # Skip articles with too few sentences
        
        # Mask title words in sentences
        masked_sentences = [mask_title_in_sentence(title, sentence) for sentence in sentences]

        return {"title": title, "sentences": masked_sentences}

@app.route("/get_article", methods=["GET"])
def get_article():
    """API route to get a filtered article."""
    article = get_filtered_article()
    return jsonify(article)

@app.route("/check_guess", methods=["POST"])
def check_guess():
    """API route to check user's guess."""
    data = request.json
    correct = data["guess"].strip().lower() == data["title"].strip().lower()
    return jsonify({"correct": correct})

if __name__ == "__main__":
    app.run(debug=True)
