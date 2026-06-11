FROM python:3.11-slim

WORKDIR /app

# Instal dependensi sistem yang dibutuhkan untuk FAISS / C++ compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Jalankan skrip ingest secara otomatis saat build agar pangkalan data FAISS siap digunakan
RUN python -m app.data.ingest

# Jalankan skrip start up (kita akan buat berkas start.sh di bawah)
RUN chmod +x start.sh
CMD ["./start.sh"]