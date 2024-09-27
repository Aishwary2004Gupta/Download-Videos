from flask import Flask, render_template, request, flash, redirect, url_for, send_file
import yt_dlp
import os
import platform
import re

app = Flask(__name__)
app.secret_key = '1bd8a0bf5cde61924846417da9b121c2'

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
    video_url = request.form['video_url']
    path_choice = request.form.get('path_choice')

    # Select the output path based on user choice
    if path_choice == 'downloads':
        output_path = get_default_download_path()
    elif path_choice == 'desktop':
        output_path = get_default_desktop_path()
    else:
        flash('Invalid path choice. Please select a valid option.', 'danger')
        return redirect(url_for('index'))

    # Check if output path exists
    if not os.path.exists(output_path):
        flash(f'The directory {output_path} does not exist.', 'danger')
        return redirect(url_for('index'))

    # Set yt-dlp options to download best video and audio, merged into one file
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Best video and audio format
        'merge_output_format': 'mp4',  # Ensure the output is a merged MP4 file
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),  # Define output template
        'progress_hooks': [progress_hook],  # Hook to monitor progress (optional)
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',  # Use FFmpeg to convert/merge video and audio
            'preferedformat': 'mp4',  # Preferred format is MP4
        }]
    }

    try:
        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)  # Download the video
            video_title = info_dict.get('title', 'video')
            video_title_sanitized = sanitize_filename(video_title)
            file_ext = info_dict.get('ext', 'mp4')
            output_filename = f"{video_title_sanitized}.{file_ext}"
            output_filepath = os.path.join(output_path, output_filename)

        # Serve the file for download
        return send_file(output_filepath, as_attachment=True)

    except yt_dlp.DownloadError as e:
        flash(f"Download error: {str(e)}", 'danger')
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
