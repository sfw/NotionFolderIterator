#!/usr/bin/env python3

import os
import argparse
import logging

from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

# -------------------------------------------------
# Setup Logging
# -------------------------------------------------
# You can adjust the log level to DEBUG, INFO, WARNING, etc.
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

# -------------------------------------------------
# Load Environment Variables
# -------------------------------------------------
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

if not NOTION_TOKEN:
    logging.error("NOTION_TOKEN not found in environment. Please set it in .env or as an environment variable.")
    exit(1)

notion = Client(auth=NOTION_TOKEN)

# -------------------------------------------------
# Notion Helpers
# -------------------------------------------------

def create_notion_page(parent_page_id: str, title: str) -> str:
    """
    Creates a new page inside the given Notion parent page,
    with the given title. Returns the newly created page ID.
    """
    logging.debug(f"Attempting to create Notion page under parent '{parent_page_id}' with title: '{title}'")
    try:
        new_page = notion.pages.create(
            parent={"page_id": parent_page_id},
            properties={
                "title": [{"type": "text", "text": {"content": title}}]
            }
        )
        page_id = new_page["id"]
        logging.info(f"Created page '{title}' -> Page ID: {page_id}")
        return page_id
    except APIResponseError as e:
        logging.error(f"Notion API error creating page '{title}': {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error creating page '{title}': {e}")
        raise

def append_text_block(page_id: str, text_content: str):
    """
    Appends the text_content to the given page_id, chunked into multiple
    paragraph blocks if it exceeds 2000 characters. Also batches them so
    we don't exceed Notion's limit of 100 blocks per request.
    """
    logging.debug(f"Appending text block to page {page_id} (content length: {len(text_content)} chars)")
    
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
    try:
        for i in range(0, len(all_blocks), max_blocks_per_request):
            batch = all_blocks[i:i+max_blocks_per_request]
            notion.blocks.children.append(
                block_id=page_id,
                children=batch
            )
        logging.info(f"Appended text block(s) to page {page_id} ({len(chunks)} chunk(s))")
    except APIResponseError as e:
        logging.error(f"Notion API error appending text block to page {page_id}: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error appending text block to page {page_id}: {e}")
        raise

def append_file_block(page_id: str, file_path: str):
    """
    Appends a file block to the Notion page.

    NOTE: This example uses a dummy URL. For real uploads to Notion,
    you'd need the file upload workflow (files:write permission).
    """
    dummy_url = f"https://example.com/files/{os.path.basename(file_path)}"
    logging.debug(f"Appending file block for '{file_path}' with dummy URL '{dummy_url}' to page {page_id}")
    try:
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
        logging.info(f"Appended file block for '{file_path}' to page {page_id}")
    except APIResponseError as e:
        logging.error(f"Notion API error appending file block for '{file_path}' to page {page_id}: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error appending file block for '{file_path}' to page {page_id}: {e}")
        raise

# -------------------------------------------------
# Main Logic
# -------------------------------------------------

def sync_folder_to_notion(folder_path: str, parent_page_id: str):
    """
    Recursively walk through the local file system and mirror the structure in Notion.
    - Folders become pages containing their children.
    - Text-like files become pages with text blocks.
    - Other files become pages with a file block (or you can embed them however you like).
    """
    if not os.path.isdir(folder_path):
        logging.error(f"'{folder_path}' is not a valid directory. Skipping.")
        return

    items = sorted(os.listdir(folder_path))
    logging.info(f"Syncing folder '{folder_path}' -> Notion page {parent_page_id}")
    
    for item in items:
        # Skip hidden files or folders if desired
        if item.startswith('.'):
            logging.debug(f"Skipping hidden item '{item}'")
            continue

        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            logging.info(f"Processing subfolder '{item_path}'")
            try:
                folder_page_id = create_notion_page(parent_page_id, item)
            except Exception:
                # If we fail to create the page, skip recursion
                logging.warning(f"Skipping '{item_path}' due to page creation failure.")
                continue
            # Recurse into the folder
            sync_folder_to_notion(item_path, folder_page_id)
        else:
            filename, extension = os.path.splitext(item)
            logging.info(f"Processing file '{item_path}' (extension: '{extension}')")
            if extension.lower() in [".txt", ".md", ".doc", ".rtf"]:
                try:
                    with open(item_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                except Exception as e:
                    # If there's an error reading, skip or handle as needed
                    logging.error(f"Error reading file '{item_path}': {e}")
                    file_content = f"Could not parse file {item}"

                try:
                    file_page_id = create_notion_page(parent_page_id, filename)
                    append_text_block(file_page_id, file_content)
                except Exception:
                    logging.warning(f"Failed to process text file '{item_path}'.")
                    continue
            else:
                try:
                    file_page_id = create_notion_page(parent_page_id, filename)
                    append_file_block(file_page_id, item_path)
                except Exception:
                    logging.warning(f"Failed to process file '{item_path}'.")
                    continue

def main():
    parser = argparse.ArgumentParser(description="Mirror a local folder structure into a Notion page.")
    parser.add_argument("-p","--page", required=True, help="Notion destination page ID.")
    parser.add_argument("-f","--folder", required=True, help="Path to the local root folder to mirror.")
    parser.add_argument("-d","--debug", action="store_true", help="Enable addvanced debug logging.")

    args = parser.parse_args()
    notion_destination_page_id = args.page
    local_root_folder = args.folder

    # Set logging level if --debug was specified
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Basic validation for folder path
    if not os.path.isdir(local_root_folder):
        logging.error(f"Error: '{local_root_folder}' is not a valid directory.")
        exit(1)

    # Mirror the folder into Notion
    logging.info("Starting Notion folder sync.")
    sync_folder_to_notion(local_root_folder, notion_destination_page_id)
    logging.info("Sync completed.")

if __name__ == "__main__":
    main()