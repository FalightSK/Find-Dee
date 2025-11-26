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
- **`search.py`**: Extracts search intent/tags from user queries.

## Configuration
- **Model**: `gemini-2.5-flash`
- **Thinking Tokens**: Disabled (`include_thoughts: False`) for lower latency.

## Usage
1.  **Upload**: Send an image or PDF to the bot. It will reply with generated tags.
2.  **Search**: Type `/หาดี [query]` to find related documents.

## System Diagram
![System Diagram](image.png)
