from flask import Flask, render_template, request, flash, redirect, url_for
import yt_dlp
import os
import platform
import time
import re

app = Flask(__name__)
app.secret_key = '1bd8a0bf5cde61924846417da9b121c2'  # Replace with your generated secret key

def get_default_download_path():
    """Returns the default path for downloads based on the OS."""
    if platform.system() == 'Windows':
        return os.path.join(os.getenv('USERPROFILE'), 'Downloads')
    elif platform.system() == 'Darwin':  # macOS
        return os.path.join(os.path.expanduser('~'), 'Downloads')
    else:  # Linux
        return os.path.join(os.path.expanduser('~'), 'Downloads')

def get_default_desktop_path():
    """Returns the default path for the desktop based on the OS."""
    if platform.system() == 'Windows':
        return os.path.join(os.getenv('USERPROFILE'), 'Desktop')
    elif platform.system() == 'Darwin':  # macOS
        return os.path.join(os.path.expanduser('~'), 'Desktop')
    else:  # Linux
        return os.path.join(os.path.expanduser('~'), 'Desktop')

def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    video_url = request.form['video_url']
    path_choice = request.form.get('path_choice')  # Added field for choosing path

    if path_choice == 'downloads':
        output_path = get_default_download_path()
    elif path_choice == 'desktop':
        output_path = get_default_desktop_path()
    else:
        flash('Invalid path choice. Please select a valid option.', 'danger')
        return redirect(url_for('index'))

    # Ensure the output path exists
    if not os.path.exists(output_path):
        flash(f'The directory {output_path} does not exist.', 'danger')
        return redirect(url_for('index'))

    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            video_title = info_dict.get('title', 'video')
            video_title_sanitized = sanitize_filename(video_title)
            file_ext = info_dict.get('ext', 'mp4')
            output_filename = f"{video_title_sanitized}.{file_ext}"
            output_filepath = os.path.join(output_path, output_filename)

            ydl.download([video_url])

            # Update the file's modified time to current time
            os.utime(output_filepath, (time.time(), time.time()))

        flash(f'Video downloaded successfully to {output_path}!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')
