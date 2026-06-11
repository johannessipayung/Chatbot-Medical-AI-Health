FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HAPUS ATAU HILANGKAN BARIS DI BAWAH INI:
# RUN python -m app.data.ingest

RUN chmod +x start.sh
CMD ["./start.sh"]