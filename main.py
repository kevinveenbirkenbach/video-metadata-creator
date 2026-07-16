import subprocess
import json
import os
import argparse
from datetime import datetime
from timezonefinder import TimezoneFinder
import pytz

def get_video_metadata(file_path):
    # Run ffprobe command to get metadata in JSON format
    command = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    metadata = json.loads(result.stdout)
    
    return metadata

def extract_gps_from_metadata(metadata):
    # Extract location from format tags
    location_tag = metadata.get('format', {}).get('tags', {}).get('location', None)
    
    if location_tag:
        # The location is in the format +latitude+longitude
        latitude = float(location_tag[1:8])  # +52.3644
        longitude = float(location_tag[9:16])  # +013.5075
        
        return round(latitude, 4), round(longitude, 4)  # Round to 4 decimal places
    return None

def extract_creation_time(metadata):
    # Extract creation time from the metadata
    creation_time = metadata.get('format', {}).get('tags', {}).get('creation_time', None)
    if creation_time:
        # Convert to datetime object
        return datetime.strptime(creation_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    return None

def get_timezone(latitude, longitude):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=latitude, lng=longitude)  # Get the timezone name
    if timezone_str:
        return timezone_str
    return "UTC"  # Fallback to UTC if no timezone is found

def process_videos(directory, prefix):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                file_path = os.path.join(root, file)
                metadata = get_video_metadata(file_path)
                gps_data = extract_gps_from_metadata(metadata)
                creation_time = extract_creation_time(metadata)
                
                if gps_data and creation_time:
                    latitude, longitude = gps_data
                    
                    # Automatically determine timezone based on GPS coordinates
                    timezone_str = get_timezone(latitude, longitude)
                    tz = pytz.timezone(timezone_str)
                    
                    # Convert creation time to the correct timezone
                    creation_time_local = creation_time.astimezone(tz)
                    formatted_time = creation_time_local.strftime("%Y-%m-%dT%H:%M")
                    
                    # Construct the new title
                    title = f"{prefix} {formatted_time}-{timezone_str}, {longitude}°, {latitude}°"
                    print(f"Generated title for {file}: {title}")
                else:
                    print(f"No GPS or creation time data found for {file}")

def main():
    parser = argparse.ArgumentParser(description="Extract geolocation and generate titles from videos in a folder.")
    parser.add_argument('directory', type=str, help="Path to the folder containing the videos.")
    parser.add_argument('prefix', type=str, help="Prefix for the generated titles.")
    
    args = parser.parse_args()
    directory = args.directory
    prefix = args.prefix

    # Check if the directory exists
    if not os.path.isdir(directory):
        print(f"The path {directory} is not a valid directory.")
        return
    
    # Process the videos in the folder
    process_videos(directory, prefix)

if __name__ == "__main__":
    main()
