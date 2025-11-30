from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

# ====== GEMINI API KEY ======
# Read from environment variable GEMINI_API_KEY
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GEMINI_MODEL_URL = (
    "https://generativestorybooks.googleapis.com/v1beta/models/"
    "gemini-2.5-flash-preview-09-2025:generateContent"
)


def call_gemini(user_query: str, system_prompt: str) -> str:
    """
    Call Gemini API and return generated text.
    If API key is missing, return a friendly error.
    """
    if not GEMINI_API_KEY:
        return (
            "Error: GEMINI_API_KEY is not set. "
            "Set it in your environment to enable AI features."
        )

    params = {"key": GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
    }

    try:
        resp = requests.post(
            GEMINI_MODEL_URL,
            params=params,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        candidate = (data.get("candidates") or [{}])[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        if parts and "text" in parts[0]:
            return parts[0]["text"]

        return "Error: No valid text returned from Gemini."

    except requests.exceptions.RequestException as e:
        return f"Error calling Gemini API: {e}"


@app.route("/")
def index():
    # Renders templates/index.html
    return render_template("index.html")


@app.route("/api/bio", methods=["POST"])
def api_bio():
    """
    Generate portfolio 'About Me' bio.
    Expects JSON: { "keywords": "..." }
    """
    data = request.get_json(silent=True) or {}
    keywords = data.get("keywords", "").strip()

    if not keywords:
        return jsonify({"error": "No keywords provided."}), 400

    system_prompt = (
        "You are a professional resume writer. Write an engaging, first-person "
        "'About Me' section for a personal portfolio. The tone should be passionate "
        "and professional. Base it on the following keywords. Keep it to 3-4 "
        "concise paragraphs."
    )

    user_query = f"Keywords: {keywords}"
    text = call_gemini(user_query, system_prompt)
    return jsonify({"text": text})


@app.route("/api/project", methods=["POST"])
def api_project():
    """
    Generate a project idea.
    Expects JSON: { "role": "..." }
    """
    data = request.get_json(silent=True) or {}
    role = data.get("role", "AI Software Engineer").strip() or "AI Software Engineer"

    system_prompt = (
        "You are a tech mentor. Suggest a new, impressive portfolio project idea. "
        "Respond with a title, a 1-2 sentence description, and 3-4 key technologies. "
        "Format your response in simple HTML "
        "(e.g., <h3>Title</h3><p>Description</p>"
        "<p><strong>Tech:</strong> Tech 1, Tech 2</p>)."
    )

    user_query = f"Role: {role}"
    html = call_gemini(user_query, system_prompt)
    return jsonify({"html": html})


if __name__ == "__main__":
    import os
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


