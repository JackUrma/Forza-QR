import os
import re
import subprocess
from datetime import datetime
from flask import Flask, request, render_template, send_from_directory, jsonify
import qrcode

app = Flask(__name__)
BASE_DIR = "saved_videos"
os.makedirs(BASE_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    vid = request.files.get('video')
    if not vid:
        app.logger.error("No file part in request")
        return jsonify({"error": "No video file received"}), 400
    now = datetime.now()
    filename = f"video_{now.strftime('%Y-%m-%d_%H-%M-%S')}.webm"
    save_path = os.path.join(BASE_DIR, filename)
    vid.save(save_path)
    size = os.path.getsize(save_path)
    app.logger.info(f"Saved upload → {filename} ({size} bytes)")
    return jsonify({"filename": filename, "size": size}), 200

@app.route('/saved_videos/<filename>')
def download(filename):
    return send_from_directory(BASE_DIR, filename, as_attachment=True)

def start_cloudflare_tunnel():
    exe_name = "cloudflared.exe"
    exe_path = os.path.join(os.path.dirname(__file__), exe_name)
    cmd = [exe_path, "tunnel", "--url", "http://localhost:5000", "--no-autoupdate"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    public_url = None
    url_pattern = re.compile(r"(https://[^\s]+\.trycloudflare\.com)")
    for line in proc.stdout:
        m = url_pattern.search(line)
        if m:
            public_url = m.group(1)
            break
    if not public_url:
        proc.kill()
        raise RuntimeError("Could not detect Cloudflare Tunnel URL.")
    return proc, public_url

if __name__ == "__main__":
    tunnel_proc, public_url = start_cloudflare_tunnel()
    qrcode.make(public_url).save("qr_code.png")
    print(f"\n🔗 Recorder is live at: {public_url}")
    print("📷 QR code saved to qr_code.png\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
