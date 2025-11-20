#!/usr/bin/env python3
"""
ArXiv Paper Summarizer - Automated Processing Script
Fetches arXiv URLs from Telegram, generates summaries, and commits to GitHub
"""

import os
import re
import json
import arxiv
import requests
from datetime import datetime
from pathlib import Path
import google.generativeai as genai

# Configuration from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# File to track processed papers
PROCESSED_FILE = 'scripts/.processed_papers.json'

def load_processed_papers():
    """Load list of already processed paper IDs"""
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return json.load(f)
    return []

def save_processed_paper(paper_id):
    """Save processed paper ID to avoid reprocessing"""
    processed = load_processed_papers()
    if paper_id not in processed:
        processed.append(paper_id)
        os.makedirs(os.path.dirname(PROCESSED_FILE), exist_ok=True)
        with open(PROCESSED_FILE, 'w') as f:
            json.dump(processed, f)

def get_telegram_updates():
    """Fetch recent messages from Telegram bot"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('result', [])
    return []

def send_telegram_message(chat_id, message):
    """Send message to Telegram chat"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    requests.post(url, data=data)

def extract_arxiv_id(text):
    """Extract arXiv ID from URL or text"""
    patterns = [
        r'arxiv\.org/abs/(\d+\.\d+)',
        r'arxiv\.org/pdf/(\d+\.\d+)',
        r'(\d{4}\.\d{4,5})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def fetch_arxiv_paper(paper_id):
    """Fetch paper details from arXiv"""
    search = arxiv.Search(id_list=[paper_id])
    paper = next(search.results())
    return paper

def generate_summary(paper):
    """Generate comprehensive summary using Gemini"""
    prompt = f"""Generate a comprehensive academic paper summary with the following structure:

Title: {paper.title}
Authors: {', '.join([author.name for author in paper.authors])}
Published: {paper.published.strftime('%B %d, %Y')}
arXiv ID: {paper.get_short_id()}

Abstract:
{paper.summary}

Create a detailed summary covering:
1. Core Contribution - Main innovation and key ideas
2. Technical Approach - Methodology, architecture, algorithms
3. Key Results & Ablations - Experimental results and ablation studies
4. Important Citations - Related work and key references
5. Conclusion & Impact - Significance and future directions

Make it comprehensive enough that someone doesn't need to read the full paper to understand its main ideas."""

    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content(prompt)
    return response.text

def create_markdown_summary(paper, summary_text):
    """Create formatted markdown file"""
    paper_id = paper.get_short_id()
    authors = ', '.join([author.name for author in paper.authors])
    
    markdown = f"""# {paper.title}

**Authors:** {authors}

**arXiv ID:** {paper_id}

**Published:** {paper.published.strftime('%B %d, %Y')}

**Link:** https://arxiv.org/abs/{paper_id}

---

{summary_text}

---

*Summary generated on: {datetime.now().strftime('%Y-%m-%d')}*
"""
    return markdown

def save_summary_to_file(paper_id, content):
    """Save summary to GitHub repo structure"""
    dir_path = Path(paper_id)
    dir_path.mkdir(exist_ok=True)
    
    file_path = dir_path / f"{paper_id}.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path

def process_new_papers():
    """Main processing function"""
    print("🔍 Checking for new arXiv papers...")
    
    # Get Telegram updates
    updates = get_telegram_updates()
    processed_papers = load_processed_papers()
    
    new_papers_found = False
    
    for update in updates:
        if 'message' not in update:
            continue
            
        message = update['message']
        chat_id = message['chat']['id']
        
        # Only process messages from the configured chat
        if str(chat_id) != TELEGRAM_CHAT_ID:
            continue
        
        text = message.get('text', '')
        paper_id = extract_arxiv_id(text)
        
        if not paper_id:
            continue
        
        # Skip if already processed
        if paper_id in processed_papers:
            print(f"⏭️  Paper {paper_id} already processed, skipping...")
            continue
        
        print(f"📥 Processing new paper: {paper_id}")
        new_papers_found = True
        
        try:
            # Send processing status
            send_telegram_message(
                chat_id,
                f"📥 Processing paper...\narXiv ID: {paper_id}\n\nFetching paper details..."
            )
            
            # Fetch paper
            paper = fetch_arxiv_paper(paper_id)
            print(f"✅ Fetched: {paper.title}")
            
            # Generate summary
            print("🤖 Generating summary with Gemini...")
            summary = generate_summary(paper)
            
            # Create markdown
            markdown_content = create_markdown_summary(paper, summary)
            
            # Save to file
            file_path = save_summary_to_file(paper_id, markdown_content)
            print(f"💾 Saved to: {file_path}")
            
            # Mark as processed
            save_processed_paper(paper_id)
            
            # Send success message
            github_url = f"https://github.com/meet-minimalist/Paper-Summaries/blob/main/{paper_id}/{paper_id}.md"
            send_telegram_message(
                chat_id,
                f"✅ Summary generated successfully!\n\n📄 Paper: {paper.title}\n🔗 Summary saved at: {github_url}"
            )
            
            print(f"✅ Successfully processed {paper_id}")
            
        except Exception as e:
            print(f"❌ Error processing {paper_id}: {str(e)}")
            send_telegram_message(
                chat_id,
                f"❌ Error processing paper {paper_id}\nReason: {str(e)}"
            )
    
    if not new_papers_found:
        print("✨ No new papers to process")
    else:
        print("🎉 Processing complete!")

if __name__ == "__main__":
    process_new_papers()
