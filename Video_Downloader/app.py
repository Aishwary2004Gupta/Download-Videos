from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, send_file, after_this_request
import yt_dlp
import os
import re
import time
import tempfile
import shutil

app = Flask(__name__)
app.secret_key = '1bd8a0bf5cde61924846417da9b121c2'

progress_data = {"progress": 0}
downloaded_file_path = None

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
    return jsonify(progress_data)

@app.route('/download', methods=['POST'])
def download():
    global progress_data, downloaded_file_path
    progress_data["progress"] = 0
    video_url = request.form['video_url']

    # Ensure the form is reset after download
    video_url = video_url.strip()
    if not video_url:
        flash("Please enter a valid URL.", "danger")
        return redirect(url_for('index'))

    print(f"Download requested for URL: {video_url} at {time.time()}")

    temp_dir = tempfile.mkdtemp()

    # Custom headers to simulate browser behavior
    custom_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Download best quality video + audio
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no-warnings': True,
        'retries': 10,  # Increase retries for network issues
        'http_headers': custom_headers,  # Custom headers for Instagram/Twitter
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'noplaylist': True,  # Only download single video, not playlist
        'timeout': 600,  # Increase timeout to avoid connection issues
        'sleep_interval_requests': 5,  # Pause between requests to prevent rate-limiting
        'geo_bypass': True,  # Allow geo-restricted downloads
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            video_title = info_dict.get('title', 'video')
            video_title_sanitized = sanitize_filename(video_title)

            downloaded_file_path = os.path.join(temp_dir, f"{video_title_sanitized}.mp4")

            current_time = time.time()
            os.utime(downloaded_file_path, (current_time, current_time))

        @after_this_request
        def cleanup(response):
            try:
                time.sleep(1)
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error cleaning up temp dir: {e}")
            return response

        # Send the downloaded file and then clear the URL
        if os.path.exists(downloaded_file_path):
            flash('Download completed successfully!', 'success')
            return send_file(downloaded_file_path, as_attachment=True, download_name=f"{video_title_sanitized}.mp4")
        else:
            flash('The file could not be found.', 'danger')

    except yt_dlp.DownloadError as e:
        # Check for login-required error for Instagram
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
