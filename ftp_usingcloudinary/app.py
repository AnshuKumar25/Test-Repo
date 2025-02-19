from flask import Flask, redirect, url_for, session, request, send_from_directory, jsonify, render_template, flash, Response
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management
app.config['SESSION_COOKIE_NAME'] = 'your_session_cookie'

# Configure Cloudinary
cloudinary.config(
    cloud_name="dmxipfjqf",
    api_key="887655257278688",
    api_secret="yHwuc_7lVWEQf58NyZcpBoSuVWY"
)

# Folder paths
UPLOAD_FOLDER = 'server_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
LOG_FILE = 'download_log.txt'

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123"

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Handle Admin Login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True  # Set session
            flash("Login Successful", "success")
            return redirect(url_for('upload_page'))
        else:
            flash("Invalid Credentials", "danger")

    return render_template('admin_login.html')

@app.route('/admin-logout')
def admin_logout():
    """Log out the admin"""
    session.pop('admin', None)
    flash("Logged Out Successfully", "info")
    return redirect(url_for('index'))

@app.route('/upload-page')
def upload_page():
    """Render the upload page only if admin is logged in."""
    if 'admin' not in session:
        flash("Please log in as Admin to upload files", "warning")
        return redirect(url_for('admin_login'))
    
    return render_template('upload_page.html')

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     """Upload file to Cloudinary and return the public URL."""
#     if 'admin' not in session:
#         return jsonify({"error": "Unauthorized"}), 403

#     if 'file' not in request.files:
#         return jsonify({"error": "No file uploaded"}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400

#     # Upload file to Cloudinary
#     response = cloudinary.uploader.upload(file)
#     file_url = response["secure_url"]

#     flash("File uploaded successfully!", "success")
#     return jsonify({"message": "File uploaded successfully", "url": file_url})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'admin' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Upload as "raw" to allow any file type
    result = cloudinary.uploader.upload(file, resource_type="raw")

    return jsonify({
        "message": "File uploaded successfully",
        "file_url": result["secure_url"]  # Get the direct URL for public access
    })

@app.route('/download-page')
def download_page():
    """Render the download page."""
    return render_template('download_page.html')
                           
@app.route('/files', methods=['GET'])
def list_files():
    """List all files stored in Cloudinary."""
    files = cloudinary.api.resources(type="upload", max_results=50)
    file_list = [{"name": file["public_id"], "url": file["secure_url"]} for file in files.get("resources", [])]
    
    return jsonify(file_list)

@app.route('/download/<filename>')
def download_file(filename):
    """Get the public Cloudinary URL of a file."""
    # Get all uploaded files from Cloudinary
    response = cloudinary.api.resources(resource_type="raw")

    # Extract file URLs and names
    # files = [{"name": file["public_id"], "url": file["secure_url"]} for file in response["resources"]]

    # return render_template('download_.html', files=files)
    # try:
    file_info = cloudinary.api.resource(filename)
    file_url = f"https://res.cloudinary.com/dmxipfjqf/raw/upload/{filename}"
    
    # Fetch the file from Cloudinary
    response = requests.get(file_url, stream=True)

    # Extract filename
    filename = filename.split("/")[-1]

    # Serve the file directly as a response with appropriate headers
    return Response(
        response.iter_content(chunk_size=8192),
        content_type=response.headers["Content-Type"],
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": response.headers["Content-Length"]
        }
    )

    # Log the download (exclude microseconds)
    with open(LOG_FILE, 'a') as log:
        log.write(f"{filename} downloaded on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    #     return jsonify({"message": "File is available for download", "url": file_url})
    # except cloudinary.exceptions.NotFound:
    #     return jsonify({"error": "File not found"}), 404

@app.route('/view-log-page')
def view_log_page():
    """Render the view log page."""
    if 'admin' not in session:
        flash("Please log in as Admin to view logs", "warning")
        return redirect(url_for('admin_login'))

    return render_template('view_log_page.html')

@app.route('/download-log', methods=['GET'])
def download_log():
    """Provide the download log entries in JSON format."""
    if not os.path.exists(LOG_FILE):
        return jsonify([])  # Return empty list if no log file exists

    logs = []
    with open(LOG_FILE, 'r') as log:
        for line in log:
            parts = line.strip().split(' downloaded on ')
            if len(parts) == 2:
                filename, timestamp = parts
                logs.append({"filename": filename, "timestamp": timestamp})

    return jsonify(logs)

@app.route('/download-success/<filename>', methods=['POST'])
def download_success(filename):
    """Log the download and show a success message."""
    with open(LOG_FILE, 'a') as log:
        log.write(f"{filename} downloaded on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    return jsonify({"message": "Download logged successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
