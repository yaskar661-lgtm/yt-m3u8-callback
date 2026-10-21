import yt_dlp
import time
import random
import re
import os
import json
import requests
from flask import Flask, request, redirect, abort, jsonify

app = Flask(__name__)

# ============= CONFIGURATION =============
GITHUB_RAW_URL = "https://github.com/yaskar661-lgtm/yt-cookies/raw/refs/heads/main/cookies.txt"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
RENDER_SECRET = os.getenv("API_SECRET_KEY", "")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def download_cookies_securely():
    """Render her açıldığında gizli GitHub reposundan cookies.txt dosyasını hatasız çeker"""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        print("🔒 Gizli repodan güncel çerezler indiriliyor...")
        response = requests.get(GITHUB_RAW_URL, headers=headers, allow_redirects=True, timeout=15)
        if response.status_code == 200:
            with open("cookies.txt", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("✅ Çerezler başarıyla güncellendi.")
            return True
        else:
            print(f"⚠️ Çerez indirilemedi, HTTP Kodu: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Çerez indirme hatası: {e}")
    return False

# Uygulama ayağa kalkarken çerezleri indir
download_cookies_securely()

def detect_channel_country(channel_name):
    """Kanal adına göre basit ülke/geo-bypass tespiti"""
    c_lower = channel_name.lower()
    if any(k in c_lower for k in ['nigeria', 'lagos', 'abuja', 'naija', 'tvc news', 'channels television', 'arise news']):
        return 'NG'
    if any(k in c_lower for k in ['ghana', 'accra', 'joy fm', 'adom', 'tv3', 'utv']):
        return 'MX'
    return 'UK'

def get_m3u8_from_json(youtube_url, cookies_file="cookies.txt"):
    """yt_dlp Python API ve geo-bypass ayarları ile yayını analiz eder, manifest yakalar."""
    try:
        # Önce hızlıca kanal adını öğrenip ülke belirleyelim
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'cookies': cookies_file if os.path.exists(cookies_file) else None}) as ydl:
            info_basic = ydl.extract_info(youtube_url, download=False, process=False)
            channel_name = info_basic.get('channel', '') if info_basic else ''
        
        country = detect_channel_country(channel_name)

        ydl_opts = {
            'cookies': cookies_file if os.path.exists(cookies_file) else None,
            'quiet': True,
            'no_warnings': True,
            'dump_single_json': True,
            'socket_timeout': 25,
            'geo_bypass': True,
            'geo_bypass_country': country,
            'xff': country,
            'headers': {
                'X-Forwarded-For': f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
                'Accept-Language': f'en-{country},en;q=0.9',
                'Origin': 'https://www.youtube.com',
                'Referer': 'https://www.youtube.com/',
                'User-Agent': USER_AGENT
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios'],
                    'live_from_start': True,
                    'skip': ['webpage', 'configs']
                }
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            if not info:
                return None

            manifest = info.get("manifest_url")
            if manifest and ".m3u8" in manifest:
                return manifest

            manifest_pattern = r'https://manifest\.googlevideo\.com/api/manifest/hls_variant[^\s\"\\]+'
            formats = info.get("formats", [])
            for f in reversed(formats):
                url = f.get("url", "")
                proto = f.get("protocol", "")
                ext = f.get("ext", "")
                
                match_f = re.search(manifest_pattern, url)
                if match_f:
                    return match_f.group(0).replace(r'\u0026', '&').replace('\\/', '/')
                    
                if proto == "m3u8_native" or ext == "m3u8" or ".m3u8" in url:
                    return url
    except Exception as e:
        print(f"  ⚠️ Manifest Çözümleme Hatası: {e}")
    return None

def build_target_url(channel_input):
    """Girdi türüne göre nokta atışı YouTube canlı yayın URL'si üretir"""
    channel_input = channel_input.strip()
    if channel_input.startswith("UC") and len(channel_input) >= 20:
        return f"https://www.youtube.com/channel/{channel_input}/live"
    elif len(channel_input) == 11 and " " not in channel_input:
        return f"https://www.youtube.com/watch?v={channel_input}"
    else:
        handle = channel_input if channel_input.startswith("@") else f"@{channel_input}"
        return f"https://www.youtube.com/{handle}/live"

# ============= FLASK ENDPOINTS =============
@app.route('/stream/<channel>')
def stream_redirect(channel):
    target_url = build_target_url(channel)
    print(f"📺 Talep geldi: {channel} -> Hedef URL: {target_url}")
    
    stream_url = get_m3u8_from_json(target_url)
    
    if stream_url:
        return redirect(stream_url, code=302)
    else:
        return abort(404, description="Kanal şu anda canlı değil veya akış adresi çözülemedi.")

@app.route('/refresh-cookies', methods=['GET'])
def refresh_cookies():
    auth = request.headers.get('Authorization')
    if auth != RENDER_SECRET:
        return jsonify({"error": "Unauthorized"}), 403
    
    success = download_cookies_securely()
    if success:
        return jsonify({"status": "success", "message": "Cookies refreshed successfully!"})
    return jsonify({"status": "error", "message": "Failed to fetch cookies."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
