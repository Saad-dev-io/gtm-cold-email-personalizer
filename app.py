"""
GTM Cold Email Personalizer — Flask Web Server
================================================
Serves the premium web UI and exposes a /generate API
endpoint that reuses the existing prompt engineering logic.

Run:  python app.py
Open: http://localhost:5000
"""

import json
import os
import sys

from flask import Flask, render_template, request, jsonify

# Reuse existing logic from email_generator.py
from email_generator import (
    configure_api,
    build_system_prompt,
    build_few_shot_examples,
    build_user_prompt,
    parse_llm_response,
    count_words,
    REQUIRED_FIELDS,
    OPENROUTER_MODEL,
    MAX_RETRIES,
)
from openai import OpenAI
import time

# ─── Fix Windows console encoding ────
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


app = Flask(__name__)

# Initialize the API client once at startup
client = None


def get_client() -> OpenAI:
    """Lazy-initialize and cache the OpenRouter client."""
    global client
    if client is None:
        client = configure_api()
    return client


# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main web UI."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    Generate a personalized cold email for a single prospect.

    Expects JSON body:
    {
        "name": "...",
        "role": "...",
        "company": "...",
        "company_industry": "...",
        "recent_achievement": "...",
        "linkedin_headline": "..."
    }

    Returns JSON:
    {
        "subject_line": "...",
        "opening_lines": "...",
        "word_count": 42
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate required fields
        missing = [f for f in REQUIRED_FIELDS if not data.get(f, "").strip()]
        if missing:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing)}"
            }), 400

        # Build the prompt and call the LLM
        api_client = get_client()
        system_prompt = build_system_prompt()
        few_shot = build_few_shot_examples()
        user_prompt = build_user_prompt(data)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = api_client.chat.completions.create(
                    model=OPENROUTER_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{few_shot}\n\n{user_prompt}"}
                    ],
                    temperature=0.7,
                    top_p=0.9,
                    max_tokens=300,
                )
                result = parse_llm_response(response.choices[0].message.content)
                result["word_count"] = count_words(result["opening_lines"])
                return jsonify(result)

            except ValueError as e:
                if attempt < MAX_RETRIES:
                    time.sleep(1)
                else:
                    return jsonify({
                        "error": f"Failed to parse AI response after {MAX_RETRIES} attempts. Please try again."
                    }), 500

            except Exception as e:
                if attempt < MAX_RETRIES:
                    time.sleep(2)
                else:
                    return jsonify({
                        "error": f"API error: {str(e)}"
                    }), 500

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  🚀 GTM Cold Email Personalizer — Web UI")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Open in your browser: http://localhost:5000")
    print("  Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
