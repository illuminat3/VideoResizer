import os
from flask import Flask, render_template, request, send_from_directory, jsonify
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "static/outputs"
ALLOWED_EXTENSIONS = {"mp4"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            output_filepath = os.path.join(app.config["OUTPUT_FOLDER"], "resized_" + filename)

            command = [
                "ffmpeg", "-i", filepath,
                "-vf", "scale=1920:1080",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-strict", "experimental",
                "-movflags", "+faststart",
                output_filepath
            ]
            subprocess.run(command, check=True)

            return jsonify({"filename": "resized_" + filename}), 200

    return render_template("index.html")

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(app.config["OUTPUT_FOLDER"], filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    response = send_from_directory(app.config["OUTPUT_FOLDER"], filename, as_attachment=True)

    @response.call_on_close
    def cleanup():
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

    return response

if __name__ == "__main__":
    app.run(debug=True)
