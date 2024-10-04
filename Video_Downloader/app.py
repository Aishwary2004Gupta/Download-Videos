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
    return jsonify(progress_data)

@app.route('/download', methods=['POST'])
def download():
    global progress_data, downloaded_file_path
    progress_data["progress"] = 0
    video_url = request.form['video_url']

    print(f"Download requested for URL: {video_url} at {time.time()}")

    temp_dir = tempfile.mkdtemp()

    # Custom headers for bypassing credential requirements (Instagram/Twitter)
    custom_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Define different format for Instagram and Twitter (bypass login requirements)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # This can be changed to 'best' to allow all formats
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no-warnings': True,
        'logger': None,
        'retries': 10,  # Increased retries for better reliability
        'http_headers': custom_headers,  # Custom headers for Instagram/Twitter
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'noplaylist': False,  # Allow playlist downloading if needed
        'age_limit': None,  # Remove age restrictions
        'source_address': None,  # Allow downloads from any source address
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            video_title = info_dict.get('title', 'video')
            video_title_sanitized = sanitize_filename(video_title)

            downloaded_file_path = os.path.join(temp_dir, f"{video_title_sanitized}.mp4")

            current_time = time.time()
            os.utime(downloaded_file_path, (current_time, current_time))

        # After the request, cleanup temporary files
        @after_this_request
        def cleanup(response):
            try:
                time.sleep(1)
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error cleaning up temp dir: {e}")
            return response

        if os.path.exists(downloaded_file_path):
            return send_file(downloaded_file_path, as_attachment=True, download_name=f"{video_title_sanitized}.mp4")
        else:
            flash('The file could not be found.', 'danger')

    except yt_dlp.DownloadError as e:
        flash(f"Download error: {str(e)}", 'danger')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
