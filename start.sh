#!/bin/bash

# Jalankan proses data ingestion di awal sebelum server up
python -m app.data.ingest

# Jalankan FastAPI di background pada port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Jalankan Streamlit (panggil ui.py secara langsung)
streamlit run ui.py --server.port $PORT --server.address 0.0.0.0