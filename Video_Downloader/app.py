from flask import Flask, render_template, request, flash, redirect, url_for, send_file
import yt_dlp
import os
import platform
import re
import time

app = Flask(__name__)
app.secret_key = '1bd8a0bf5cde61924846417da9b121c2'

def get_default_download_path():
    if platform.system() == 'Windows':
        return os.path.join(os.getenv('USERPROFILE'), 'Downloads')
    elif platform.system() == 'Darwin':  # macOS
        return os.path.join(os.path.expanduser('~'), 'Downloads')
    else:  # Linux
        return os.path.join(os.path.expanduser('~'), 'Downloads')

def get_default_desktop_path():
    if platform.system() == 'Windows':
        return os.path.join(os.getenv('USERPROFILE'), 'Desktop')
    elif platform.system() == 'Darwin':  # macOS
        return os.path.join(os.path.expanduser('~'), 'Desktop')
    else:  # Linux
        return os.path.join(os.path.expanduser('~'), 'Desktop')

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

# Progress hook to show download progress (optional)
def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 100
        print(f'Download progress: {percent:.2f}%')  # You can send this data to the frontend

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    print("Download route called")

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
        'quiet': True,
        'no-warnings': True,
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

        flash(f"Video downloaded successfully: {video_title_sanitized}.mp4", 'success')
        return redirect(url_for('index'))

    except yt_dlp.DownloadError as e:
        flash(f"Download error: {str(e)}", 'danger')
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)