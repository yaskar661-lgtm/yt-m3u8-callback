# Resmi hafif Python imajını kullan
FROM python:3.10-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Önce gereksinimler dosyasını kopyala ve kütüphaneleri yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tüm proje dosyalarını kopyala
COPY . .

# Render'ın dinamik port atamasını destekleyecek şekilde Gunicorn ile başlat
CMD gunicorn --bind 0.0.0.0:$PORT app:app
