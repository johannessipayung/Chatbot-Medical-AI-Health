FROM python:3.11-slim

WORKDIR /app

# Instal dependensi sistem dan alat dos2unix
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Paksa konversi file start.sh ke format Linux secara internal
RUN dos2unix start.sh

RUN chmod +x start.sh
CMD ["./start.sh"]