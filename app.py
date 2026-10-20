from flask import Flask, request, redirect, jsonify, abort
import os
import time
import threading

app = Flask(__name__)

LINK_CACHE = {}
REQUEST_QUEUE = []     # Yerel scriptin okuyacağı kuyruk
LOCK = threading.Condition()

# Render panelindeki Environment'tan şifreyi okur
RENDER_SECRET = os.getenv("API_SECRET_KEY", "x9T!sK_2026_secure_token_677")

@app.route('/stream/<channel>')
def stream_redirect(channel):
    # 1. Eğer link zaten hafızadaysa (cache) anında 302 yönlendir
    if channel in LINK_CACHE:
        return redirect(LINK_CACHE[channel]['url'], code=302)
        
    # 2. Link yoksa, bu kanalı yerel scriptin çözmesi için kuyruğa ekle
    with LOCK:
        if channel not in REQUEST_QUEUE:
            REQUEST_QUEUE.append(channel)
        
        # Yerel scriptin linki getirmesi için oynatıcıyı maksimum 15 saniye beklet (Long-Polling)
        locked = LOCK.wait(timeout=15)
        
    # 3. Bekleme süresi bittiğinde link cache'e gelmiş mi kontrol et
    if channel in LINK_CACHE:
        return redirect(LINK_CACHE[channel]['url'], code=302)
    else:
        return abort(504, description="Kanal yayını zaman aşımına uğradı, lütfen tekrar deneyin.")

@app.route('/get-queue', methods=['GET'])
def get_queue():
    auth = request.headers.get('Authorization')
    if auth != RENDER_SECRET:
        return jsonify({"error": "Unauthorized"}), 403
        
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
        
    channel = data['channel']
    url = data['url']
    
    with LOCK:
        LINK_CACHE[channel] = {
            'url': url,
            'time': time.time()
        }
        # Bekleyen (blocking) tüm oynatıcı isteklerini uyandır / serbest bırak
        LOCK.notify_all()
        
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
