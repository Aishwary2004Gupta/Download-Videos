from flask import Flask, render_template, request, flash, redirect, url_for, send_file, Response
import yt_dlp
import os
import platform
import time
import re

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

def progress_hook(d):
    if d['status'] == 'downloading':
        # Send progress to the client
        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
        print(f'Download progress: {percent:.2f}%')  # You can log this or send it to the client

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    video_url = request.form['video_url']
    path_choice = request.form.get('path_choice')  

    if path_choice == 'downloads':
        output_path = get_default_download_path()
    elif path_choice == 'desktop':
        output_path = get_default_desktop_path()
    else:
        flash('Invalid path choice. Please select a valid option.', 'danger')
        return redirect(url_for('index'))

    if not os.path.exists(output_path):
        flash(f'The directory {output_path} does not exist.', 'danger')
        return redirect(url_for('index'))

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Download best video and audio
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],  # Add progress hook

    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)  # Change to download=True
            video_title = info_dict.get('title', 'video')
            video_title_sanitized = sanitize_filename(video_title)
            file_ext = info_dict.get('ext', 'mp4')
            output_filename = f"{video_title_sanitized}.{file_ext}"
            output_filepath = os.path.join(output_path, output_filename)

        return send_file(output_filepath, as_attachment=True)  # Send the file for download

    except Exception as e:
        flash(f'Your video has been downloaded, try finding it using the video title', 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
