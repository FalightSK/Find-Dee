import os
import firebase_admin
from firebase_admin import credentials, db
from search.deduplicator import TagDeduplicator
from firebase_config import initialize_firebase, get_tag_pool, save_tag_pool, get_candidate_files, update_file_metadata

def deduplicate_tags_script():
    # 1. Initialize Firebase
    app = initialize_firebase()
    if not app:
        print("Failed to initialize Firebase.")
        return

    print("Firebase initialized.")

    # 2. Initialize Deduplicator
    try:
        deduplicator = TagDeduplicator()
    except Exception as e:
        print(f"Failed to initialize TagDeduplicator: {e}")
        return

    print("TagDeduplicator initialized.")

    # 3. Fetch Data
    print("Fetching files and tag pool...")
    files = get_candidate_files()
    tag_pool = get_tag_pool() or []
    
    print(f"Found {len(files)} files.")
    print(f"Current tag pool size: {len(tag_pool)}")

    # 4. Collect all unique tags
    all_tags = set(tag_pool)
    for file in files:
        if 'tags' in file and isinstance(file['tags'], list):
            all_tags.update(file['tags'])
            
    all_tags_list = list(all_tags)
    print(f"Total unique tags to process: {len(all_tags_list)}")
    
    if not all_tags_list:
        print("No tags found. Exiting.")
        return

    # 5. Deduplicate and Map
    print("Deduplicating tags (this may take a moment)...")
    tag_mapping = deduplicator.deduplicate_and_map(all_tags_list)
    
    print("Deduplication complete.")
    # print(f"Mapping: {tag_mapping}")

    # 6. Update Tag Pool
    new_tag_pool = sorted(list(set(tag_mapping.values())))
    print(f"New tag pool size: {len(new_tag_pool)}")
    save_tag_pool(new_tag_pool)
    print("Tag pool updated.")

    # 7. Update Files
    print("Updating file tags...")
    updated_count = 0
    for file in files:
        file_id = file.get('id')
        original_tags = file.get('tags', [])
        
        if not original_tags:
            continue
            
        new_tags = []
        for tag in original_tags:
            if tag in tag_mapping:
                new_tags.append(tag_mapping[tag])
            else:
                # Should not happen if logic is correct, but keep original if missing
                new_tags.append(tag)
        
        # Deduplicate tags within the file itself
        new_tags = sorted(list(set(new_tags)))
        
        if new_tags != sorted(original_tags):
            update_file_metadata(file_id, {'tags': new_tags})
            updated_count += 1
            print(f"Updated file {file_id}: {original_tags} -> {new_tags}")
            
    print(f"Finished. Updated {updated_count} files.")

if __name__ == "__main__":
    deduplicate_tags_script()
