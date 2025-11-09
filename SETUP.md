# Setup Guide

## Environment Variables

Create a `.env` file in the project root with the following:

```bash
# Claude API Key (preferred)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OR OpenAI API Key (fallback)
# OPENAI_API_KEY=your_openai_api_key_here
```

### Getting API Keys

**Claude API Key:**
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

**OpenAI API Key (if using OpenAI instead):**
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new API key
4. Copy the key and add it to your `.env` file

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your API key:
```bash
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

3. Run the service:
```bash
python main.py
```

4. Test the API:
```bash
curl "http://localhost:8000/ask?question=When is Layla planning her trip to London?"
```

## Verification

Check that the API is configured correctly:
```bash
curl http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "llm_provider": "claude",
  "claude_configured": true,
  "openai_configured": false
}
```

