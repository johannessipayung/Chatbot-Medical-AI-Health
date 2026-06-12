#!/bin/bash
set -e

echo "===================================================="
echo "STARTING MEDICAL AI INTERACTION & RAG EVALUATION"
echo "===================================================="

# Load environment variables dari file .env yang sudah tersedia
if [ -f .env ]; then
    export $(cat .env | xargs)
    echo "✅ Konfigurasi .env berhasil dimuat secara otomatis."
else
    echo "🛑 Error: File .env tidak ditemukan di root directory!"
    exit 1
fi

# echo "👉 Step 1: Menjalankan Data Ingestion & Ekstraksi Vektor FAISS..."
# python -m app.data.ingest

echo "👉 Step 2: Mengeksekusi Kerangka Evaluasi Reproducible Metrics..."
python app/eval.py --with-generation

echo "===================================================="
echo "PROSES EVALUASI BERHASIL DISELESAIKAN!"
echo "===================================================="