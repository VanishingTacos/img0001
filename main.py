from atproto import Client
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Access the environment variables
youtube_api_key = os.getenv("YOUTUBE_API_KEY")
bluesky_username = os.getenv("BLUESKY_USERNAME")
bluesky_password = os.getenv("BLUESKY_PASSWORD")

# Function to fetch YouTube video details
def fetch_youtube_vid(random_vid_id):
    url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={random_vid_id}&key={youtube_api_key}'

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
        thumbnail_url = snippet["thumbnails"]["high"]["url"]  # Use "high" for better resolution
        description = snippet["description"]
        return title, description, thumbnail_url
    else:
        print("No video found for the given ID.")
        exit()

# Fetch random video data
try:
    random_vid = requests.get('https://walzr.com/IMG_0001/random')
    random_vid.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    exit()

# Helper function to format datetime objects
def convert_datetime_obj(dt_obj):
    return dt_obj.strftime("%B %d, %Y at %H:%M:%S")

if random_vid.status_code == 200:
    response_data = random_vid.json()
    random_vid_id = response_data.get('id')
    random_vid_date = response_data.get('published')  # Expecting an ISO 8601 date string
    random_vid_views = response_data.get('views')

    if random_vid_id:
        random_vid_url = f'https://www.youtube.com/watch?v={random_vid_id}'
    else:
        print('No ID has been found')
        exit()

    if random_vid_date:
        try:
            dt_obj = datetime.fromisoformat(random_vid_date)  # Convert string to datetime
            human_readable_date = convert_datetime_obj(dt_obj)
        except ValueError:
            print(f"Invalid date format: {random_vid_date}")
    else:
        print("No 'published' date found in the response.")
        exit()

    title, description, thumbnail = fetch_youtube_vid(random_vid_id)

    # Download the thumbnail image
    thumbnail_path = "thumbnail.jpg"
    try:
        response = requests.get(thumbnail, stream=True)
        response.raise_for_status()
        with open(thumbnail_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading thumbnail: {e}")
        exit()

    # Initialize the Bluesky client
    client = Client()
    client.login(bluesky_username, bluesky_password)

    # Upload the thumbnail image as a blob
    try:
        with open(thumbnail_path, "rb") as f:
            img_data = f.read()
            thumb = client.upload_blob(img_data)  # Correct usage of `upload_blob` on the instance
    except Exception as e:
        print(f"Failed to upload thumbnail: {e}")
        exit()

    # Create the post with an external link embed
    post_content = f'📹 {title}\n👁 Views: {random_vid_views}\n📅 Published: {human_readable_date}\n\n🔗 {random_vid_url}'
    embed = {
        "$type": "app.bsky.embed.external",
        "external": {
            "uri": random_vid_url,
            "title": title,
            "description": description,
            "thumb": thumb["blob"]  # Correctly using the returned blob
        }
    }

    # Send the post
    try:
        post = client.send_post(text=post_content, embed=embed)
    except Exception as e:
        print(f"Failed to create post: {e}")
