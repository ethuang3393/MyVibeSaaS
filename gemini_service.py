import os
import json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- Helper for Tasks ---
def generate_subtasks(todo_title):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = (f"Break down '{todo_title}' into exactly 5 actionable sub-tasks. "
                  "Return ONLY a raw JSON array of strings. Example: [\"Step 1\", \"Step 2\"]")
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)[:5]
    except Exception as e:
        print(f"Gemini Error: {e}")
        return ["Plan details", "Gather resources", "Execute step 1", "Execute step 2", "Review"]

# --- Helpers for Stash ---
def fetch_url_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]): script.extract()
        return soup.get_text()[:10000]
    except: return None

def summarize_content(url):
    content = fetch_url_content(url)
    if not content: return {'summary': "Could not access URL.", 'tags': "error"}
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = (f"Text: {content}\n\nTasks: 1. Summary (max 2 sentences). 2. 5 tags.\n"
                  "Return JSON keys: 'summary', 'tags' (comma-separated string).")
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {'summary': "AI Error", 'tags': "error"}