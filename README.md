# GTM Cold Email Personalizer

An interactive Flask web application and CLI tool that generates highly personalized, high-conversion cold email openers. 

This project was built to demonstrate advanced prompt engineering and production-grade engineering for the **Synapse AI GTM Agent** showcase. It leverages **Gemini 2.5** via OpenRouter to generate concise, highly specific 3-sentence openers based on real prospect data (LinkedIn highlights and company milestones).

---

## Key Features

- **2-Shot Prompting:** Uses highly optimized few-shot examples to maintain a peer-to-peer, confident tone under 50 words.
- **Structured JSON Output:** Bypasses LLM conversational filler and parses raw responses into programmatically safe formats.
- **Web UI & CLI Modes:** A polished, modern dark-mode Flask UI for live demos, alongside a high-throughput CLI tool.
- **Negative Constraints:** Explicitly filters out cliché sales phrases like *"I hope this finds you well"* or *"I noticed your profile"*.

---

## Demo

https://github.com/Saad-dev-io/gtm-cold-email-personalizer/raw/main/demo.mp4

---

## Quick Start

### Prerequisites
- Python 3.10+
- An OpenRouter API Key

### Setup & Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/gtm-cold-email-personalizer.git
cd gtm-cold-email-personalizer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
# Create a .env file in the root directory:
echo OPENROUTER_API_KEY=your_api_key_here > .env
```

### Running the App

#### Option A: Web Interface (Recommended)
Launch the Flask development server to run the interactive dashboard:
```bash
python app.py
```
Open **`http://localhost:5000`** in your browser. You can manually enter prospect data or click **"Load Sample"** to cycle through mock LinkedIn profiles.

#### Option B: Command Line Interface (CLI)
Process batch prospects from `prospects.json` and generate an outreach file:
```bash
python email_generator.py
```
Results will display in the console and automatically save to `generated_outreach.txt`.

---

## Technical Architecture

```
[prospects.json] ──> [email_generator.py] ──> [OpenRouter API]
                            │                     │
                            ├──> Flask UI         └──> JSON Parser
                            └──> Terminal              │
                                                       └──> [generated_outreach.txt]
```

### Core Technologies
- **Backend:** Python, Flask, python-dotenv
- **LLM Integration:** OpenAI SDK (configured for OpenRouter / Gemini 2.5 Flash)
- **Frontend:** Vanilla HTML5, CSS3 (Custom Glassmorphism Design System), Modern JS
- **Terminal:** Colorama (formatted ASCII output)

---

## Project Structure

```
├── app.py                  # Flask web controller & API routes
├── email_generator.py      # Core AI engine, prompt builder, & CLI entry point
├── prospects.json          # Pre-configured mock prospect profiles
├── requirements.txt        # Package dependencies
├── .env                    # Local environment secrets (gitignored)
├── .gitignore              # Build and secret exclusion configurations
├── static/
│   ├── style.css           # Custom dark-mode styles
│   └── script.js           # Fetch API & clipboard integration
└── templates/
    └── index.html          # Web dashboard layout
<<<<<<< HEAD
```

