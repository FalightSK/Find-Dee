from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    ImageMessage, FileMessage, FlexSendMessage, PostbackEvent
)
import os
import logging
import re
import json
import requests
from firebase_config import (
    save_file_metadata, save_user, upload_file_to_storage, 
    get_tag_pool, save_tag_pool, check_filename_exists,
    get_candidate_files, update_file_metadata
)
from search.tagger import TagGenerator
from search.deduplicator import TagDeduplicator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Services
try:
    tagger = TagGenerator()
    deduplicator = TagDeduplicator()
except Exception as e:
    logger.error(f"Warning: Could not initialize search services: {e}")
    tagger = None
    deduplicator = None

# In-memory state management
# Structure: { user_id: { "state": "STATE_NAME", "data": { ... } } }
user_states = {}

# States
STATE_WAITING_FOR_FILE = "WAITING_FOR_FILE"
STATE_CONFIRMING_UPLOAD = "CONFIRMING_UPLOAD"

def sanitize_filename(name):
    """Sanitizes a string to be safe for filenames."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.replace(' ', '_')
    return name

def handle_line_event(event, line_bot_api):
    user_id = event.source.user_id
    
    # --- Handle Postback Events (Button Clicks) ---
    if isinstance(event, PostbackEvent):
        data = event.postback.data
        params = {}
        try:
            # Parse query string style data (e.g., "action=confirm&file_id=123")
            for part in data.split('&'):
                key, value = part.split('=')
                params[key] = value
        except:
            pass
            
        action = params.get('action')
        
        if action == 'send_file':
            user_states[user_id] = {"state": STATE_WAITING_FOR_FILE, "data": {}}
            reply_text = "กรุณาส่งไฟล์รูปภาพ 🖼️ หรือ PDF 📄 ที่ต้องการฝากมาได้เลยครับ"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            
        elif action == 'search_file':
            # Link to Mini App
            liff_id = os.getenv("LIFF_ID", "YOUR_LIFF_ID")
            mini_app_url = f"https://liff.line.me/{liff_id}"
            reply_text = f"ค้นหาไฟล์ได้ที่นี่เลยครับ 👇\n{mini_app_url}"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            
        elif action == 'settings':
            reply_text = "ฟีเจอร์ตั้งค่ากำลังมาเร็วๆ นี้ครับ ⚙️"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            
        elif action == 'confirm_upload':
            # Process the uploaded file
            state = user_states.get(user_id)
            if state and state.get('state') == STATE_CONFIRMING_UPLOAD:
                # Show Loading Animation
                try:
                    url = "https://api.line.me/v2/bot/chat/loading/start"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {os.getenv('LINE_CHANNEL_ACCESS_TOKEN')}"
                    }
                    payload = {
                        "chatId": user_id,
                        "loadingSeconds": 20 # Max 60, 20 should be enough for AI
                    }
                    requests.post(url, headers=headers, json=payload)
                except Exception as e:
                    logger.error(f"Failed to send loading animation: {e}")
                
                # Process (using original reply_token)
                process_upload(event, line_bot_api, user_id, state['data'])
                user_states.pop(user_id, None)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="หมดเวลาการยืนยันครับ กรุณาเริ่มใหม่"))
                
        elif action == 'cancel_upload':
            user_states.pop(user_id, None)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ยกเลิกการส่งไฟล์เรียบร้อยครับ ❌"))

    # --- Handle Text Messages ---
    elif isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
        text = event.message.text.strip()
        
        if text == "ฟายดี":
            # Send Main Menu Flex Message
            send_main_menu(event, line_bot_api)
        else:
            # Check if waiting for file but user sent text
            state = user_states.get(user_id)
            if state and state.get('state') == STATE_WAITING_FOR_FILE:
                if text == "ยกเลิก":
                    user_states.pop(user_id, None)
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ยกเลิกเรียบร้อยครับ"))
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ผมกำลังรอไฟล์อยู่นะครับ 😅 (พิมพ์ 'ยกเลิก' เพื่อออก)"))

    # --- Handle File/Image Messages ---
    elif isinstance(event, MessageEvent) and isinstance(event.message, (ImageMessage, FileMessage)):
        state = user_states.get(user_id)
        if state and state.get('state') == STATE_WAITING_FOR_FILE:
            handle_file_upload_request(event, line_bot_api, user_id)
        else:
            # Ignore or hint
            pass

def send_main_menu(event, line_bot_api):
    flex_message = FlexSendMessage(
        alt_text="เมนูหลัก ฟายดี",
        contents={
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "จะทำอะไรเลือกเลย 😎",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#FFFFFF",
                        "align": "center"
                    }
                ],
                "backgroundColor": "#06C755",
                "paddingAll": "lg"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "postback",
                            "label": "ส่งไฟล์ 📤",
                            "data": "action=send_file",
                            "displayText": "ส่งไฟล์"
                        },
                        "color": "#06C755"
                    },
                    {
                        "type": "button",
                        "style": "secondary",
                        "action": {
                            "type": "postback",
                            "label": "ค้นหาไฟล์ 🔍",
                            "data": "action=search_file",
                            "displayText": "ค้นหาไฟล์"
                        }
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "action": {
                            "type": "postback",
                            "label": "ตั้งค่า ⚙️",
                            "data": "action=settings",
                            "displayText": "ตั้งค่า"
                        }
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def handle_file_upload_request(event, line_bot_api, user_id):
    # 1. Save file temporarily
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    
    file_type = "image" if isinstance(event.message, ImageMessage) else "file"
    extension = "jpg"
    original_filename = "unknown"
    
    if file_type == "file":
        original_filename = event.message.file_name
        if not original_filename.lower().endswith(".pdf"):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ขออภัยครับ รองรับเฉพาะ PDF และรูปภาพครับ"))
            return
        extension = "pdf"
    
    temp_path = f"/tmp/{message_id}.{extension}"
    with open(temp_path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)
            
    # 2. Prepare Data for Confirmation (Skip AI Tagging here)
    mock_name = f"File-{message_id}"
    if file_type == "file":
        mock_name = os.path.splitext(original_filename)[0]
        
    # Store in state
    user_states[user_id] = {
        "state": STATE_CONFIRMING_UPLOAD,
        "data": {
            "temp_path": temp_path,
            "extension": extension,
            "original_filename": original_filename,
            "mock_name": mock_name,
            "file_type": file_type
        }
    }
    
    # 3. Send Confirmation Flex
    flex_message = FlexSendMessage(
        alt_text="ยืนยันการส่งไฟล์",
        contents={
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "ยืนยันข้อมูลไฟล์ 📄", "weight": "bold", "size": "lg", "color": "#FFFFFF"}
                ],
                "backgroundColor": "#06C755"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "ชื่อไฟล์:", "size": "sm", "color": "#888888"},
                    {"type": "text", "text": f"{mock_name}.{extension}", "size": "md", "weight": "bold", "wrap": True},
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "ระบบจะทำการวิเคราะห์และติด Tag ให้หลังจากยืนยันครับ 🤖", "size": "xs", "color": "#aaaaaa", "wrap": True, "margin": "md"}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "secondary",
                        "action": {
                            "type": "postback",
                            "label": "ยกเลิก",
                            "data": "action=cancel_upload"
                        }
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "color": "#06C755",
                        "action": {
                            "type": "postback",
                            "label": "ยืนยัน",
                            "data": "action=confirm_upload"
                        }
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)

def process_upload(event, line_bot_api, user_id, data):
    temp_path = data['temp_path']
    extension = data['extension']
    mock_name = data['mock_name']
    
    # 1. Analyze (Tagging) - Now done here to save tokens
    generated_metadata = {"tags": [], "title": mock_name, "summary": ""}
    
    if tagger:
        mime_type = "image/jpeg" if extension in ["jpg", "jpeg", "png"] else "application/pdf"
        try:
            # Notify user that processing is starting (optional, but good UX)
            # line_bot_api.push_message(user_id, TextSendMessage(text="กำลังวิเคราะห์ไฟล์... ⏳")) 
            # Note: push_message might cost, but here we are replying to postback. 
            # We can't easily send an intermediate message and then another reply token message without push.
            # Let's just do it and hope it's fast enough.
            
            generated_metadata = tagger.generate_metadata(temp_path, mime_type)
        except Exception as e:
            logger.error(f"Tagging failed: {e}")

    # 2. Deduplicate Tags
    tags = generated_metadata.get("tags", [])
    if deduplicator:
        try:
            # Get current pool
            tag_pool = get_tag_pool() or []
            
            # Combine new tags with existing pool for holistic deduplication
            all_tags_to_process = list(set(tags + tag_pool))
            
            # Run Deduplication
            tag_mapping = deduplicator.deduplicate_and_map(all_tags_to_process)
            
            # Update Tag Pool
            new_pool = sorted(list(set(tag_mapping.values())))
            save_tag_pool(new_pool)
            
            # Update tags for the CURRENT file
            final_current_tags = []
            for t in tags:
                final_current_tags.append(tag_mapping.get(t, t))
            tags = sorted(list(set(final_current_tags)))
            
            # Update tags for ALL EXISTING files
            # This ensures consistency across the entire database
            all_files = get_candidate_files()
            for f in all_files:
                f_id = f.get('id')
                f_tags = f.get('tags', [])
                if not f_tags:
                    continue
                    
                new_f_tags = []
                changed = False
                for t in f_tags:
                    new_t = tag_mapping.get(t, t)
                    new_f_tags.append(new_t)
                    if new_t != t:
                        changed = True
                
                if changed:
                    new_f_tags = sorted(list(set(new_f_tags)))
                    update_file_metadata(f_id, {'tags': new_f_tags})
                    logger.info(f"Updated tags for file {f_id} during upload cleanup.")
                    
        except Exception as e:
            logger.error(f"Error during tag deduplication/remapping: {e}")
            # Fallback: just use generated tags
            pass
        
    if not tags:
        tags = ["Uncategorized"]
        
    # 3. Determine Final Filename
    # Use AI title if available and different from generic
    ai_title = generated_metadata.get("title")
    suggested_filename = generated_metadata.get("suggested_filename")
    
    base_name = sanitize_filename(mock_name)
    if suggested_filename:
        base_name = suggested_filename
    elif ai_title and ai_title != "Untitled":
         base_name = sanitize_filename(ai_title)
         
    count = 0
    while True:
        candidate = f"{base_name}.{extension}" if count == 0 else f"{base_name}_{count}.{extension}"
        if not check_filename_exists(candidate):
            final_filename = candidate
            break
        count += 1
        
    # 4. Upload to Storage
    blob_name = f"uploads/{user_id}/{final_filename}"
    public_url = upload_file_to_storage(temp_path, blob_name)
    
    # 5. Save Metadata
    # Get User Info
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
    except:
        display_name = "Unknown User"
        
    # Get Group Info
    group_id = None
    group_name = None
    if event.source.type == 'group':
        group_id = event.source.group_id
        try:
            summary = line_bot_api.get_group_summary(group_id)
            group_name = summary.group_name
        except:
            group_name = "Unknown Group"
            
    save_user(user_id, display_name, group_id, group_name)
    
    file_data = {
        "filename": final_filename,
        "file_type": extension,
        "storage_path": blob_name,
        "url": public_url,
        "owner_id": user_id,
        "group_id": group_id,
        "tags": tags,
        "version": "v1",
        "detail_summary": generated_metadata.get("summary", ""),
        "due_date_id": None
    }
    
    save_file_metadata(file_data)
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    # 6. Send Success Message
    liff_id = os.getenv("LIFF_ID", "YOUR_LIFF_ID")
    mini_app_url = f"https://liff.line.me/{liff_id}"
    
    # Create Tag Bubbles
    tag_contents = []
    for tag in tags:
        tag_contents.append({
            "type": "text",
            "text": f"#{tag}",
            "color": "#06C755",
            "size": "sm",
            "flex": 0,
            "margin": "xs"
        })

    flex_message = FlexSendMessage(
        alt_text="บันทึกไฟล์สำเร็จ ✅",
        contents={
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "บันทึกไฟล์สำเร็จ! ✅", "weight": "bold", "size": "lg", "color": "#FFFFFF"}
                ],
                "backgroundColor": "#06C755"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": final_filename, "weight": "bold", "size": "md", "wrap": True},
                    {"type": "text", "text": "ถูกจัดเก็บเรียบร้อยแล้ว", "size": "sm", "color": "#666666", "margin": "sm"},
                    {"type": "separator", "margin": "md"},
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": tag_contents,
                        "wrap": True,
                        "margin": "md"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "color": "#06C755",
                        "action": {
                            "type": "uri",
                            "label": "ดูไฟล์ใน Mini App",
                            "uri": mini_app_url
                        }
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)
