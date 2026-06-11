#!/bin/bash

# Jalankan FastAPI di background pada port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Jalankan Streamlit di port yang disediakan oleh Railway (default biasanya diakses langsung oleh user)
streamlit run app/ui.py --server.port $PORT --server.address 0.0.0.0