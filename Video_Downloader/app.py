from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, send_file
import yt_dlp
import os
import platform
import re
import time

app = Flask(__name__)
app.secret_key = '1bd8a0bf5cde61924846417da9b121c2'

progress_data = {"progress": 0}  
downloaded_file_path = None  

# Function to get the default download path
def get_default_download_path():
    if platform.system() == 'Windows':
        return os.path.join(os.getenv('USERPROFILE'), 'Downloads')
    elif platform.system() == 'Darwin':  # macOS
        return os.path.join(os.path.expanduser('~'), 'Downloads')
    else:  # Linux
        return os.path.join(os.path.expanduser('~'), 'Downloads')

# Function to get the default desktop path
def get_default_desktop_path():
    if platform.system() == 'Windows':
        return os.path.join(os.getenv('USERPROFILE'), 'Desktop')
    elif platform.system() == 'Darwin':  # macOS
        return os.path.join(os.path.expanduser('~'), 'Desktop')
    else:  # Linux
        return os.path.join(os.path.expanduser('~'), 'Desktop')

# Function to sanitize filenames
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

# Progress hook to show download progress
def progress_hook(d):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded_bytes = d.get('downloaded_bytes', 0)

        if total_bytes > 0:
            percent = (downloaded_bytes / total_bytes) * 100
            progress_data["progress"] = round(percent, 2)
        else:
            progress_data["progress"] = 0
    elif d['status'] == 'finished':
        progress_data["progress"] = 100

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/progress')
def progress():
    return jsonify(progress_data)  # Return the progress data as JSON

@app.route('/download', methods=['POST'])
def download():
    global progress_data, downloaded_file_path
    progress_data["progress"] = 0  # Reset progress before starting download
    video_url = request.form['video_url']
    path_choice = request.form.get('path_choice')

    # Select the output path based on user choice
    output_path = get_default_download_path() if path_choice == 'downloads' else get_default_desktop_path()

    # Check if output path exists
    if not os.path.exists(output_path):
        flash(f'The directory {output_path} does not exist.', 'danger')
        return redirect(url_for('index'))

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'quiet': True,          # Suppress all unnecessary logs
        'no-warnings': True,    # Suppress warnings
        'logger': None,         # Disable internal yt-dlp logger
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }

    try:
        # Download the video and extract the title
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            video_title = info_dict.get('title', 'video')
            video_title_sanitized = sanitize_filename(video_title)

            # Get the final file path of the downloaded video
            downloaded_file_path = os.path.join(output_path, f"{video_title_sanitized}.mp4")

            # Set the file's modification and access time to the current time
            current_time = time.time()
            os.utime(downloaded_file_path, (current_time, current_time))

        # Send the file directly after download without redirecting
        return send_file(downloaded_file_path, as_attachment=True, download_name=os.path.basename(downloaded_file_path))

    except yt_dlp.DownloadError as e:
        flash(f"Download error: {str(e)}", 'danger')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
