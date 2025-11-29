# Find-Dee Backend

This directory contains the backend logic for the Find-Dee LINE Bot, including the intelligent search and tagging system powered by Google Gemini.

## Features

### Intelligent Tagging & Summarization
- **Multimodal Analysis**: Uses **Gemini 2.5 Flash** to analyze uploaded images and PDFs directly.
- **Auto-Tagging**: Generates relevant tags for every uploaded file.
- **Summarization**: Creates a concise title and summary for the content.

### Dynamic Search
- **Natural Language Search**: Users can search using natural language (e.g., `/หาดี lecture notes`).
- **Query Understanding**: Extracts key tags from the user's query to match against stored documents.
- **Contextual Filtering**:
    - **Group Filter**: Automatically filters results to the current LINE group.
    - **Owner Filter**: Filters results to the user's own files in private chats.
- **Dynamic Tag Pool**:
    - Maintains a global pool of tags that grows as files are uploaded.
    - **Semantic Deduplication**: Automatically merges similar tags (e.g., "Math" and "Mathematics") to keep the pool clean and consistent.

## Architecture

### `bot.py`
The main entry point for the LINE Bot.
- Handles LINE events (Text, Image, File).
- Manages user state (e.g., waiting for file upload).
- Integrates with the `search` module to process files and handle search queries.
- Updates the global `tag_pool` dynamically upon every file upload.

### `search/` Module
- **`tagger.py`**: Handles interaction with Gemini to generate metadata (tags, title, summary) from files.
- **`deduplicator.py`**: Uses Gemini to semantically deduplicate lists of tags.
- **`search.py`**: 
    - Extracts search intent/tags from user queries.
    - Matches query tags against document tags using Jaccard similarity.
    - Filters documents by `group_id` and `owner_id`.

### FastAPI Service (`search/api.py`)
A standalone API service for tag generation and search logic testing.

**Endpoints:**
- `POST /tags/generate`: Generate tags from text.
- `POST /tags/deduplicate`: Deduplicate a list of tags.
- `POST /search`: Extract tags from a query and calculate match score against a tag pool.

#### Running the API
1. Navigate to `backend/search`:
   ```bash
   cd backend/search
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   python api.py
   ```
   The API will be available at `http://localhost:8000`.
   Interactive docs: `http://localhost:8000/docs`.

### Main Backend API (`main.py`)
The core API for the LINE Mini App and Bot.

**File Management:**
- `GET /api/files/{user_id}`: Get files for a user (personal + group files).
- `POST /api/upload`: Upload a file (multipart/form-data). **Now includes AI-powered auto-tagging, summarization, and smart renaming.**
- `PUT /api/files/{file_id}`: Update file metadata.
- `DELETE /api/files/{file_id}`: Delete a file.

**Search:**
- `POST /api/search`: Semantic search for files with filtering by `user_id` and `group_id`.

**Planner/Dates:**
- `POST /api/dates`: Create a new date/task.
- `GET /api/dates/{user_id}`: Get all dates for a user.
- `PUT /api/dates/{date_id}`: Update a date.
- `DELETE /api/dates/{date_id}`: Delete a date.

**LINE Webhook:**
- `POST /callback`: Handles incoming LINE events.

#### Running the Main Backend
```bash
cd backend
uvicorn main:app --reload --port 8001
```
Interactive docs: `http://localhost:8001/docs`.

## Configuration
- **Model**: `gemini-2.0-flash`
- **Thinking Tokens**: Disabled (`include_thoughts: False`) for lower latency.

## Usage
1.  **Upload**: Send an image or PDF to the bot. It will reply with generated tags.
2.  **Search**: Type `/หาดี [query]` to find related documents.

## API Usage Examples

### Search API (Port 8000)

**Search for tags in a query:**
```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
           "query": "exam schedule for math",
           "tag_pool": ["Exam", "Schedule", "Math", "Science"]
         }'
```

**Generate Tags from Text:**
```bash
curl -X POST "http://localhost:8000/tags/generate" \
     -H "Content-Type: application/json" \
     -d '{
           "text": "This document contains the syllabus for the Calculus I course, including limits, derivatives, and integrals."
         }'
```

**Deduplicate Tags:**
```bash
curl -X POST "http://localhost:8000/tags/deduplicate" \
     -H "Content-Type: application/json" \
     -d '{
           "tags": ["Math", "Mathematics", "Calc", "Calculus"]
         }'
```

### Main Backend API (Port 8001)

**Get User Files:**
```bash
curl -X GET "http://localhost:8001/api/files/USER_ID_123"
```

**Upload a File:**
```bash
curl -X POST "http://localhost:8001/api/upload" \
     -F "file=@/path/to/your/file.pdf" \
     -F "user_id=USER_ID_123" \
     -F "tags=Homework,Math"
```

**Semantic Search:**
```bash
curl -X POST "http://localhost:8001/api/search" \
     -H "Content-Type: application/json" \
     -d '{
           "query": "lecture notes for biology",
           "user_id": "USER_ID_123"
         }'
```

**Update File Metadata:**
```bash
curl -X PUT "http://localhost:8001/api/files/FILE_ID_123" \
     -H "Content-Type: application/json" \
     -d '{
           "filename": "Calculus_Syllabus_Final.pdf",
           "tags": ["Syllabus", "Math", "Important"]
         }'
```

**Delete a File:**
```bash
curl -X DELETE "http://localhost:8001/api/files/FILE_ID_123"
```

**Create a Date/Task:**
```bash
curl -X POST "http://localhost:8001/api/dates" \
     -H "Content-Type: application/json" \
     -d '{
           "title": "Math Homework Due",
           "date": "2023-12-31",
           "owner_id": "USER_ID_123",
           "tags": ["Homework", "Math"],
           "color": "danger"
         }'
```

**Get User Dates:**
```bash
curl -X GET "http://localhost:8001/api/dates/USER_ID_123"
```

**Update a Date:**
```bash
curl -X PUT "http://localhost:8001/api/dates/DATE_ID_123" \
     -H "Content-Type: application/json" \
     -d '{
           "is_complete": true
         }'
```

**Delete a Date:**
```bash
curl -X DELETE "http://localhost:8001/api/dates/DATE_ID_123"
```

## System Diagram
![System Diagram](image.png)
