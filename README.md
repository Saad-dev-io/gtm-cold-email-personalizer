# 🚀 GTM Cold Email Personalizer

> Generate highly personalized, 3-sentence cold email openers using **Few-Shot Prompting** and **Google Gemini via OpenRouter** — built to demonstrate core GTM Agent capabilities.

---

## 🎯 Why I Built This

This project directly addresses a core responsibility of the **Synapse AI GTM Agent role**: the ability to *"generate the first 3 sentences of a cold email that reference specific, verifiable facts about the prospect."*

Rather than writing generic outreach, this tool uses **advanced prompt engineering** to produce emails that:
- Reference specific, verifiable achievements
- Maintain a confident, peer-to-peer tone
- Stay under 50 words
- Create genuine curiosity

### Zero-Shot vs Few-Shot Prompting

| Technique | How It Works | Why It Matters |
|-----------|-------------|----------------|
| **Zero-Shot** | Give the LLM a task with no examples | Too unpredictable — output quality varies wildly |
| **Few-Shot** | Provide 2-3 examples of ideal input→output pairs | The model learns the exact tone, structure, and length from examples |

This project uses **2-shot prompting** — providing two carefully crafted example emails that teach the model the *exact pattern* before generating for real prospects.

---

## 🏗️ How It Works

```
prospects.json          →    email_generator.py    →    Terminal Output
(Mock LinkedIn Data)         ┌─────────────────┐        (Colored & Formatted)
                             │ 1. System Prompt │
4 Prospect Profiles          │    (Persona)     │        generated_outreach.txt
with:                        │ 2. Few-Shot      │        (Saved File)
  • Name & Role              │    (2 Examples)  │
  • Company & Industry       │ 3. Prospect Data │
  • Recent Achievement       │    (Dynamic)     │
  • LinkedIn Headline        └────────┬────────┘
                                      │
                             OpenRouter API (Gemini)
                                      │
                              Structured JSON
                              (subject + email)
```

### Prompt Engineering Strategy

1. **Persona Engineering**: The system prompt assigns the LLM the role of an *"elite B2B tech sales closer"* — activating domain-specific communication patterns.

2. **Few-Shot Examples**: Two hand-crafted example input→output pairs demonstrate the exact tone, structure, and word count we expect.

3. **Structured Output**: The LLM is instructed to return a JSON object with `subject_line` and `opening_lines` keys, making the output programmatically parseable.

4. **Negative Constraints**: Explicit rules ban cliché phrases like *"I hope this finds you well"* — forcing the model to be creative and genuine.

---

## 🖥️ Two Ways to Use

### Option 1: Web UI (Recommended)

A premium dark-mode web interface — perfect for demos and non-technical users.

```bash
# Start the web server
python app.py

# Open in your browser
http://localhost:5000
```

**Features:**
- 🎨 Premium dark-mode UI with glassmorphism design
- 📝 Simple form to enter prospect details
- ✨ One-click email generation with AI
- 📋 Copy-to-clipboard with visual feedback
- 📜 Session history to track all generated emails
- 🔄 "Load Sample" button for instant demos

### Option 2: CLI Mode

Process all prospects from `prospects.json` in your terminal.

```bash
python email_generator.py
```

---

## 📋 Sample Output

```
  ==========================================================
  PROSPECT 1/4: Sarah Chen
  VP of Engineering @ NovaTech Solutions
  ==========================================================

  [Achievement] Led the launch of an AI-powered customer
     support platform that reduced ticket resolution time by 40%

  [Subject] Your AI support platform × autonomous agents

  [Email]
     "That 40% reduction in ticket resolution is the real
      deal, Sarah — most teams talk AI, your team shipped it.
      At Synapse, we're building agents that could plug into
      NovaTech's platform to handle L1 tickets end-to-end.
      Worth a 15-min chat next week?"

  [Word Count] 47/50
```

---

## 🚀 How to Run

### Prerequisites
- Python 3.10+
- A free [OpenRouter](https://openrouter.ai/keys) API key

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/gtm-cold-email-personalizer.git
cd gtm-cold-email-personalizer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
# Create a .env file with:
OPENROUTER_API_KEY=your_api_key_here

# 4a. Run the Web UI
python app.py
# Then open http://localhost:5000

# 4b. Or run the CLI version
python email_generator.py
```

### Output
- **Web UI**: Beautiful dark-mode interface at `http://localhost:5000`
- **Terminal**: Color-coded results in the console
- **File**: `generated_outreach.txt` with all generated emails

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Python 3.10+** | Core language |
| **Flask** | Web server for the UI |
| **OpenRouter API** | Gateway for Gemini LLM generation |
| **Few-Shot Prompting** | Prompt engineering technique |
| **colorama** | Terminal color formatting |
| **python-dotenv** | Secure API key management |
| **JSON** | Structured data I/O |

---

## 📁 Project Structure

```
├── app.py                    # Flask web server (Web UI mode)
├── email_generator.py        # Core logic + CLI mode
├── templates/
│   └── index.html            # Web UI page
├── static/
│   ├── style.css             # Premium dark-mode styles
│   └── script.js             # Frontend logic
├── prospects.json            # Mock LinkedIn profile data (input)
├── generated_outreach.txt    # Generated emails (output, gitignored)
├── requirements.txt          # Python dependencies
├── .env                      # API key (gitignored)
├── .gitignore                # Ignore secrets & generated files
└── README.md                 # This file
```

---

## 📜 License

MIT License — feel free to use, modify, and distribute.