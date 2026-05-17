"""
GTM Cold Email Personalizer
============================
Generates highly personalized 3-sentence cold email openers using
Google Gemini API with few-shot prompting.

Built to demonstrate the core GTM Agent capability:
"Generate the first 3 sentences of a cold email that reference
specific, verifiable facts about the prospect."

Author: Your Name
Tech: Python, Google Gemini API (google-genai), Few-Shot Prompting
"""

import json
import os
import re
import sys
import time
from datetime import datetime

from openai import OpenAI
from colorama import Fore, Style, init as colorama_init
from dotenv import load_dotenv


# ─── Fix Windows console encoding for Unicode characters ────
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

PROSPECTS_FILE = "prospects.json"
OUTPUT_FILE = "generated_outreach.txt"
OPENROUTER_MODEL = "google/gemini-2.5-flash"
MAX_RETRIES = 3

# Required fields every prospect entry must have
REQUIRED_FIELDS = [
    "name", "role", "company",
    "company_industry", "recent_achievement", "linkedin_headline"
]


# ─────────────────────────────────────────────────────────────
# DATA LOADING & VALIDATION
# ─────────────────────────────────────────────────────────────

def load_prospects(filepath: str) -> list[dict]:
    """
    Load and validate prospect data from a JSON file.

    Args:
        filepath: Path to the prospects JSON file.

    Returns:
        A list of prospect dictionaries, each containing
        name, role, company, company_industry,
        recent_achievement, and linkedin_headline.

    Raises:
        FileNotFoundError: If the JSON file doesn't exist.
        ValueError: If the JSON is malformed or missing required fields.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Prospects file not found: '{filepath}'\n"
            f"Please create it with mock LinkedIn profile data."
        )

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in '{filepath}': {e}")

    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(
            f"'{filepath}' must contain a non-empty JSON array of prospects."
        )

    # Validate each prospect has all required fields
    for i, prospect in enumerate(data):
        missing = [field for field in REQUIRED_FIELDS if field not in prospect]
        if missing:
            raise ValueError(
                f"Prospect #{i+1} is missing required fields: {missing}"
            )

    return data


# ─────────────────────────────────────────────────────────────
# PROMPT ENGINEERING — FEW-SHOT PROMPT CONSTRUCTION
# ─────────────────────────────────────────────────────────────

def build_system_prompt() -> str:
    """
    Build the system-level prompt that defines the LLM's persona
    and output rules.

    This uses PERSONA ENGINEERING to constrain the model's behavior
    to that of an expert B2B sales professional.
    """
    return """You are an elite B2B tech sales closer at a cutting-edge AI company called Synapse AI.
Your job is to write the first 3 sentences of a cold email.

STRICT RULES:
1. The email MUST reference the prospect's recent achievement naturally — not forced or generic.
2. Total word count MUST be under 50 words.
3. Tone: confident, peer-to-peer, conversational. Never salesy, desperate, or sycophantic.
4. NEVER use phrases like:
   - "I hope this finds you well"
   - "I came across your profile"
   - "I'd love to connect"
   - "I noticed that you"
5. The email should create genuine curiosity and end with a soft call-to-action.
6. You MUST return your response as a valid JSON object with exactly these keys:
   - "subject_line": A short, punchy email subject line (under 10 words)
   - "opening_lines": The 3 sentences of the email body

Return ONLY the JSON object. No markdown, no code fences, no extra text."""


def build_few_shot_examples() -> str:
    """
    Build the few-shot examples that teach the LLM the exact
    pattern, tone, and structure we expect.

    TWO examples are provided (2-shot prompting) — enough to
    establish the pattern without over-constraining creativity.
    """
    return """Here are 2 examples of the exact input and output format I expect:

---
EXAMPLE INPUT 1:
Name: Alex Kim | Role: VP of Product | Company: StreamScale (Video Infrastructure)
Recent Achievement: Just launched a real-time video analytics dashboard that processes 2M events/sec
LinkedIn Headline: Product leader obsessed with developer experience

EXAMPLE OUTPUT 1:
{"subject_line": "Your analytics dashboard x our AI agents", "opening_lines": "Congrats on shipping the real-time analytics dashboard, Alex — processing 2M events/sec is no joke. At Synapse AI, we're building autonomous agents that plug directly into platforms like StreamScale to surface customer insights in real time. Would 15 minutes next week make sense to explore a quick pilot?"}

---
EXAMPLE INPUT 2:
Name: Rachel Torres | Role: Head of Ops | Company: LogiFlow (Supply Chain Tech)
Recent Achievement: Reduced fulfillment errors by 28% using a new automated QA pipeline
LinkedIn Headline: Ops leader turning chaos into systems

EXAMPLE OUTPUT 2:
{"subject_line": "28% error reduction - what's next?", "opening_lines": "That 28% drop in fulfillment errors is impressive, Rachel — automation done right. We've been helping ops teams like yours at LogiFlow layer AI agents on top of existing pipelines to push those numbers even further. Curious if that's on your roadmap for Q3?"}
---"""


def build_user_prompt(prospect: dict) -> str:
    """
    Build the dynamic user prompt for a specific prospect.

    This injects the prospect's real data into the prompt template,
    giving the LLM the context it needs to personalize the email.

    Args:
        prospect: Dictionary with prospect data fields.

    Returns:
        Formatted prompt string with the prospect's information.
    """
    return f"""Now generate for this real prospect:

Name: {prospect['name']} | Role: {prospect['role']} | Company: {prospect['company']} ({prospect['company_industry']})
Recent Achievement: {prospect['recent_achievement']}
LinkedIn Headline: {prospect['linkedin_headline']}

Return ONLY the JSON object. No other text."""


# ─────────────────────────────────────────────────────────────
# LLM API INTERACTION
# ─────────────────────────────────────────────────────────────

def configure_api() -> OpenAI:
    """
    Load the API key from .env and configure the OpenRouter client.

    Returns:
        A configured OpenAI client instance ready for generation via OpenRouter.

    Raises:
        EnvironmentError: If the API key is not found.
    """
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY not found in environment.\n"
            "Please create a .env file with: OPENROUTER_API_KEY=your_key_here\n"
            "Get a key at: https://openrouter.ai/keys"
        )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    return client


def parse_llm_response(response_text: str) -> dict:
    """
    Parse the LLM's response text into a structured dictionary.

    Handles edge cases where the LLM wraps JSON in markdown code
    fences or adds extra text around the JSON.

    Args:
        response_text: Raw text response from the LLM.

    Returns:
        Dictionary with 'subject_line' and 'opening_lines' keys.

    Raises:
        ValueError: If the response cannot be parsed as valid JSON.
    """
    text = response_text.strip()

    # Strip markdown code fences if present (```json ... ```)
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from surrounding text
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            raise ValueError(f"Could not parse LLM response as JSON:\n{text}")

    # Validate required keys
    if "subject_line" not in data or "opening_lines" not in data:
        raise ValueError(
            f"LLM response missing required keys. Got: {list(data.keys())}"
        )

    return data


def generate_email(prospect: dict, client: OpenAI) -> dict:
    """
    Generate a personalized cold email for a single prospect.

    Constructs the full few-shot prompt, sends it to OpenRouter,
    and parses the structured JSON response.

    Includes retry logic for robustness.

    Args:
        prospect: Dictionary with prospect data.
        client: Configured OpenAI client (for OpenRouter).

    Returns:
        Dictionary with 'subject_line' and 'opening_lines'.
    """
    system_prompt = build_system_prompt()
    few_shot = build_few_shot_examples()
    user_prompt = build_user_prompt(prospect)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
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
            return result

        except ValueError as e:
            if attempt < MAX_RETRIES:
                print(f"  {Fore.YELLOW}>> Parse error (attempt {attempt}/{MAX_RETRIES}), retrying...{Style.RESET_ALL}")
                time.sleep(1)
            else:
                raise ValueError(
                    f"Failed to get valid response after {MAX_RETRIES} attempts: {e}"
                )

        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"  {Fore.YELLOW}>> API error (attempt {attempt}/{MAX_RETRIES}), retrying...{Style.RESET_ALL}")
                time.sleep(2)
            else:
                raise RuntimeError(
                    f"API call failed after {MAX_RETRIES} attempts: {e}"
                )


# ─────────────────────────────────────────────────────────────
# OUTPUT FORMATTING & DISPLAY
# ─────────────────────────────────────────────────────────────

def count_words(text: str) -> int:
    """Count the number of words in a text string."""
    return len(text.split())


def wrap_text(text: str, width: int = 54, indent: str = "") -> str:
    """Simple word-wrap for terminal display."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            current_line += (" " + word) if current_line else word
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return ("\n" + indent).join(lines)


def display_result(prospect: dict, email_data: dict, index: int, total: int) -> str:
    """
    Format and display a single prospect's generated email
    with rich terminal formatting.

    Args:
        prospect: The prospect's data dictionary.
        email_data: The generated email dictionary from the LLM.
        index: Current prospect number (1-indexed).
        total: Total number of prospects.

    Returns:
        A plain-text formatted string (for file saving).
    """
    word_count = count_words(email_data["opening_lines"])
    word_color = Fore.GREEN if word_count <= 50 else Fore.RED

    # Terminal output (with colors) — using ASCII-safe box characters
    separator = f"  {Fore.CYAN}{'=' * 58}{Style.RESET_ALL}"

    print(separator)
    print(f"  {Fore.WHITE}{Style.BRIGHT}PROSPECT {index}/{total}: {prospect['name']}{Style.RESET_ALL}")
    print(f"  {Fore.BLUE}{prospect['role']} @ {prospect['company']}{Style.RESET_ALL}")
    print(separator)
    print()
    print(f"  {Fore.YELLOW}[Achievement]{Style.RESET_ALL} {prospect['recent_achievement']}")
    print()
    print(f"  {Fore.MAGENTA}[Subject]{Style.RESET_ALL} {email_data['subject_line']}")
    print()
    print(f"  {Fore.GREEN}[Email]{Style.RESET_ALL}")

    # Word-wrap the email for clean display
    email_lines = email_data["opening_lines"]
    wrapped = wrap_text(email_lines, width=54, indent="     ")
    print(f'     {Fore.WHITE}"{wrapped}"{Style.RESET_ALL}')
    print()
    print(f"  {word_color}[Word Count] {word_count}/50{Style.RESET_ALL}")
    print()

    # Plain-text version for file output
    plain = (
        f"{'=' * 60}\n"
        f"PROSPECT {index}/{total}: {prospect['name']}\n"
        f"{prospect['role']} @ {prospect['company']}\n"
        f"{'=' * 60}\n\n"
        f"Achievement: {prospect['recent_achievement']}\n\n"
        f"Subject: {email_data['subject_line']}\n\n"
        f"Email:\n"
        f"\"{email_data['opening_lines']}\"\n\n"
        f"Word Count: {word_count}/50\n\n"
    )

    return plain


def print_header():
    """Print the application header banner."""
    print()
    print(f"  {Fore.CYAN}+{'=' * 58}+{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}|{Style.RESET_ALL}  {Fore.WHITE}{Style.BRIGHT}GTM COLD EMAIL PERSONALIZER{Style.RESET_ALL}                             {Fore.CYAN}|{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}|{Style.RESET_ALL}  {Fore.BLUE}Powered by Few-Shot Prompting + Google Gemini{Style.RESET_ALL}       {Fore.CYAN}|{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}+{'=' * 58}+{Style.RESET_ALL}")
    print()


def print_footer(total: int, output_file: str, elapsed: float):
    """Print the summary footer after all emails are generated."""
    print(f"  {Fore.CYAN}{'=' * 58}{Style.RESET_ALL}")
    print()
    print(f"  {Fore.GREEN}[OK] All {total} emails generated successfully!{Style.RESET_ALL}")
    print(f"  {Fore.BLUE}[FILE] Saved to: {output_file}{Style.RESET_ALL}")
    print(f"  {Fore.BLUE}[TIME] Total time: {elapsed:.1f}s{Style.RESET_ALL}")
    print()


# ─────────────────────────────────────────────────────────────
# FILE OUTPUT
# ─────────────────────────────────────────────────────────────

def save_to_file(all_results: list[str], filepath: str):
    """
    Save all generated email results to a text file.

    Args:
        all_results: List of plain-text formatted result strings.
        filepath: Output file path.
    """
    header = (
        "GTM COLD EMAIL PERSONALIZER — Generated Outreach\n"
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Model: {OPENROUTER_MODEL}\n"
        f"Technique: Few-Shot Prompting (2-shot)\n"
        f"{'=' * 60}\n\n"
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header)
        for result in all_results:
            f.write(result)


# ─────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────

def main():
    """
    Main execution flow:
    1. Initialize terminal colors
    2. Load & validate prospect data
    3. Configure Gemini API
    4. Generate personalized emails for each prospect
    5. Display results beautifully in the terminal
    6. Save results to output file
    """
    # Initialize colorama for Windows terminal color support
    colorama_init(strip=False)

    print_header()

    # -- Step 1: Load prospect data --
    print(f"  {Fore.BLUE}[LOAD] Loading prospects from {PROSPECTS_FILE}...{Style.RESET_ALL}")
    try:
        prospects = load_prospects(PROSPECTS_FILE)
        print(f"  {Fore.GREEN}[OK] Loaded {len(prospects)} prospects{Style.RESET_ALL}")
    except (FileNotFoundError, ValueError) as e:
        print(f"\n  {Fore.RED}[ERROR] {e}{Style.RESET_ALL}")
        sys.exit(1)

    # -- Step 2: Configure API --
    print(f"  {Fore.BLUE}[API] Configuring OpenRouter API...{Style.RESET_ALL}")
    try:
        client = configure_api()
        print(f"  {Fore.GREEN}[OK] API configured (model: {OPENROUTER_MODEL}){Style.RESET_ALL}")
    except EnvironmentError as e:
        print(f"\n  {Fore.RED}[ERROR] {e}{Style.RESET_ALL}")
        sys.exit(1)

    print()
    print(f"  {Fore.WHITE}{Style.BRIGHT}Generating personalized emails...{Style.RESET_ALL}")
    print()

    # -- Step 3: Generate emails for each prospect --
    all_results = []
    start_time = time.time()

    for i, prospect in enumerate(prospects, start=1):
        print(f"  {Fore.YELLOW}[GEN] Generating email for {prospect['name']}...{Style.RESET_ALL}")

        try:
            email_data = generate_email(prospect, client)
            result_text = display_result(prospect, email_data, i, len(prospects))
            all_results.append(result_text)

        except (ValueError, RuntimeError) as e:
            print(f"  {Fore.RED}[FAIL] Failed for {prospect['name']}: {e}{Style.RESET_ALL}")
            all_results.append(
                f"{'=' * 60}\n"
                f"PROSPECT {i}/{len(prospects)}: {prospect['name']}\n"
                f"ERROR: {e}\n\n"
            )

    elapsed = time.time() - start_time

    # -- Step 4: Save to file --
    save_to_file(all_results, OUTPUT_FILE)

    # -- Step 5: Print summary --
    print_footer(len(prospects), OUTPUT_FILE, elapsed)


if __name__ == "__main__":
    main()
