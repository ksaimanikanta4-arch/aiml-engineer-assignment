# Task Explanation

## What We Need to Build

### 🎯 Main Goal
Build a **question-answering system** that can answer natural-language questions about member data from a public API.

### 📊 Data Source
- **API Endpoint**: `GET /messages` from `https://november7-730026606190.europe-west1.run.app/messages`
- **Data Format**: Returns paginated messages with:
  - `id`: Message ID
  - `user_id`: User identifier
  - `user_name`: User's name (e.g., "Layla", "Vikram Desai", "Amira")
  - `timestamp`: When the message was sent
  - `message`: The actual message content

### ❓ Example Questions to Answer
1. "When is Layla planning her trip to London?"
2. "How many cars does Vikram Desai have?"
3. "What are Amira's favorite restaurants?"

### 🔧 Requirements

#### 1. API Endpoint
- Create an `/ask` endpoint
- Accept a question (via GET or POST)
- Return answer in format: `{ "answer": "..." }`

#### 2. Functionality
- Fetch messages from the external API
- Process the messages to understand member data
- Answer questions based on the message content
- Handle natural language questions

#### 3. Deployment
- Service must be deployed and publicly accessible
- Can use any deployment platform (Railway, Render, Heroku, Fly.io, etc.)

### 🎁 Bonus Requirements

#### Bonus 1: Design Notes
- Document alternative approaches considered
- Explain why the chosen approach was selected
- Include in README.md

#### Bonus 2: Data Insights
- Analyze the dataset for anomalies
- Identify inconsistencies in member data
- Summarize findings in README.md

### 🏗️ Implementation Approach

#### Step 1: Fetch Data
- Call the external API to get all messages
- Handle pagination (100 messages per page)
- Store/process the messages

#### Step 2: Process Questions
- Accept natural language questions
- Extract relevant information from messages
- Use LLM (OpenAI) or semantic search to find answers

#### Step 3: Return Answers
- Format the answer as JSON: `{ "answer": "..." }`
- Handle cases where information is not found

#### Step 4: Deploy
- Create Dockerfile for containerization
- Set up deployment configuration
- Deploy to a cloud platform

### 📁 Project Structure

```
Assessment Project/
├── main.py                 # FastAPI application with /ask endpoint
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── README.md              # Documentation with design notes
├── analysis.py            # Data analysis script
├── test_api.py            # Test script
├── .env.example           # Environment variables template
└── .gitignore             # Git ignore file
```

### 🚀 How It Works

1. **User asks a question**: `GET /ask?question=When is Layla planning her trip to London?`

2. **System fetches messages**: 
   - Calls external API
   - Retrieves all messages (handles pagination)
   - Processes the data

3. **System finds answer**:
   - Uses OpenAI GPT-3.5 to understand the question
   - Searches through messages for relevant information
   - Generates an answer based on the context

4. **System returns answer**:
   - Returns JSON: `{ "answer": "Based on the messages, Layla mentioned planning a trip to London in March 2024." }`

### 🔍 Key Technologies

- **FastAPI**: Modern Python web framework for building APIs
- **OpenAI GPT-3.5**: Large language model for understanding and answering questions
- **httpx**: Async HTTP client for fetching messages from external API
- **Docker**: Containerization for deployment

### 📝 Next Steps

1. ✅ Set up project structure
2. ✅ Create API service with /ask endpoint
3. ✅ Implement question-answering logic
4. ✅ Add data analysis
5. ✅ Create documentation
6. ✅ Deploy the service

### 🎯 Success Criteria

- ✅ Service responds to questions about member data
- ✅ Answers are accurate and based on the message content
- ✅ Service is deployed and publicly accessible
- ✅ README includes design notes and data insights
- ✅ Code is clean, well-documented, and follows best practices

