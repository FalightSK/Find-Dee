import firebase_admin
from firebase_admin import credentials, storage, db
import os
import datetime

import base64
import json
import tempfile

# Path to the service account key file
SERVICE_ACCOUNT_KEY_PATH = "serviceAccountKey.json"

def initialize_firebase():
    try:
        cred = None
        
        # Option 1: Try Base64 Env Var (For Cloud Run)
        firebase_creds_base64 = os.environ.get('FIREBASE_CREDENTIALS_BASE64')
        if firebase_creds_base64:
            try:
                creds_json = base64.b64decode(firebase_creds_base64).decode('utf-8')
                creds_dict = json.loads(creds_json)
                cred = credentials.Certificate(creds_dict)
                print("Initialized Firebase using FIREBASE_CREDENTIALS_BASE64 env var.")
            except Exception as e:
                print(f"Failed to decode FIREBASE_CREDENTIALS_BASE64: {e}")

        # Option 2: Try Local File
        if not cred and os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            print(f"Initialized Firebase using {SERVICE_ACCOUNT_KEY_PATH}.")

        if not cred:
            print("Error: Could not find Firebase credentials (env var or file).")
            return None

        # Initialize Firebase Admin SDK
        # Check if already initialized to avoid error on reload
        if not firebase_admin._apps:
            project_id = "find-dee" 
            
            options = {
                'databaseURL': f'https://{project_id}-default-rtdb.firebaseio.com/',
                'storageBucket': f'{project_id}.firebasestorage.app'
            }
            
            app = firebase_admin.initialize_app(cred, options)
            print("Firebase Admin SDK initialized successfully.")
            return app
        else:
            return firebase_admin.get_app()
            
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        return None

def get_db_ref(path='/'):
    return db.reference(path)

def save_user(line_user_id, display_name, group_id=None, group_name=None):
    """Saves or updates user info and tracks group membership."""
    ref = db.reference(f'users/{line_user_id}')
    
    # We only update basic info here. 
    # Lists like files_owned should be updated via specific operations, 
    # but for prototype we might initialize them if not exist.
    # For now, just ensuring the user record exists.
    
    user_data = ref.get()
    if not user_data:
        initial_data = {
            'display_name': display_name,
            'files_owned': [],
            # files_accessible removed as per optimization
            'groups': {}, # map: group_id -> group_name
            'due_dates': [],
            'created_at': str(datetime.datetime.utcnow()),
            'updated_at': str(datetime.datetime.utcnow())
        }
        if group_id:
            initial_data['groups'][group_id] = group_name or "Unknown Group"
        ref.set(initial_data)
    else:
        updates = {
            'display_name': display_name,
            'updated_at': str(datetime.datetime.utcnow())
        }
        if group_id:
            updates[f'groups/{group_id}'] = group_name or "Unknown Group"
        ref.update(updates)

def upload_file_to_storage(file_path, destination_blob_name):
    """Uploads a file to the bucket."""
    bucket = storage.bucket()
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    
    # Make the blob publicly viewable (or generate signed URL)
    # For prototype, let's generate a signed URL valid for 7 days
    url = blob.generate_signed_url(datetime.timedelta(days=7), method='GET')
    return url

def upload_bytes_to_storage(file_bytes, destination_blob_name, content_type):
    """Uploads bytes to the bucket (for API uploads)."""
    bucket = storage.bucket()
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(file_bytes, content_type=content_type)
    
    # Generate signed URL
    url = blob.generate_signed_url(datetime.timedelta(days=7), method='GET')
    return url

def save_file_metadata(file_data):
    """
    Saves file metadata.
    file_data should include: 
    - filename, file_type (png/pdf), storage_path
    - owner_id, group_id
    - tags (list)
    - detail_summary, version, due_date_id (optional)
    """
    files_ref = db.reference('files')
    new_file_ref = files_ref.push() # Generate unique ID
    file_id = new_file_ref.key
    
    file_data['upload_date'] = str(datetime.datetime.utcnow())
    new_file_ref.set(file_data)
    
    # Update User's files_owned
    owner_ref = db.reference(f'users/{file_data["owner_id"]}/files_owned')
    # Firebase lists are weird, often easier to use push() or a dict with keys
    # For simplicity in prototype, we'll use a dict where key is file_id
    owner_ref.update({file_id: True})
    
    return file_id

def update_file_metadata(file_id, updates):
    """Updates specific fields of a file."""
    ref = db.reference(f'files/{file_id}')
    # Only allow updating specific fields to prevent overwriting critical data
    allowed_fields = ['filename', 'tags', 'description', 'detail_summary']
    safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if safe_updates:
        safe_updates['updated_at'] = str(datetime.datetime.utcnow())
        ref.update(safe_updates)
        return True
    return False

def delete_file(file_id):
    """Deletes a file from DB and Storage."""
    file_ref = db.reference(f'files/{file_id}')
    file_data = file_ref.get()
    
    if not file_data:
        return False
        
    # 1. Delete from Storage
    # 1. Delete from Storage
    if 'storage_path' in file_data:
        storage_path = file_data['storage_path']
        
        # Check if it's a URL (legacy bug fix)
        if storage_path.startswith("http"):
            print(f"Skipping storage deletion for legacy file (path is URL): {storage_path}")
        else:
            try:
                # Explicitly get the bucket using the name defined in initialize_firebase
                project_id = "find-dee"
                bucket_name = f'{project_id}.firebasestorage.app'
                bucket = storage.bucket(name=bucket_name)
                
                blob = bucket.blob(storage_path)
                blob.delete()
                print(f"Successfully deleted blob: {storage_path}")
            except Exception as e:
                print(f"Error deleting from storage: {e}")
                # Continue to delete metadata even if storage delete fails
            
    # 2. Remove from User's files_owned
    if 'owner_id' in file_data:
        owner_ref = db.reference(f'users/{file_data["owner_id"]}/files_owned/{file_id}')
        owner_ref.delete()
        
    # 3. Delete Metadata
    file_ref.delete()
    return True

def save_date(date_data):
    """
    Saves due date info.
    date_data: due_date, title, description, tags, file_id (optional)
    """
    dates_ref = db.reference('dates')
    new_date_ref = dates_ref.push()
    date_id = new_date_ref.key
    
    new_date_ref.set(date_data)
    return date_id

def get_user_profile(line_user_id):
    """Retrieves user profile including groups."""
    ref = db.reference(f'users/{line_user_id}')
    return ref.get()

def get_files_by_user(line_user_id):
    """Retrieves files uploaded by a specific user."""
    files_ref = db.reference('files')
    snapshot = files_ref.order_by_child('owner_id').equal_to(line_user_id).get()
    
    files = []
    if snapshot:
        for key, val in snapshot.items():
            val['id'] = key
            # Backfill URL for legacy files
            if 'url' not in val and 'storage_path' in val and val['storage_path'].startswith('http'):
                val['url'] = val['storage_path']
            files.append(val)
    return files

def get_files_by_group(group_id):
    """Retrieves files shared in a specific group."""
    files_ref = db.reference('files')
    snapshot = files_ref.order_by_child('group_id').equal_to(group_id).get()
    
    files = []
    if snapshot:
        for key, val in snapshot.items():
            val['id'] = key
            # Backfill URL for legacy files
            if 'url' not in val and 'storage_path' in val and val['storage_path'].startswith('http'):
                val['url'] = val['storage_path']
            files.append(val)
    return files

def get_dates_by_user(line_user_id):
    """Retrieves dates/tasks for a specific user."""
    try:
        dates_ref = db.reference('dates')
        snapshot = dates_ref.get()
        
        dates = []
        if snapshot:
            if isinstance(snapshot, list):
                # Handle list case (rare but possible if keys are integers)
                for i, val in enumerate(snapshot):
                    if val and val.get('owner_id') == line_user_id:
                        val['id'] = str(i)
                        dates.append(val)
            elif isinstance(snapshot, dict):
                for key, val in snapshot.items():
                    if val.get('owner_id') == line_user_id:
                        val['id'] = key
                        dates.append(val)
        return dates
    except Exception as e:
        print(f"Error in get_dates_by_user: {e}")
        return []

def update_date(date_id, updates):
    """Updates a date/task."""
    ref = db.reference(f'dates/{date_id}')
    if ref.get():
        ref.update(updates)
        return True
    return False

def delete_date(date_id):
    """Deletes a date/task."""
    ref = db.reference(f'dates/{date_id}')
    if ref.get():
        ref.delete()
        return True
    return False

def search_files_by_tags(query_tags):
    """
    Searches for files that contain at least one of the query tags.
    Returns a list of file objects.
    """
    if not query_tags:
        return []
        
    files_ref = db.reference('files')
    snapshot = files_ref.get()
    
    matched_files = []
    if snapshot:
        # Normalize query tags to lower case for case-insensitive matching
        q_tags_lower = set(t.lower() for t in query_tags)
        
        for key, val in snapshot.items():
            file_tags = val.get('tags', [])
            if not file_tags:
                continue
                
            # Check for intersection
            f_tags_lower = set(t.lower() for t in file_tags)
            if q_tags_lower.intersection(f_tags_lower):
                val['id'] = key
                # Backfill URL
                if 'url' not in val and 'storage_path' in val and val['storage_path'].startswith('http'):
                    val['url'] = val['storage_path']
                matched_files.append(val)
                
    return matched_files

def get_tag_pool():
    """Retrieves the global tag pool."""
    ref = db.reference('tags/all')
    tags = ref.get()
    if not tags:
        return []
    return tags

def save_tag_pool(tags):
    """Saves the global tag pool."""
    ref = db.reference('tags/all')
    ref.set(tags)
    return True

def check_filename_exists(filename):
    """Checks if a filename already exists in the database."""
    files_ref = db.reference('files')
    snapshot = files_ref.get()
    
    if not snapshot:
        return False
        
    for val in snapshot.values():
        if val.get('filename') == filename:
            return True
            
    return False

def search_dates(query):
    """
    Searches for dates/events that match the query string.
    Searches in 'title' and 'description' fields.
    """
    if not query:
        return []
        
    dates_ref = db.reference('dates')
    snapshot = dates_ref.get()
    
    matched_dates = []
    if snapshot:
        query_lower = query.lower()
        
        # Handle both list and dict structures just in case
        items = []
        if isinstance(snapshot, list):
            for i, val in enumerate(snapshot):
                if val:
                    val['id'] = str(i)
                    items.append(val)
        elif isinstance(snapshot, dict):
            for key, val in snapshot.items():
                val['id'] = key
                items.append(val)
                
        for val in items:
            title = val.get('title', '').lower()
            description = val.get('description', '').lower()
            
            if query_lower in title or query_lower in description:
                matched_dates.append(val)
                
    return matched_dates

def get_upcoming_dates():
    """Retrieves all upcoming dates (from today onwards)."""
    dates_ref = db.reference('dates')
    snapshot = dates_ref.get()
    
    if not snapshot:
        return []
        
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    upcoming = []
    
    items = []
    if isinstance(snapshot, list):
        for i, val in enumerate(snapshot):
            if val:
                val['id'] = str(i)
                items.append(val)
    elif isinstance(snapshot, dict):
        for key, val in snapshot.items():
            val['id'] = key
            items.append(val)
            
    for val in items:
        # Check 'date' or 'date_time' field
        date_str = val.get('date') or val.get('date_time')
        if date_str and date_str >= today:
            upcoming.append(val)
            
    # Sort by date
    upcoming.sort(key=lambda x: x.get('date') or x.get('date_time') or "")
    return upcoming

def get_dates_this_month():
    """Retrieves all dates in the current month."""
    dates_ref = db.reference('dates')
    snapshot = dates_ref.get()
    
    if not snapshot:
        return []
        
    now = datetime.datetime.now()
    current_month = now.strftime("%Y-%m")
    
    this_month = []
    
    items = []
    if isinstance(snapshot, list):
        for i, val in enumerate(snapshot):
            if val:
                val['id'] = str(i)
                items.append(val)
    elif isinstance(snapshot, dict):
        for key, val in snapshot.items():
            val['id'] = key
            items.append(val)
            
    for val in items:
        date_str = val.get('date') or val.get('date_time')
        if date_str and date_str.startswith(current_month):
            this_month.append(val)
            
    # Sort by date
    this_month.sort(key=lambda x: x.get('date') or x.get('date_time') or "")
    return this_month

def get_all_dates():
    """Retrieves all dates/events."""
    dates_ref = db.reference('dates')
    snapshot = dates_ref.get()
    
    if not snapshot:
        return []
        
    all_dates = []
    
    items = []
    if isinstance(snapshot, list):
        for i, val in enumerate(snapshot):
            if val:
                val['id'] = str(i)
                items.append(val)
    elif isinstance(snapshot, dict):
        for key, val in snapshot.items():
            val['id'] = key
            items.append(val)
            
    return items
