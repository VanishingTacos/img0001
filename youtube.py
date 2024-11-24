import requests
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Access the environment variables
youtube_api_key = os.getenv("YOUTUBE_API_KEY")


# Function to fetch YouTube video details
def fetch_youtube_vid(random_vid_id):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={random_vid_id}&key={youtube_api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        exit()

    data = response.json()
    items = data.get("items", [])
    if items:
        snippet = items[0]["snippet"]
        title = snippet["title"]
        thumbnail_url = snippet["thumbnails"]["high"][
            "url"
        ]  # Use "high" for better resolution
        description = snippet["description"]
        channel_title = snippet["channelTitle"]
        return title, description, thumbnail_url, channel_title
    else:
        print("No video found for the given ID.")
        exit()
