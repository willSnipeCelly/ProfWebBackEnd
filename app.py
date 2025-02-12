from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from any origin

@app.route("/get_article", methods=["GET"])
def get_article():
    return jsonify({"title": "Example Title", "sentences": ["This is a test sentence."]})

@app.route("/check_guess", methods=["POST"])
def check_guess():
    data = request.json
    return jsonify({"correct": data["guess"].lower() == "example title"})

if __name__ == "__main__":
    app.run(debug=True)
