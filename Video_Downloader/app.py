from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, send_file, after_this_request
import yt_dlp
import os
import re
import time

app = Flask(__name__)
app.secret_key = '1bd8a0bf5cde61924846417da9b121c2'

progress_data = {"progress": 0}
downloaded_file_path = None

def sanitize_filename(filename):
    # Ensure we have a clean filename without invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Remove any leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    return sanitized

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
    return jsonify(progress_data)

@app.route('/download', methods=['POST'])
def download():
    global progress_data, downloaded_file_path
    progress_data["progress"] = 0
    video_url = request.form['video_url'].strip()

    if not video_url:
        flash("Please enter a valid URL.", "danger")
        return redirect(url_for('index'))

    print(f"Download requested for URL: {video_url} at {time.time()}")

    download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')

    try:
        # First, extract info without downloading
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            video_title = info_dict.get('title', 'video')
            video_title_sanitized = sanitize_filename(video_title)
            # Prepare the full output path
            output_path = os.path.join(download_dir, f"{video_title_sanitized}.mp4")

        # Configure download options with specific output template
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': output_path,  # Use the specific output path
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'retries': 10,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'noplaylist': True,
            'timeout': 600,
            'sleep_interval_requests': 5,
            'geo_bypass': True,
        }

        # Download the video with the specified options
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            downloaded_file_path = output_path

        # Verify file exists and send it
        if os.path.exists(downloaded_file_path):
            flash('Download completed successfully!', 'success')
            return send_file(
                downloaded_file_path,
                as_attachment=True,
                download_name=f"{video_title_sanitized}.mp4"
            )
        else:
            flash('The file could not be found.', 'danger')

    except yt_dlp.DownloadError as e:
        if "login required" in str(e).lower() and "instagram" in video_url:
            flash('Instagram video download requires login. Please use cookies or login details.', 'danger')
        elif "rate-limit" in str(e).lower():
            flash('Request rate limit reached. Please try again later.', 'danger')
        else:
            flash(f"Download error: {str(e)}", 'danger')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)