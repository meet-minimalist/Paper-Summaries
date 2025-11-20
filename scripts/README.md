# ArXiv Paper Summarizer - Automation Setup

This directory contains the automation scripts for processing arXiv papers from Telegram and generating summaries.

## How It Works

1. **Telegram Bot** receives arXiv URLs from you
2. **GitHub Actions** runs every hour (or manually triggered)
3. **Python Script** checks for new papers, generates summaries with Gemini
4. **Auto-commits** summaries to the repository

## Setup Instructions

### 1. Add GitHub Secrets

Go to your repository settings → Secrets and variables → Actions → New repository secret

Add these secrets:

- **TELEGRAM_BOT_TOKEN**: `8276931827:AAFJlRyezJIev3MSozaF-pE60T3DNWiInEE`
- **TELEGRAM_CHAT_ID**: `1377999503`
- **GEMINI_API_KEY**: Your Gemini API key (get from https://aistudio.google.com/apikey)

### 2. Get Gemini API Key

1. Visit https://aistudio.google.com/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it as `GEMINI_API_KEY` secret in GitHub

### 3. Enable GitHub Actions

1. Go to repository → Actions tab
2. Enable workflows if prompted
3. The workflow will run automatically every hour

### 4. Manual Trigger (Optional)

You can manually trigger the workflow:
1. Go to Actions tab
2. Select "ArXiv Paper Summarizer" workflow
3. Click "Run workflow"

## Usage

Simply send arXiv URLs to your Telegram bot:
- `https://arxiv.org/abs/2301.08727`
- `https://arxiv.org/pdf/2301.08727.pdf`
- Or just: `2301.08727`

The bot will:
1. Send "Processing..." message
2. Fetch paper from arXiv
3. Generate comprehensive summary with Gemini
4. Create `{paper_id}/{paper_id}.md` in the repo
5. Send success message with GitHub link

## Files

- **`.github/workflows/arxiv-summarizer.yml`**: GitHub Actions workflow
- **`scripts/process_arxiv.py`**: Main processing script
- **`scripts/.processed_papers.json`**: Tracks processed papers to avoid duplicates

## Troubleshooting

**Workflow not running?**
- Check if GitHub Actions is enabled
- Verify all secrets are added correctly
- Check Actions tab for error logs

**Papers not being processed?**
- Ensure you're sending messages to the correct bot
- Check if paper ID is already in `.processed_papers.json`
- Verify Gemini API key is valid

**Want to reprocess a paper?**
- Remove the paper ID from `scripts/.processed_papers.json`
- Wait for next hourly run or trigger manually
