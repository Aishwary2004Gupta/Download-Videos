from flask import Flask, render_template, request, flash, redirect, url_for, send_file, after_this_request
import yt_dlp
import os
import re
import time
import tempfile
import shutil

app = Flask(__name__)
app.secret_key = '1bd8a0bf5cde61924846417da9b121c2'

downloaded_file_path = None

# Function to sanitize filenames
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    global downloaded_file_path
    video_url = request.form['video_url']

    print(f"Download requested for URL: {video_url} at {time.time()}")

    temp_dir = tempfile.mkdtemp()

    # Custom headers for bypassing credential requirements (Twitter)
    custom_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Settings to improve reliability for Twitter downloads, handle retries and timeouts
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Download best quality video + audio
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': False,  # This will display the download progress in the console
        'no-warnings': True,
        'retries': 10,  # Increase retries for network issues
        'http_headers': custom_headers,  # Custom headers for Twitter
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'noplaylist': True,  # Only download single video, not playlist
        'timeout': 600,  # Increase timeout to avoid connection issues
        'sleep_interval_requests': 5,  # Pause between requests to prevent rate-limiting
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
        if "login required" in str(e).lower() and "instagram" in video_url:
            flash('Instagram video download requires login. Please use cookies or login details.', 'danger')
        else:
            flash(f"Download error: {str(e)}", 'danger')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
