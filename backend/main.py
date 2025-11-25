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

load_dotenv()

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

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    group_id: Optional[str] = Form(None),
    tags: Optional[str] = Form(None) # Comma separated
):
    try:
        # 1. Validate file type
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        file_type = 'other'
        if ext in ['.jpg', '.jpeg', '.png']:
            file_type = 'image'
        elif ext == '.pdf':
            file_type = 'pdf'
            
        # 2. Upload to Storage
        file_bytes = await file.read()
        storage_path = f"uploads/{user_id}/{uuid.uuid4()}{ext}"
        public_url = upload_bytes_to_storage(file_bytes, storage_path, file.content_type)
        
        # 3. Save Metadata
        tag_list = [t.strip() for t in tags.split(',')] if tags else []
        
        file_data = {
            'filename': filename,
            'file_type': file_type,
            'storage_path': storage_path,
            'url': public_url,
            'owner_id': user_id,
            'group_id': group_id,
            'tags': tag_list,
            'version': 'v1'
        }
        
        file_id = save_file_metadata(file_data)
        
        return {"file_id": file_id, "url": public_url, "message": "File uploaded successfully"}
        
    except Exception as e:
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
