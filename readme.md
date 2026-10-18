# 📊 Instagram AI Growth Report

> **A beginner-friendly guide to understanding this project**

---

## What Does This Project Do?

This project is a tool that helps you **understand how an Instagram account is performing**. You simply paste an Instagram profile URL into the app, and it will:

1. **Collect data** — It automatically fetches the profile details and recent posts from Instagram.
2. **Analyze the data** — It figures out which types of posts get the most likes, the best times to post, and how the follower count is changing over time.
3. **Create charts** — It draws easy-to-read graphs so you can see the results visually.
4. **Generate AI recommendations** — It uses Google Gemini (an AI) to read the analytics and write a personalized growth strategy, explaining exactly what the account owner should do to grow.
5. **Display everything in a dashboard** — All the results are shown in a clean, interactive web app built with Streamlit.

Think of it as having a personal Instagram growth coach that is powered by AI.

---

## Who Is This For?

- Beginners learning how Python, AI, and web scraping work together
- Instagram creators who want to understand their account performance
- Developers who want to study a real-world AI analytics project

---

## Technologies Used (Plain English Explanation)

| Tool / Library | What It Does in This Project |
|---|---|
| **Python** | The main programming language — all the logic is written in Python |
| **Streamlit** | Creates the interactive web dashboard (the visual interface you open in your browser) |
| **Apify** | A cloud service that collects Instagram profile and post data for us (Instagram does not allow direct scraping) |
| **Google Gemini AI** | The main AI model that reads the analytics and writes personalized growth recommendations |
| **Ollama + Llama 3.2** | A local AI model (runs on your own computer) used to create human-readable names for posts |
| **Matplotlib** | Creates the charts and graphs shown in the dashboard |
| **python-dotenv** | Reads your secret API keys from a `.env` file so you do not have to hard-code them |
| **Requests** | Sends messages to the Ollama local AI model running on your computer |
| **MCP (FastMCP)** | A lightweight server module included for future AI tool integration |

---

## Project Structure (What Each File Does)

Here is every folder and file explained in simple terms:

```
Social media report/
│
├── backend/                        ← All the "behind the scenes" code lives here
│   │
│   ├── analytics/
│   │   └── analytics.py            ← The brain of the project. It reads the collected
│   │                                  Instagram data and calculates all the stats:
│   │                                  follower growth, top posts, best posting times,
│   │                                  content type performance, etc.
│   │
│   ├── data/                       ← Where all collected and processed data is saved
│   │   ├── instagram_data.json     ← Raw Instagram post data collected by Apify
│   │   ├── instagram_profile.json  ← Instagram profile info (followers, bio, etc.)
│   │   ├── profile_history.json    ← Follower count snapshots saved over time
│   │   ├── analytics_report.json   ← The final processed analytics results
│   │   ├── llm_recommendations.json← AI-generated growth advice saved here
│   │   └── cache/                  ← Stores previously fetched data so we don't
│   │                                  re-fetch it every time (saves API credits)
│   │
│   ├── llm/
│   │   ├── llm.py                  ← Sends the analytics to Google Gemini and
│   │   │                              gets back a personalized growth strategy
│   │   ├── post_namer.py           ← Uses the local Ollama AI to convert
│   │   │                              technical post IDs into human-readable names
│   │   │                              (e.g. "DZh470dtCr5" → "Morning Workout Reel")
│   │   └── recommendation_builder.py← Reads the analytics and builds a clear list
│   │                                   of data-backed recommendations before
│   │                                   passing them to Gemini
│   │
│   ├── logs/
│   │   ├── logs.py                 ← Sets up the logging system
│   │   └── app.log                 ← A running log file that records what the app
│   │                                  is doing (useful for debugging)
│   │
│   ├── mcp_server/
│   │   └── server.py               ← A small server for future AI tool integrations
│   │                                  (experimental, not used in the main app yet)
│   │
│   ├── scrapers/
│   │   └── instagram_scraper.py    ← Connects to Apify and fetches Instagram
│   │                                  profile + post data. Also checks the local
│   │                                  cache first to avoid unnecessary API calls.
│   │
│   ├── test/                       ← Test scripts used during development
│   │   ├── test_apify.py           ← Tests the Apify connection
│   │   └── check_post_data.py      ← Checks what the raw post data looks like
│   │
│   └── visualization/
│       └── charts.py               ← Draws all the charts using Matplotlib:
│                                      content distribution, average likes,
│                                      posting time performance, top 3 posts
│
├── frontend/
│   └── app.py                      ← The Streamlit web app. This is the file you
│                                      run to start the dashboard. It ties everything
│                                      together and shows it in your browser.
│
├── .env                            ← Your secret API keys go here (never share this file!)
├── .gitignore                      ← Tells Git which files NOT to upload (like .env)
├── README.md                       ← This file you are reading right now
└── requirements.txt                ← The list of Python packages needed to run the project
```

---

## How the App Works — Step by Step

Here is the full journey from entering a URL to seeing the results:

```
Step 1: You open the Streamlit dashboard in your browser
        and paste an Instagram profile URL
                    ↓
Step 2: The Instagram Scraper connects to Apify
        and fetches the profile info + recent posts
        (checks local cache first to save API credits)
                    ↓
Step 3: Follower count is saved as a daily snapshot
        so we can track growth over time
                    ↓
Step 4: The Analytics Engine processes the post data:
        - Which content types (Reels, Carousels, Feed) perform best?
        - Which posting hours get the most likes?
        - What are the top 3 performing posts?
        - How much has the follower count changed?
                    ↓
Step 5: Ollama (local AI) generates human-readable names
        for each post using the post caption and hashtags
                    ↓
Step 6: The Recommendation Builder reads the analytics
        and creates a structured list of data-backed insights
                    ↓
Step 7: Google Gemini reads the insights and writes
        a full personalized growth strategy
                    ↓
Step 8: Charts are drawn using Matplotlib
                    ↓
Step 9: Everything is displayed in the Streamlit dashboard:
        profile info, follower growth, charts, and AI advice
```

---

## Prerequisites (What You Need Before Starting)

Before installing anything, make sure you have:

- **Python 3.10 or newer** installed on your computer
  - Check by running: `python --version` in your terminal
- **An Apify account** with an API token
  - Sign up for free at [apify.com](https://apify.com) → Go to Settings → API & Integrations → Copy your API token
- **A Google Gemini API key**
  - Get one for free at [aistudio.google.com](https://aistudio.google.com) → Click "Get API key"
- **Ollama installed** (optional but recommended — used for post naming)
  - Download from [ollama.com](https://ollama.com) and run `ollama pull llama3.2` in your terminal

---

## Installation — Step by Step

### Step 1: Download the Project

If you have Git installed:
```bash
git clone <your-github-repository-url>
cd "Social media report"
```

Or simply download the project as a ZIP file and extract it.

---

### Step 2: Create a Virtual Environment

A virtual environment keeps this project's packages separate from other Python projects on your computer. This is a good habit.

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You will know it worked when you see `(venv)` appear at the start of your terminal line.

---

### Step 3: Install All Required Packages

```bash
pip install -r requirements.txt
```

This reads the `requirements.txt` file and installs every library the project needs.

---

### Step 4: Set Up Your API Keys

Create a file named `.env` in the project root folder (the same folder as `requirements.txt`).

Add the following lines to the file:

```env
APIFY_API_TOKEN=paste_your_apify_token_here
GEMINI_API_KEY=paste_your_gemini_api_key_here
```

Replace the placeholder text with your actual keys. Never share this file or commit it to GitHub — it is already listed in `.gitignore` so Git will automatically ignore it.

---

### Step 5: Set Up Ollama (Optional — for Post Naming)

Ollama is a free tool that runs AI models locally on your computer. This project uses it to generate readable names for Instagram posts.

1. Download and install Ollama from [ollama.com](https://ollama.com)
2. After installing, open a terminal and run:
   ```bash
   ollama pull llama3.2
   ```
3. Keep Ollama running in the background when you use the app.

> **Note:** If Ollama is not running or not installed, the app will still work — it will fall back to a simpler naming method using the post caption and hashtags. No features are broken without Ollama.

---

## Running the Application

Make sure your virtual environment is activated, then run:

```bash
python -m streamlit run frontend/app.py
```

Streamlit will start a local web server. Open your browser and go to:

```
http://localhost:8501
```

You will see the Instagram AI Growth Report dashboard.

---

## Using the Dashboard

1. **Enter an Instagram URL** in the input field. Example:
   ```
   https://www.instagram.com/username/
   ```
   The profile must be **public** (private accounts cannot be analyzed).

2. **Configure settings** in the left sidebar:
   - Use cached data (instant, no API cost) or force a fresh scrape
   - Set how many posts to analyze

3. **Click Analyze** and wait for the results. The first time takes longer because it fetches data from Apify.

4. **Explore the results:**
   - Profile overview (followers, bio, verification status)
   - Follower growth tracking
   - Analytics charts
   - AI-powered growth recommendations from Google Gemini

---

## Understanding the Charts

| Chart | What It Shows |
|---|---|
| **Content Distribution** | What percentage of posts are Reels, Carousels, or Feed posts |
| **Average Likes by Content Type** | Which type of post gets the most likes on average |
| **Posting Time Performance** | Which hours of the day get the most engagement |
| **Top 3 Posts** | The three posts that received the most likes |

---

## How Follower Growth Tracking Works

Every time you analyze a profile, the app saves today's follower count with today's date. Over time, this builds a history that shows how the follower count changes.

**Important:** The app can only calculate growth between dates that it has actually recorded. If you first use the app today, it will not know the follower count from last month. Growth tracking gets more useful the longer you use the app.

Example output:
```
Start Followers:    15,000   (recorded 2 weeks ago)
Current Followers:  15,500   (recorded today)
Growth:             +500
Growth Percentage:  +3.33%
```

---

## Caching (Saving API Credits)

Every time you analyze a profile, the raw data is saved locally in `backend/data/cache/`. On the next visit to the same profile, the app loads from the cache instead of calling Apify again. This saves your Apify API credits.

You can force a fresh scrape at any time using the "Force Refresh" option in the sidebar.

---

## Data Storage

All data is stored locally as JSON files inside `backend/data/`:

| File | What is Stored |
|---|---|
| `instagram_data.json` | Raw post data collected from Instagram |
| `instagram_profile.json` | Profile info (followers, bio, post count, etc.) |
| `profile_history.json` | Daily follower count snapshots for all analyzed profiles |
| `analytics_report.json` | The processed analytics results |
| `llm_recommendations.json` | The AI-generated growth recommendations |

---

## Logs

The app keeps a running log at `backend/logs/app.log`. If something goes wrong or you want to see what the app did, open that file. It records events like when data was fetched, when snapshots were saved, and any errors that occurred.

---

## API Credits and Cost

- **Apify** — The free tier gives you enough credits for light usage. Each profile scrape consumes some credits. Using the cache avoids repeated credit usage.
- **Google Gemini** — Has a generous free tier. Each recommendation generation sends one request to Gemini.
- **Ollama** — Completely free and runs locally on your computer.

---

## Known Limitations

- Only works with **public** Instagram profiles (private profiles cannot be scraped).
- Follower growth history only starts from the first time you analyze a profile.
- Analytics quality depends on how many posts Apify collects (you can adjust the post limit in settings).
- AI recommendations are based only on the data that was collected — the AI is instructed not to invent anything.

---

## Possible Future Improvements

- Interactive follower growth chart with a timeline
- Month-by-month filtering for analytics
- Support for more social media platforms (YouTube, TikTok, Twitter/X)
- More detailed engagement metrics (saves, shares, reach)
- Downloadable PDF reports
- Scheduled automatic profile tracking
- Advanced AI analysis using more detailed prompts

---

## Security Reminder

- Never paste your API keys directly into Python files.
- Always use the `.env` file for secrets.
- Never commit `.env` to GitHub. It is already in `.gitignore`, but double-check before pushing.

---

## Author

**Deepak Garg**  
AI/ML & Generative AI Developer

---

## Project Status

🚧 **Under Active Development**  
This project is being developed as an AI-powered Instagram analytics and growth recommendation tool with a Streamlit frontend. New features and improvements are being added regularly.