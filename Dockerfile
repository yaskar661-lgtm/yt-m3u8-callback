# Resmi hafif Python imajını kullanıyoruz
FROM python:3.10-slim

# Çalışma dizinini /app olarak belirliyoruz
WORKDIR /app

# Gerekli sistem bağımlılıklarının kurulması (yt-dlp ve ağ işlemleri için)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt dosyasını konteynere kopyalıyoruz
COPY requirements.txt .

# Python kütüphanelerini yüklüyoruz (yt-dlp dahil)
RUN pip install --no-cache-dir -r requirements.txt

# Projedeki tüm dosyaları (app.py vb.) konteynere kopyalıyoruz
COPY . .

# Render'ın dinamik port atamasını destekleyecek şekilde Gunicorn ile başlatıyoruz
CMD gunicorn --bind 0.0.0.0:$PORT app:app
