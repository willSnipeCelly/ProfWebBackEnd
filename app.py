from flask import Flask, jsonify, request
import requests
import random

app = Flask(__name__)

@app.route('/get_article', methods=['GET'])
def get_article():
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "random",
        "grnnamespace": 0,
        "prop": "extracts",
        "explaintext": True,
        "format": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()
    page = next(iter(data['query']['pages'].values()))
    title = page['title']
    sentences = page['extract'].split('. ')
    return jsonify({"title": title, "sentences": sentences})

@app.route('/check_guess', methods=['POST'])
def check_guess():
    data = request.json
    title = data['title']
    guess = data['guess']
    if guess.lower() == title.lower():
        return jsonify({"correct": True})
    return jsonify({"correct": False})
