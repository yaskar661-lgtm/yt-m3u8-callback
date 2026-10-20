from flask import Flask, request, redirect, jsonify, abort
import os
import time

app = Flask(__name__)

LINK_CACHE = {}
REQUEST_QUEUE = []  # Oynatıcıdan anlık istenen kanalların kuyruğu
RENDER_SECRET = os.getenv("API_SECRET_KEY", "gizli_sifreniz")

@app.route('/stream/<channel>')
def stream_redirect(channel):
    # 1. Eğer link cache'te varsa direkt YouTube'a 302 yönlendir
    if channel in LINK_CACHE:
        return redirect(LINK_CACHE[channel]['url'], code=302)
        
    # 2. Cache'te yoksa bu kanalı anlık çözümleme kuyruğuna ekle
    if channel not in REQUEST_QUEUE:
        REQUEST_QUEUE.append(channel)
        
    return "Kanal araniyor, lutfen 5 saniye sonra tekrar oynat tusuna basin...", 503

@app.route('/get-queue', methods=['GET'])
def get_queue():
    auth = request.headers.get('Authorization')
    if auth != RENDER_SECRET:
        return jsonify({"error": "Unauthorized"}), 403
        
    # Yerel script sorduğunda kuyruktaki ilk kanalı ver
    if REQUEST_QUEUE:
        channel = REQUEST_QUEUE.pop(0)
        return jsonify({"channel": channel})
    return jsonify({"channel": None})

@app.route('/update', methods=['POST'])
def update_link():
    auth = request.headers.get('Authorization')
    if auth != RENDER_SECRET:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.json
    if not data or 'channel' not in data or 'url' not in data:
        return jsonify({"error": "Eksik veri"}), 400
        
    LINK_CACHE[data['channel']] = {
        'url': data['url'],
        'time': time.time()
    }
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
