from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    ImageMessage, FileMessage, FlexSendMessage
)
import os
import logging
import re
from firebase_config import (
    save_file_metadata, save_user, upload_file_to_storage, 
    search_files_by_tags, get_tag_pool, save_tag_pool, check_filename_exists
)
from search.tagger import TagGenerator
from search.deduplicator import TagDeduplicator
from search.search import TagSearch

# Configure Logging
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
    searcher = TagSearch()
except Exception as e:
    logger.error(f"Warning: Could not initialize search services: {e}")
    tagger = None
    deduplicator = None
    searcher = None

# Simple in-memory state for prototype: {user_id: "mode"}
user_states = {}

def sanitize_filename(name):
    """Sanitizes a string to be safe for filenames."""
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    return name

def handle_line_event(event, line_bot_api):
    user_id = event.source.user_id

    # Fetch Tag Pool from Firebase
    tag_pool = get_tag_pool()
    if not tag_pool:
        tag_pool = ["Lecture", "Homework", "Exam", "Schedule", "Payment"]

    # print(user_states.get(user_id)) # Replaced with debug log if needed, or just remove
    
    if isinstance(event.message, TextMessage):
        text = event.message.text.strip()
        
        if text == r"/ฟายดี":
            # Enter file saving mode
            user_states[user_id] = "waiting_for_file"
            reply_text = "เข้าสู่โหมดรับฝากไฟล์ครับ 📂\nกรุณาส่งรูปภาพ 🖼️ หรือไฟล์ PDF 📄 มาได้เลยครับ"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            
        elif text.startswith(r"/หาดี"):
            # Search command
            query = text.replace(r"/หาดี", "").strip()
            
            if not searcher:
                reply_text = "ระบบค้นหายังไม่พร้อมใช้งานครับ"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            else:
                # 1. Extract Tags from Query
                query_tags = searcher.extract_query_tags(query, tag_pool)
                logger.info(f"Search query: '{query}' -> Tags: {query_tags}")
                
                # 2. Search in Firebase
                found_files = search_files_by_tags(query_tags)
                
                if not found_files:
                    reply_text = f"ไม่พบเอกสารที่เกี่ยวกับ: {', '.join(query_tags)} ครับ 😅"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
                else:
                    # 3. Generate Meta-Summary
                    summaries = [f.get('detail_summary') for f in found_files if f.get('detail_summary')]
                    meta_summary = ""
                    if summaries and tagger:
                        meta_summary = tagger.summarize_group(summaries)
                    
                    messages_to_send = []
                    
                    if meta_summary:
                        summary_text = f"สรุปภาพรวมของเอกสารที่พบ {len(found_files)} รายการครับ:\n\n{meta_summary}"
                        messages_to_send.append(TextSendMessage(text=summary_text))
                    
                    # 4. Create Flex Message Carousel
                    bubbles = []
                    for file in found_files[:10]: # Limit to 10
                        file_name = file.get('filename', 'Untitled')
                        file_url = file.get('url', '#')
                        file_tags = file.get('tags', [])
                        
                        tag_text = ", ".join([f"#{t}" for t in file_tags[:3]])
                        
                        bubble = {
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": file_name,
                                        "weight": "bold",
                                        "size": "md",
                                        "wrap": True
                                    },
                                    {
                                        "type": "text",
                                        "text": tag_text,
                                        "size": "xs",
                                        "color": "#aaaaaa",
                                        "wrap": True,
                                        "margin": "sm"
                                    }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "button",
                                        "style": "link",
                                        "height": "sm",
                                        "action": {
                                            "type": "uri",
                                            "label": "Download",
                                            "uri": file_url
                                        }
                                    }
                                ]
                            }
                        }
                        bubbles.append(bubble)
                        
                    flex_message = FlexSendMessage(
                        alt_text=f"ผลการค้นหา: {len(found_files)} รายการ",
                        contents={
                            "type": "carousel",
                            "contents": bubbles
                        }
                    )
                    messages_to_send.append(flex_message)
                    
                    line_bot_api.reply_message(event.reply_token, messages_to_send)
            
        elif text == r"/วันดี":
            # Deadline list command
            # TODO: Implement deadline fetching
            reply_text = "📅 รายการ Deadline ที่ใกล้จะถึงครับ..."
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            
        else:
            # Check if user is in a specific mode or just chatting
            if user_states.get(user_id) == "waiting_for_file":
                reply_text = "ผมกำลังรอไฟล์อยู่นะครับ 😅\nถ้าต้องการยกเลิก ให้พิมพ์ 'ยกเลิก' ครับ"
                if text == "ยกเลิก":
                    user_states.pop(user_id, None)
                    reply_text = "ยกเลิกโหมดรับฝากไฟล์เรียบร้อยครับ"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    
    elif isinstance(event.message, (ImageMessage, FileMessage)):
        if user_states.get(user_id) == "waiting_for_file":
            logger.info(f"Retrieving file from user: {user_id}")
            
            # Determine file type first
            file_type = "image" if isinstance(event.message, ImageMessage) else "file"
            original_filename = "unknown"
            
            # File Type Validation
            if file_type == "image":
                # LINE images are typically JPEGs. We'll use jpg as default.
                extension = "jpg" 
            elif file_type == "file":
                # Check if it is PDF
                file_name = event.message.file_name
                original_filename = file_name
                if not file_name.lower().endswith(".pdf"):
                    reply_text = "ขออภัยครับ รองรับเฉพาะไฟล์ PDF 📄 และรูปภาพ 🖼️ เท่านั้นครับ"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
                    return
                extension = "pdf"
            else:
                return

            # Handle file upload
            message_id = event.message.id
            message_content = line_bot_api.get_message_content(message_id)
            
            # Save temporarily with ID first
            temp_save_path = f"/tmp/{message_id}.{extension}"
            
            with open(temp_save_path, 'wb') as fd:
                for chunk in message_content.iter_content():
                    fd.write(chunk)
            
            logger.info(f"File saved locally to {temp_save_path}")

            # Call SLM to categorize and version the file
            generated_metadata = {"tags": [], "title": "Untitled", "summary": ""}
            
            if tagger:
                mime_type = "image/jpeg" if extension in ["jpg", "jpeg", "png"] else "application/pdf"
                logger.info(f"Starting tag generation for {temp_save_path} ({mime_type})")
                try:
                    generated_metadata = tagger.generate_metadata(temp_save_path, mime_type)
                    tags_found = generated_metadata.get("tags", [])
                    if tags_found:
                        logger.info(f"Tags generated successfully: {tags_found}")
                    else:
                        logger.warning("Tag generation returned empty list.")
                except Exception as e:
                    logger.error(f"Tag generation failed: {e}")
            else:
                logger.warning("TagGenerator service is not available.")
            
            raw_tags = generated_metadata.get("tags", [])
            
            # Deduplicate tags
            final_tags = raw_tags
            if deduplicator:
                final_tags = deduplicator.deduplicate(raw_tags)
            
            # Update Global Tag Pool
            # Add new tags to the pool and re-deduplicate to ensure semantic consistency
            if deduplicator and final_tags:
                logger.info(f"Updating tag pool. Current size: {len(tag_pool)}")
                # Combine and remove exact duplicates first
                combined_pool = list(set(tag_pool + final_tags))
                # Semantic deduplication on the whole pool
                tag_pool = deduplicator.deduplicate(combined_pool)
                # Save back to Firebase
                save_tag_pool(tag_pool)
                logger.info(f"Tag pool updated and saved. New size: {len(tag_pool)}")
            elif final_tags:
                tag_pool.extend(final_tags)
                tag_pool = list(set(tag_pool))
                save_tag_pool(tag_pool)

            # Fallback if no tags
            if not final_tags:
                final_tags = ["Uncategorized"]

            mock_tags = final_tags
            mock_name = generated_metadata.get("title", f"File-{message_id}")
            mock_summary = generated_metadata.get("summary", "No summary available")
            suggested_filename = generated_metadata.get("suggested_filename", "")

            # --- Smart Rename Logic ---
            # 1. Determine Base Name
            base_name = "untitled_file"
            
            if suggested_filename:
                base_name = suggested_filename
            elif file_type == "file" and original_filename != "unknown":
                # Fallback to original filename (without extension) if AI didn't suggest one
                base_name = os.path.splitext(original_filename)[0]
                base_name = sanitize_filename(base_name)
            else:
                # Fallback to sanitized title
                base_name = sanitize_filename(mock_name)
            
            # 2. Ensure Uniqueness Loop
            count = 0
            while True:
                if count == 0:
                    candidate_name = f"{base_name}.{extension}"
                else:
                    candidate_name = f"{base_name}_{count}.{extension}"
                
                if not check_filename_exists(candidate_name):
                    final_filename = candidate_name
                    break
                count += 1
            
            logger.info(f"Final filename determined: {final_filename}")
            
            # Save to Firebase
            
            # Fetch User Profile
            try:
                profile = line_bot_api.get_profile(user_id)
                display_name = profile.display_name
            except:
                display_name = "Unknown User"

            # Get Group ID and Name if available
            group_id = None
            group_name = None
            
            if event.source.type == 'group':
                group_id = event.source.group_id
                try:
                    summary = line_bot_api.get_group_summary(group_id)
                    group_name = summary.group_name
                except:
                    group_name = "Unknown Group"
            elif event.source.type == 'room':
                group_id = event.source.room_id
                group_name = "Room" # Rooms don't have names in the same way

            # Ensure user exists and track group
            save_user(user_id, display_name, group_id, group_name) 
            
            # Upload to Firebase Storage
            blob_name = f"uploads/{user_id}/{final_filename}"
            public_url = upload_file_to_storage(temp_save_path, blob_name)
            
            file_data = {
                "filename": final_filename, 
                "file_type": extension, # png or pdf
                "storage_path": blob_name, 
                "url": public_url, 
                "owner_id": user_id,
                "group_id": group_id, 
                "tags": mock_tags,
                "version": "v1",
                "detail_summary": mock_summary, 
                "due_date_id": None
            }
            
            file_id = save_file_metadata(file_data)
            
            # Clean up local temp file
            if os.path.exists(temp_save_path):
                os.remove(temp_save_path)
            
            # Create Flex Message
            liff_id = os.getenv("LIFF_ID", "YOUR_LIFF_ID") # Fallback if not set
            mini_app_url = f"https://miniapp.line.me/{liff_id}"
            
            # Create Tag Bubbles (Pills)
            tag_contents = []
            for tag in mock_tags:
                tag_contents.append({
                    "type": "text",
                    "text": f"#{tag}",
                    "color": "#06C755",
                    "size": "sm",
                    "flex": 0,
                    "margin": "xs"
                })

            flex_message = FlexSendMessage(
                alt_text="จัดการเรียบร้อยครับ! ✅",
                contents={
                    "type": "bubble",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "จัดการเรียบร้อยครับ! ✅",
                                "weight": "bold",
                                "size": "md",
                                "color": "#F8F8F8" 
                            },
                            {
                                "type": "text",
                                "text": final_filename,
                                "size": "xs",
                                "color": "#F2F3F2",
                                "wrap": True,
                                "margin": "xs"
                            }
                        ],
                        "backgroundColor": "#96C678",
                        "paddingAll": "lg"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "Tags:",
                                "size": "sm",
                                "color": "#555555",
                                "margin": "sm",
                                "weight": "bold"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": tag_contents,
                                "wrap": True,
                                "margin": "sm"
                            },
                            {
                                "type": "separator",
                                "margin": "lg"
                            },
                            {
                                "type": "text",
                                "text": "ทำการจัดเก็บไฟล์ไว้ที่นี่",
                                "size": "sm",
                                "color": "#06C755",
                                "margin": "lg",
                                "align": "center",
                                "action": {
                                    "type": "uri",
                                    "label": "Download",
                                    "uri": public_url
                                },
                                "decoration": "underline"
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "height": "sm",
                                "action": {
                                    "type": "uri",
                                    "label": "จัดการเพิ่มเติมได้ที่ MINI APP",
                                    "uri": mini_app_url
                                },
                                "color": "#96C678"
                            }
                        ]
                    }
                }
            )
            
            line_bot_api.reply_message(event.reply_token, flex_message)
            
            # Reset state
            user_states.pop(user_id, None)
        else:
            # Ignore files if not in saving mode? Or maybe auto-save?
            # For now, let's ignore to avoid spam, or give a hint.
            pass
