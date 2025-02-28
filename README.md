# Notion Folder Iterator

Using AI to facilitate the BS tasks in my life - Part II.

This script mirrors a local folder structure into a specified Notion page. It creates pages for folders and files, adding file contents to child pages.

## Features

1. **Recursive Mirroring**  
   - Folders become pages, containing child pages for subfolders or files.  
   - Text-based files (`.txt`, `.md`, `.docx`, `.rtf`) are read and inserted into Notion pages as text blocks.  
   - Other file formats get a page with a *File* block (using a dummy URL in this example because the Notion API does not current support file upload).

2. **Chunked Text**  
   - Handles Notion’s limit of **2,000 characters per block** by chunking larger text into multiple blocks.

3. **Sorted Output**  
   - Child items in each folder are sorted alphabetically.

## Prerequisites

1. **Python 3.7+** (Recommended to use a virtual environment).  
2. **[Notion Internal Integration Token](https://developers.notion.com/docs/getting-started)**.  
3. **`.env` file** with the token (see [Setup](#setup) below).

## Setup

1. **Clone or Download this Repository**
   	```
	git clone https://github.com/sfw/NotionFolderIterator.git
	cd NotionFolderIterator
	```


2.	**Install Dependencies**
	```
	pip install -r requirements.txt
	```

	This should install:
	- notion-client (Python wrapper for Notion API)
	- python-dotenv (for loading environment variables from .env)

3.	**Create Your .env File**
	Inside the project folder, create a file named .env:
	```
	touch .env
	```
	Edit .env with a line containing your Notion integration token:
	```
	NOTION_TOKEN=ntn_secret_yourIntegrationTokenHere
	```
	Make sure not to commit this file to version control if it contains secrets.

## Connecting to Notion

1. **Create a Notion Internal Integration**
	- Go to Notion My Integrations and click “New integration”.
	- Choose a name (e.g., “Folder Mirror App”), and select the workspace it belongs to.
	- Under Capabilities, make sure permission is given for reading/writing pages and blocks.
	- Copy the Internal Integration Token (starts with secret_...).

2. **Share Your Target Notion Page With the Integration**
	- In Notion, open the page you want to use as the parent page (the “destination page”).
	- Click Share (top right).
	- Select “Connections…” → “Select Integration” → choose your integration.
	- Save. Now your integration has permission to create child pages/blocks inside that page.

3. **Obtain the Notion Page ID**

	In your browser, open the Notion page. The URL looks like:
	
	https://www.notion.so/YourPageName-XXNXNXNXNXNXNXNXNXNXNXNXNXN


	Copy only the UUID portion after the last - (32 or 36 characters). For example:

	XXNXNXNXNXNXNXNXNXNXNXNXNXN

	That is the ID you will pass via -p/--page when running the script.

## Usage

Once your .env is configured and you have your Notion page ID, run:
```
python NotionFolderIterator.py --page "XXNXNXNXNXNXNXNXNXNXNXNXNXN" --folder "/path/to/local/folder"
```
**Command line options:**
- -p, --page (required): The parent Notion page ID (UUID).
- -f, --folder (required): The path to the local root folder you want to be mirrored into Notion.
- -d, --debug: Verbose debug logging to console

## Example
```
python NotionFolderIterator.py -p "XXNXNXNXNXNXNXNXNXNXNXNXNXN" -f "/Users/myuser/Documents/Projects"
```
The script will:
1.	Recursively traverse "/Users/myuser/Documents/Projects".
2.	For each folder, create a corresponding page in Notion.
3.	For .txt, .md, .doc, .rtf files, read text content into paragraph blocks.
4.	For all other file types, create a file block with a dummy external link (you can update it to a real hosting mechanism if needed).

## Notes
- File Uploads (FUTURE FUNCTIONALITY): non-text files are added with a “dummy URL.” If you need to truly upload files, you’ll need to implement an approach tohost files publicly and pass in the real URLs.
- Text Parsing: For .docx or .rtf, the script reads only the text. .doc is fully unsupported.
- Chunked Blocks: Notion imposes a 2,000-character limit per text block, so text files longer than that are split across multiple paragraphs.

## Contributing

Feel free to open issues or pull requests if you’d like to extend or improve this script:
- Improved file parsing -  extraction media, handling of other formats.
- Real file uploads instead of dummy URLs

## License

MIT License

