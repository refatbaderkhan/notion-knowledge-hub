# Notion Knowledge Hub Pipeline

An automated pipeline that transforms content into a structured knowledge base in Notion. Currently supports YouTube videos with plans to expand to articles, Kindle highlights, and other content sources.

The tool extracts metadata and transcripts, uses AI to generate summaries and extract key insights, then creates interconnected database entries for media, entities, and atomic knowledge snippets.

## What It Does

This tool bridges the gap between consuming video content and building a queryable knowledge repository. Instead of bookmarking videos and hoping to remember their insights, you get:

- **Comprehensive summaries** in markdown format
- **Atomic knowledge snippets** that stand alone and remain useful out of context
- **Automatic entity linking** that connects related concepts across your entire knowledge base
- **Date extraction** for historical facts and events mentioned in videos

Perfect for researchers, content curators, and anyone building a personal knowledge management system.

## Current Support

**YouTube Videos** (fully implemented)

- Video metadata extraction
- Transcript fetching (English/Arabic)
- AI-powered summarization and snippet extraction

**Potential Expansion**

- Articles and blog posts
- Kindle highlights
- PDF documents

## Architecture

```
YouTube API → Transcript Extraction → Gemini → Notion Database
```

The pipeline consists of three main processors:

1. **YoutubeExtractor** - Pulls video metadata and transcripts via Google's YouTube Data API and youtube-transcript-api
2. **GeminiProcessor** - Analyzes content using structured output with Pydantic validation to ensure clean, consistent data
3. **NotionIngester** - Creates and links database entries across three interconnected tables (Media, Entities, Snippets)

## Key Features

- **Smart entity resolution** with caching to avoid duplicate entries
- **Batch processing** of multiple videos from a JSON list
- **Graceful error handling** with detailed logging at every step
- **Markdown-formatted summaries** stored as code blocks in Notion
- **Automatic date parsing** from natural language (e.g., "early 1980s" → ISO 8601)
- **Relational linking** between snippets, entities, and source media

## Setup

### Prerequisites

Before you begin, ensure you have:

- **Python 3.8 or higher** installed on your system
- A **Notion account** (free tier works fine)
- **Google Cloud account** for YouTube API access
- **Google AI Studio account** for Gemini API access

### Step 1: Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/refatbaderkhan/notion-knowledge-ingestor
cd notion-knowledge-hub

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### Step 2: Set Up Notion Workspace

#### 2.1 Duplicate the Template

1. Visit the [Notion Knowledge Hub template](https://purring-bar-7da.notion.site/Knowledge-Hub-template-2b22dcfd8ce5808bba71f821e854ac18)
2. Click **"Duplicate"** in the top-right corner to add it to your workspace
3. This creates three interconnected databases:
   - **Media** - Stores video summaries and metadata
   - **Entities** - Tracks people, concepts, and organizations
   - **Snippets** - Contains atomic knowledge extracts

#### 2.2 Create a Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Give it a name (e.g., "Knowledge Hub Ingestor")
4. Select the workspace where you duplicated the template
5. Click **"Submit"** to create the integration
6. Copy the **Internal Integration Token** (starts with `secret_...`)

#### 2.3 Connect Integration to Your Databases

You need to grant your integration access to each database:

1. Open your duplicated **Media** database in Notion
2. Click the **"⋯"** menu in the top-right
3. Scroll down and click **"+ Add connections"**
4. Find and select your integration
5. **Repeat steps 1-4 for the Entities and Snippets databases**

#### 2.4 Get Database IDs

You need the database IDs for each of the three tables:

1. Open each database as a **full page** (not inline)
2. Look at the URL in your browser:
   ```
   https://www.notion.so/{workspace_name}/{DATABASE_ID}?v=...
   ```
3. The `DATABASE_ID` is the 32-character string (with hyphens) between your workspace name and the `?v=`
4. Copy the database ID for:
   - Media database → `MEDIA_DB_ID`
   - Entities database → `ENTITIES_DB_ID`
   - Snippets database → `SNIPPETS_DB_ID`

### Step 3: Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **"APIs & Services"** → **"Library"**
4. Search for **"YouTube Data API v3"**
5. Click **"Enable"**
6. Go to **"APIs & Services"** → **"Credentials"**
7. Click **"+ CREATE CREDENTIALS"** → **"API key"**
8. Copy your API key and optionally restrict it to YouTube Data API v3

### Step 4: Get Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Select a Google Cloud project (or create a new one)
5. Copy the generated API key

### Step 5: Configure Environment Variables

rename `.env.template` to `.env`.

Add the following content to `.env`:

```env
# Notion Configuration
NOTION_API_KEY=secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# YouTube API (from Google Cloud Console)
GOOGLE_API=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Gemini API (from Google AI Studio)
GEMINI_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Notion Database IDs (32-character strings with hyphens)
MEDIA_DB_ID=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
ENTITIES_DB_ID=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
SNIPPETS_DB_ID=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### Step 6: Prepare Video List

Edit `youtube_ids.json` to include the YouTube video IDs you want to process:

```json
["youtube_id_1", "youtube_id_2", "youtube_id_3"]
```

**How to get a YouTube video ID:**

- From URL `https://www.youtube.com/watch?v=AUiqaFIONPQ`
- The ID is everything after `v=` → `AUiqaFIONPQ`

### Step 7: Run the Pipeline

```bash
python main.py
```

**What happens:**

1. The script reads video IDs from `youtube_ids.json`
2. For each video:
   - Fetches metadata and transcript from YouTube
   - Sends content to Gemini for analysis
   - Creates linked entries in your Notion databases
   - Saves backup JSON files to `output_data/`
3. Progress is logged to both console and `myapp.log`

## Project Structure

```
├── config.py           # Environment and path configuration
├── youtube.py          # YouTube API client and transcript fetching
├── gemini.py           # Gemini API integration with Pydantic models
├── notion.py           # Notion client with entity resolution and page creation
├── main.py             # Orchestration and batch processing
├── prompt.txt          # System instructions for Gemini (extraction rules)
├── requirements.txt    # Python dependencies
└── youtube_ids.json    # Input list of video IDs to process
```

## How It Works

### 1. Extraction

The YouTube extractor fetches video metadata (title, description, publish date, channel) and retrieves English or Arabic transcripts. If no transcript is available, the video is skipped.

### 2. Analysis

The Gemini processor sends the combined metadata and transcript to Google's Gemini 2.5 Flash model with specific instructions to:

- Generate a markdown summary capturing main arguments and themes
- Extract atomic knowledge snippets that are self-contained and properly contextualized
- Identify entities (people, places, concepts) using Wikipedia-style formal naming
- Parse and normalize dates into ISO 8601 format

### 3. Ingestion

The Notion ingester creates three types of database entries:

- **Media page** with the full summary, URL, and metadata
- **Entity pages** for any new people/concepts (with deduplication)
- **Snippet pages** linking back to the source media and related entities

## Technical Highlights

- **Structured outputs** via Pydantic ensure type safety and validation
- **Functional caching** on entity resolution reduces redundant API calls
- **Chunked content handling** for large summaries (Notion has a 2000-character limit per block)
- **Retry logic** for date validation errors in Notion's API
- **Comprehensive logging** to both file and console for debugging

## Dependencies

Core libraries:

- `notion-client` - Official Notion API client
- `google-genai` - Google's Gemini API
- `googleapiclient` - YouTube Data API v3
- `youtube-transcript-api` - Unofficial transcript fetching
- `pydantic` - Data validation and settings management

See `requirements.txt` for full list with versions.
