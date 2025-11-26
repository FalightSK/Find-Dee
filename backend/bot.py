from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    ImageMessage, FileMessage, FlexSendMessage
)
import os
from firebase_config import save_file_metadata, save_user, upload_file_to_storage

# Simple in-memory state for prototype: {user_id: "mode"}
user_states = {}

def handle_line_event(event, line_bot_api):
    user_id = event.source.user_id

    print(user_states.get(user_id))
    
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
            # TODO: Implement search logic
            reply_text = f"🔍 กำลังค้นหาเอกสารเกี่ยวกับ '{query}' ให้ครับ..."
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            
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
            print("Retrieving file")
            
            # Determine file type first
            file_type = "image" if isinstance(event.message, ImageMessage) else "file"
            
            # File Type Validation
            if file_type == "image":
                # LINE images are typically JPEGs. We'll use jpg as default.
                extension = "jpg" 
            elif file_type == "file":
                # Check if it is PDF
                file_name = event.message.file_name
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
            
            save_path = f"/tmp/{message_id}.{extension}"
            
            with open(save_path, 'wb') as fd:
                for chunk in message_content.iter_content():
                    fd.write(chunk)
            
            # TODO: Call SLM to categorize and version the file
            # Mocking SLM result for now
            mock_tags = ["Uncategorized"]
            if file_type == "image":
                mock_tags = ["Image", "Lecture"]
            
            # TODO: Call SLM to name and summarize the file
            mock_name = "Mock Name"
            mock_summary = "Mock Summary"

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
            blob_name = f"uploads/{user_id}/{message_id}.{extension}"
            public_url = upload_file_to_storage(save_path, blob_name)
            
            file_data = {
                "filename": f"{message_id}.{extension}", # message_id is placeholder for SLM
                "file_type": extension, # png or pdf
                "storage_path": blob_name, 
                "url": public_url, # Save URL separately if needed, or just rely on storage_path
                "owner_id": user_id,
                "group_id": group_id, 
                "tags": mock_tags,
                "version": "v1",
                "detail_summary": "Auto-generated summary...", # Placeholder for SLM
                "due_date_id": None
            }
            
            file_id = save_file_metadata(file_data)
            
            # Clean up local temp file
            if os.path.exists(save_path):
                os.remove(save_path)
            
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
                                "text": f"{message_id}.{extension}",
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
