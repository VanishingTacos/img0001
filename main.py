from atproto import Client
import requests
from dateutil import parser
import os
import pytz
from youtube import fetch_youtube_vid
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Access the environment variables
bluesky_username = os.getenv("BLUESKY_USERNAME")
bluesky_password = os.getenv("BLUESKY_PASSWORD")

# Helper function to format datetime objects UTC to EST
def convert_datetime_obj_to_est(dt_obj):
    est = pytz.timezone("US/Eastern")
    return dt_obj.astimezone(est)

# Helper function to convert seconds to MM:SS format
def convert_seconds_to_mmss(seconds):
    return f"{seconds // 60}:{seconds % 60:02d}"

def main():
    # Fetch random video data
    try:
        random_vid = requests.get("https://walzr.com/IMG_0001/random")
        random_vid.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        exit()

    if random_vid.status_code == 200:
        response_data = random_vid.json()
        random_vid_id = response_data.get("id")
        random_vid_duration = convert_seconds_to_mmss(response_data.get("duration"))
        random_vid_date = response_data.get("published")  # Expecting an ISO 8601 date string
        random_vid_views = response_data.get("views")

        if random_vid_id:
            random_vid_url = f"https://www.youtube.com/watch?v={random_vid_id}"
        else:
            print("No ID has been found")
            exit()

    if random_vid_date:
        try:
            # Parse the date string and ensure it's in UTC
            random_vid_date_obj = parser.isoparse(random_vid_date).replace(tzinfo=pytz.utc)
            # Convert to EST
            random_vid_date_est = convert_datetime_obj_to_est(random_vid_date_obj)
            # Format the output
            formatted_date = random_vid_date_est.strftime("%B %d, %Y at %I:%M %p")
        except (ValueError, TypeError):
            print(f"Invalid date format: {random_vid_date}")
            formatted_date = "N/A"
    else:
        formatted_date = "N/A"

    title, description, thumbnail, channel_title = fetch_youtube_vid(random_vid_id)

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
            thumb = client.upload_blob(img_data)
    except Exception as e:
        print(f"Failed to upload thumbnail: {e}")
        exit()

    # Create the post with an external link embed
    print(random_vid_duration)
    print(formatted_date)
    post_content = f"📹 {title}\n👤 Channel: {channel_title}\n👁 Views: {random_vid_views}\n🕑 Duration: {random_vid_duration}\n📅 Published: {formatted_date}"
    embed = {
        "$type": "app.bsky.embed.external",
        "external": {
            "uri": random_vid_url,
            "title": title,
            "description": description,
            "thumb": thumb["blob"], 
        },
    }

    # Send the post
    try:
        post = client.send_post(text=post_content, embed=embed)
    except Exception as e:
        print(f"Failed to create post: {e}")

if __name__ == "__main__":
    main()
