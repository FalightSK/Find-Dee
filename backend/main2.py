import os
import uuid
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage, FileMessage
from dotenv import load_dotenv

load_dotenv()

from bot import handle_line_event
from firebase_config import (
    initialize_firebase, 
    save_file_metadata, 
    upload_bytes_to_storage, 
    update_file_metadata, 
    delete_file,
    get_user_profile, 
    get_files_by_group, 
    get_files_by_user,
    save_date,
    get_dates_by_user,
    update_date,
    delete_date
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase
firebase_app = initialize_firebase()

# Initialize Services
from search.tagger import TagGenerator
from search.deduplicator import TagDeduplicator
from search.search import TagSearch
from firebase_config import get_tag_pool, save_tag_pool, check_filename_exists, get_candidate_files

try:
    tagger = TagGenerator()
    deduplicator = TagDeduplicator()
    searcher = TagSearch()
except Exception as e:
    print(f"Warning: Could not initialize search services: {e}")
    tagger = None
    deduplicator = None
    searcher = None

# LINE Bot configuration
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

class FileUpdate(BaseModel):
    filename: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "LINE File Management Bot API is running"}

@app.get("/api/files/{user_id}")
async def get_user_files(user_id: str):
    # 1. Get User Profile to find groups
    user_profile = get_user_profile(user_id)
    if not user_profile:
        return {"files": []}
    
    groups = user_profile.get('groups', {})
    
    # 2. Fetch files for each group
    grouped_files = []
    
    # 2.1 Personal Files (uploaded by user)
    personal_files = get_files_by_user(user_id)
    if personal_files:
        grouped_files.append({
            "group_name": "My Uploads",
            "files": personal_files
        })
        
    # 2.2 Group Files
    for group_id, group_name in groups.items():
        # group_name might be True if legacy, handle that
        if group_name is True: 
            group_name = "Unknown Group"
            
        files = get_files_by_group(group_id)
        if files:
            grouped_files.append({
                "group_name": group_name,
                "files": files
            })
            
    return {"groups": grouped_files}

import re

class SearchRequest(BaseModel):
    query: str
    user_id: str
    group_id: Optional[str] = None

@app.post("/api/search")
async def search_files(request: SearchRequest):
    try:
        if not searcher:
             raise HTTPException(status_code=503, detail="Search service unavailable")
             
        # 1. Fetch Tag Pool
        tag_pool = get_tag_pool() or []
        
        # 2. Extract Tags
        query_tags = searcher.extract_query_tags(request.query, tag_pool)
        
        # 3. Get Candidate Files
        candidate_files = get_candidate_files(group_id=request.group_id, user_id=request.user_id)
        
        # 4. Search & Rank
        found_files = searcher.search_documents(
            request.query, 
            candidate_files, 
            tag_pool, 
            group_id=request.group_id, 
            owner_id=request.user_id
        )
        
        return {
            "query": request.query,
            "extracted_tags": query_tags,
            "results": found_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    group_id: Optional[str] = Form(None),
    tags: Optional[str] = Form(None) # Comma separated, optional manual tags
):
    try:
        # 1. Validate file type
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower().replace('.', '')
        if not ext:
            ext = "jpg" # Default
            
        file_type = 'other'
        mime_type = file.content_type
        
        if ext in ['jpg', 'jpeg', 'png']:
            file_type = 'image'
            if not mime_type: mime_type = "image/jpeg"
        elif ext == 'pdf':
            file_type = 'pdf'
            if not mime_type: mime_type = "application/pdf"
            
        # 2. Save temporarily for AI analysis
        temp_save_path = f"temp_{uuid.uuid4()}.{ext}"
        with open(temp_save_path, "wb") as buffer:
            import shutil
            shutil.copyfileobj(file.file, buffer)
            
        # 3. AI Analysis (Tagging & Summarization)
        generated_metadata = {"tags": [], "title": "Untitled", "summary": ""}
        
        if tagger:
            try:
                generated_metadata = tagger.generate_metadata(temp_save_path, mime_type)
            except Exception as e:
                print(f"Tag generation failed: {e}")
                
        raw_tags = generated_metadata.get("tags", [])
        
        # Merge manual tags if provided
        if tags:
            manual_tags = [t.strip() for t in tags.split(',')]
            raw_tags.extend(manual_tags)
            
        # 4. Deduplication & Tag Pool Update
        final_tags = raw_tags
        if deduplicator and raw_tags:
            final_tags = deduplicator.deduplicate(raw_tags)
            
        # Update Global Tag Pool
        tag_pool = get_tag_pool() or []
        if deduplicator and final_tags:
            combined_pool = list(set(tag_pool + final_tags))
            tag_pool = deduplicator.deduplicate(combined_pool)
            save_tag_pool(tag_pool)
        elif final_tags:
            tag_pool.extend(final_tags)
            tag_pool = list(set(tag_pool))
            save_tag_pool(tag_pool)
            
        if not final_tags:
            final_tags = ["Uncategorized"]
            
        # 5. Smart Renaming
        mock_name = generated_metadata.get("title", filename)
        mock_summary = generated_metadata.get("summary", "No summary available")
        suggested_filename = generated_metadata.get("suggested_filename", "")
        
        base_name = "untitled_file"
        if suggested_filename:
            base_name = suggested_filename
        elif file_type == 'pdf':
             base_name = os.path.splitext(filename)[0]
        else:
             # Sanitize title
             base_name = re.sub(r'[<>:"/\\|?*]', '', mock_name).replace(' ', '_')
             
        # Ensure uniqueness
        count = 0
        while True:
            candidate_name = f"{base_name}.{ext}" if count == 0 else f"{base_name}_{count}.{ext}"
            if not check_filename_exists(candidate_name):
                final_filename = candidate_name
                break
            count += 1
            
        # 6. Upload to Storage
        # Re-open temp file to upload
        with open(temp_save_path, "rb") as f:
            file_bytes = f.read()
            
        storage_path = f"uploads/{user_id}/{final_filename}"
        public_url = upload_bytes_to_storage(file_bytes, storage_path, mime_type)
        
        # 7. Save Metadata
        file_data = {
            'filename': final_filename,
            'file_type': ext,
            'storage_path': storage_path,
            'url': public_url,
            'owner_id': user_id,
            'group_id': group_id,
            'tags': final_tags,
            'version': 'v1',
            'detail_summary': mock_summary,
            'due_date_id': None
        }
        
        file_id = save_file_metadata(file_data)
        
        # Cleanup
        if os.path.exists(temp_save_path):
            os.remove(temp_save_path)
        
        return {
            "file_id": file_id, 
            "url": public_url, 
            "filename": final_filename,
            "tags": final_tags,
            "summary": mock_summary,
            "message": "File uploaded and analyzed successfully"
        }
        
    except Exception as e:
        if 'temp_save_path' in locals() and os.path.exists(temp_save_path):
            os.remove(temp_save_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/files/{file_id}")
async def update_file(file_id: str, updates: FileUpdate):
    try:
        update_dict = updates.dict(exclude_unset=True)
        success = update_file_metadata(file_id, update_dict)
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        return {"message": "File updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/{file_id}")
async def delete_file_endpoint(file_id: str):
    try:
        success = delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DateCreate(BaseModel):
    title: str
    date: str # YYYY-MM-DD
    tags: Optional[List[str]] = []
    owner_id: str
    color: Optional[str] = "primary"

class DateUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    tags: Optional[List[str]] = None
    color: Optional[str] = None
    is_complete: Optional[bool] = None

@app.post("/api/dates")
async def create_date(date: DateCreate):
    try:
        date_data = date.dict()
        date_id = save_date(date_data)
        return {"date_id": date_id, "message": "Date created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dates/{user_id}")
async def get_user_dates(user_id: str):
    try:
        dates = get_dates_by_user(user_id)
        return {"dates": dates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/dates/{date_id}")
async def update_date_endpoint(date_id: str, updates: DateUpdate):
    try:
        update_dict = updates.dict(exclude_unset=True)
        success = update_date(date_id, update_dict)
        if not success:
            raise HTTPException(status_code=404, detail="Date not found")
        return {"message": "Date updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/dates/{date_id}")
async def delete_date_endpoint(date_id: str):
    try:
        success = delete_date(date_id)
        if not success:
            raise HTTPException(status_code=404, detail="Date not found")
        return {"message": "Date deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/callback")
async def callback(request: Request):
    # get X-Line-Signature header value
    signature = request.headers.get("X-Line-Signature")

    # get request body as text
    body = await request.body()
    body_text = body.decode("utf-8")

    # handle webhook body
    try:
        handler.handle(body_text, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"

@handler.add(MessageEvent, message=(TextMessage, ImageMessage, FileMessage))
def handle_message(event):
    handle_line_event(event, line_bot_api)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
