#!/usr/bin/env python3

import os
import argparse
from dotenv import load_dotenv
from notion_client import Client

# Initialize Notion client using environment variable
# e.g., export NOTION_TOKEN="secret_abc123"
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
notion = Client(auth=NOTION_TOKEN)

def create_notion_page(parent_page_id: str, title: str) -> str:
    """
    Creates a new page inside the given Notion parent page,
    with the given title. Returns the newly created page ID.
    """
    new_page = notion.pages.create(
        parent={"page_id": parent_page_id},
        properties={
            "title": [{"type": "text", "text": {"content": title}}]
        }
    )
    return new_page["id"]

def append_text_block(page_id: str, text_content: str):
    """
    Appends the text_content to the given page_id, chunked into multiple
    paragraph blocks if it exceeds 2000 characters. Also batches them so
    we don't exceed Notion's limit of 100 blocks per request.
    """
    chunk_size = 2000
    max_blocks_per_request = 50  # A bit lower than 100 to be safe

    # Break text_content into chunks of <= 2000 characters.
    chunks = [text_content[i:i+chunk_size] for i in range(0, len(text_content), chunk_size)]
    
    # Build paragraph blocks from the chunks
    all_blocks = []
    for chunk in chunks:
        block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": chunk}
                    }
                ]
            }
        }
        all_blocks.append(block)
    
    # Now we need to append these blocks in batches (max 50 blocks per request).
    for i in range(0, len(all_blocks), max_blocks_per_request):
        batch = all_blocks[i:i+max_blocks_per_request]
        notion.blocks.children.append(
            block_id=page_id,
            children=batch
        )

def append_file_block(page_id: str, file_path: str):
    """
    Appends a file block to the Notion page.

    NOTE: For a real implementation, you'd need a publicly accessible URL
    or handle the Notion file upload process. This example uses a dummy URL.
    """
    dummy_url = f"https://example.com/files/{os.path.basename(file_path)}"
    notion.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "object": "block",
                "type": "file",
                "file": {
                    "type": "external",
                    "external": {
                        "url": dummy_url
                    }
                }
            }
        ]
    )

def sync_folder_to_notion(folder_path: str, parent_page_id: str):
    """
    Recursively walk through the local file system and mirror the structure in Notion.
    - Folders become pages containing their children.
    - Text-like files become pages with text blocks.
    - Other files become pages with a file block (or you can embed them however you like).
    """
    for item in os.listdir(folder_path):
        # Skip hidden files or folders if desired
        if item.startswith('.'):
            continue

        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            # Create a page for the folder
            folder_page_id = create_notion_page(parent_page_id, item)
            # Recurse into the folder
            sync_folder_to_notion(item_path, folder_page_id)
        else:
            filename, extension = os.path.splitext(item)
            # For demonstration, treat ".txt", ".md", ".doc", ".rtf" as text
            if extension.lower() in [".txt", ".md", ".doc", ".rtf"]:
                try:
                    with open(item_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                except:
                    # If there's an error reading, skip or handle as needed
                    file_content = f"Could not parse file {item}"

                # Create a page for this file
                file_page_id = create_notion_page(parent_page_id, filename)
                # Append the text content
                append_text_block(file_page_id, file_content)
            else:
                # Create a page and attach as a file block for non-text formats
                file_page_id = create_notion_page(parent_page_id, filename)
                append_file_block(file_page_id, item_path)

def main():
    parser = argparse.ArgumentParser(description="Mirror a local folder structure into a Notion page.")
    parser.add_argument("-p","--page", required=True, help="Notion destination page ID.")
    parser.add_argument("-f","--folder", required=True, help="Path to the local root folder to mirror.")

    args = parser.parse_args()
    notion_destination_page_id = args.page
    local_root_folder = args.folder

    # Basic validation for folder path
    if not os.path.isdir(local_root_folder):
        print(f"Error: '{local_root_folder}' is not a valid directory.")
        exit(1)

    # Mirror the folder into Notion
    sync_folder_to_notion(local_root_folder, notion_destination_page_id)

if __name__ == "__main__":
    main()