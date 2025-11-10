"""
Question-Answering API Service
Answers natural-language questions about member data from external API
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import httpx
import os
import asyncio
from dotenv import load_dotenv
from groq import Groq
from anthropic import Anthropic
import openai

load_dotenv()

app = FastAPI(
    title="Member Data QA Service",
    description="Answer questions about member data from messages",
    version="1.0.0",
)

# External API configuration
EXTERNAL_API_BASE_URL = "https://november7-730026606190.europe-west1.run.app"

# LLM Configuration - Groq is preferred (free), then Claude, then OpenAI
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize LLM clients (prefer Groq > Claude > OpenAI)
groq_client = None
claude_client = None
openai_client = None
llm_provider = None

if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    llm_provider = "groq"
    print("✓ Groq API configured (free tier)")
elif ANTHROPIC_API_KEY:
    claude_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    llm_provider = "claude"
    print("✓ Claude API configured")
elif OPENAI_API_KEY:
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    llm_provider = "openai"
    print("✓ OpenAI API configured")
else:
    print(
        "Warning: No LLM API key found (GROQ_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY). Using simple keyword search."
    )


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str


class Message(BaseModel):
    id: str
    user_id: str
    user_name: str
    timestamp: str
    message: str


class MessagesResponse(BaseModel):
    total: int
    items: list[Message]


async def fetch_all_messages() -> list[Message]:
    """
    Fetch all messages from the external API by paginating through results
    Implements retry logic for resilience against API errors
    """
    all_messages = []
    skip = 0
    limit = 100
    max_retries = 3
    consecutive_failures = 0
    max_consecutive_failures = 5

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http_client:
        while True:
            retry_count = 0
            success = False

            while retry_count < max_retries and not success:
                try:
                    response = await http_client.get(
                        f"{EXTERNAL_API_BASE_URL}/messages/", params={"skip": skip, "limit": limit}
                    )
                    response.raise_for_status()
                    data = response.json()

                    messages = [Message(**item) for item in data.get("items", [])]
                    if not messages:
                        # No more messages, we're done
                        return all_messages

                    all_messages.extend(messages)
                    consecutive_failures = 0  # Reset on success
                    success = True

                    # Check if we've fetched all messages
                    if len(all_messages) >= data.get("total", 0):
                        return all_messages

                    skip += limit

                except httpx.HTTPError as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(
                            f"Retrying... Error at skip={skip} (attempt {retry_count}/{max_retries}): {e}"
                        )
                        await asyncio.sleep(0.5 * retry_count)  # Exponential backoff
                    else:
                        print(f"Skipping batch at skip={skip} after {max_retries} attempts: {e}")
                        consecutive_failures += 1

                except Exception as e:
                    print(f"Unexpected error at skip={skip}: {e}")
                    retry_count = max_retries  # Don't retry on unexpected errors
                    consecutive_failures += 1

            if not success:
                # Skip this batch and try the next one
                skip += limit

                # If too many consecutive failures, stop
                if consecutive_failures >= max_consecutive_failures:
                    print(
                        f"Stopping pagination after {max_consecutive_failures} consecutive failures. Fetched {len(all_messages)} messages."
                    )
                    break

    return all_messages


def format_messages_for_context(messages: list[Message], max_chars: int = 8000) -> str:
    """
    Format messages into a context string for the LLM
    """
    context_parts = []
    char_count = 0

    for msg in messages:
        # Format: "User: [name] (user_id: [id], timestamp: [time]): [message]"
        formatted = (
            f"User: {msg.user_name} (ID: {msg.user_id}, Time: {msg.timestamp}): {msg.message}\n"
        )

        if char_count + len(formatted) > max_chars:
            break

        context_parts.append(formatted)
        char_count += len(formatted)

    return "".join(context_parts)


async def answer_question_with_llm(question: str, messages: list[Message]) -> str:
    """
    Use Groq, Claude, or OpenAI API to answer questions based on the messages
    Priority: Groq (free) > Claude > OpenAI
    """
    # Use Groq if available (FREE!)
    if groq_client:
        try:
            # Groq has a 12k token limit, so use smaller context (20k chars ≈ 5k tokens)
            context = format_messages_for_context(messages, max_chars=20000)

            if not context:
                return "I couldn't find any messages to analyze. The data source may be empty."

            system_prompt = "You are a helpful assistant that answers questions accurately based on the provided context. Be specific and cite user names when relevant."

            user_prompt = f"""Here are the messages from members:

{context}

Based on the above messages, please answer the following question. If the information is not available in the messages, say so. Be specific and cite user names when relevant.

Question: {question}

Answer:"""

            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Fast and good quality
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e:
            print(f"Groq error: {e}, falling back to Claude/OpenAI if available")
            # Continue to fallback options

    # Format messages as context (larger for Claude/OpenAI)
    context = format_messages_for_context(messages, max_chars=100000)

    if not context:
        return "I couldn't find any messages to analyze. The data source may be empty."

    # Create a prompt for the LLM
    system_prompt = "You are a helpful assistant that answers questions accurately based on the provided context. Be specific and cite user names when relevant."

    user_prompt = f"""Here are the messages from members:

{context}

Based on the above messages, please answer the following question. If the information is not available in the messages, say so. Be specific and cite user names when relevant.

Question: {question}

Answer:"""

    # Use Claude if available (fallback from Groq)
    if claude_client:
        try:
            # Try multiple model names - use the latest available
            # Order: try newer models first, fallback to older ones
            model_names = [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-sonnet-20240620",
                "claude-3-5-sonnet",
                "claude-3-opus-20240229",  # Fallback that typically works
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ]
            message = None
            last_error = None

            for model_name in model_names:
                try:
                    message = claude_client.messages.create(
                        model=model_name,
                        max_tokens=2048,
                        temperature=0.7,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}],
                    )
                    break  # Success, exit loop
                except Exception as e:
                    last_error = e
                    # Continue to try next model
                    continue

            if message is None:
                raise (
                    last_error if last_error else Exception("Failed to find a working Claude model")
                )

            answer = message.content[0].text.strip()
            return answer
        except Exception as e:
            return f"Error generating answer with Claude: {str(e)}"

    # Fallback to OpenAI if Claude is not available
    elif openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e:
            return f"Error generating answer with OpenAI: {str(e)}"

    else:
        return "Error: No LLM API key configured. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable."


def answer_question_simple(question: str, messages: list[Message]) -> str:
    """
    Simple rule-based fallback when LLM is not available
    This is a basic implementation that does keyword matching
    """
    question_lower = question.lower()
    answers = []

    # Extract user name from question if mentioned
    mentioned_users = []
    for msg in messages:
        if msg.user_name.lower() in question_lower:
            mentioned_users.append(msg.user_name)

    # Filter messages by mentioned users or search all
    relevant_messages = messages
    if mentioned_users:
        relevant_messages = [msg for msg in messages if msg.user_name in mentioned_users]

    # Simple keyword-based search
    keywords = question_lower.split()
    keyword_matches = []

    for msg in relevant_messages[:50]:  # Limit search to recent 50 messages
        msg_lower = msg.message.lower()
        matches = sum(1 for keyword in keywords if keyword in msg_lower and len(keyword) > 3)
        if matches > 0:
            keyword_matches.append((matches, msg))

    # Sort by match count and get top matches
    keyword_matches.sort(reverse=True, key=lambda x: x[0])

    if keyword_matches:
        top_match = keyword_matches[0][1]
        return f"Based on the messages, I found that {top_match.user_name} mentioned: '{top_match.message}' (on {top_match.timestamp})"
    else:
        return "I couldn't find relevant information in the messages to answer this question."


@app.get("/")
async def root():
    return {
        "service": "Member Data QA Service",
        "endpoints": {"ask": "/ask?question=YOUR_QUESTION", "health": "/health", "stats": "/stats"},
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "llm_provider": llm_provider or "none",
        "groq_configured": groq_client is not None,
        "claude_configured": claude_client is not None,
        "openai_configured": openai_client is not None,
    }


@app.get("/stats")
async def stats():
    """Get statistics about the messages"""
    try:
        messages = await fetch_all_messages()
        users = {}
        for msg in messages:
            if msg.user_name not in users:
                users[msg.user_name] = 0
            users[msg.user_name] += 1

        return {"total_messages": len(messages), "unique_users": len(users), "users": users}
    except Exception as e:
        return {"error": str(e)}


@app.get("/ask")
async def ask_question(question: str = Query(..., description="The question to answer")):
    """
    Answer a natural-language question about member data
    """
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Question parameter is required")

    try:
        # Fetch all messages
        messages = await fetch_all_messages()

        if not messages:
            return AnswerResponse(answer="No messages found in the data source.")

        # Use LLM if available, otherwise fall back to simple search
        if groq_client or claude_client or openai_client:
            answer = await answer_question_with_llm(question, messages)
        else:
            answer = answer_question_simple(question, messages)

        return AnswerResponse(answer=answer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.post("/ask")
async def ask_question_post(request: QuestionRequest):
    """
    Answer a natural-language question about member data (POST endpoint)
    """
    return await ask_question(request.question)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
