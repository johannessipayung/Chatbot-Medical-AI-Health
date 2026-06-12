# ⚕️ Medical AI Chatbot Assistant 

Aplikasi Medical AI Chatbot Assistant yang saya kembangkan secara modular menggunakan **LangGraph (State Machine)**, **CrewAI (Multi-Agent Systems)**, dan **Hybrid Retrieval (FAISS Dense + BM25 Sparse + Cross-Encoder Reranker)**. Sistem ini saya rancang khusus untuk memenuhi standar regulasi klinis kedokteran nasional dan global dengan implementasi keamanan tingkat lanjut.


---

## 🛠️ Arsitektur & Alur Sistem (System Design)

Sistem memproses input pengguna melalui alur grafik terarah state machine berbasis `LangGraph` untuk menjamin keamanan penanganan kondisi medis sebelum berinteraksi dengan LLM utama.

1. **Guardrail + PII Layer:** Input dibersihkan dari PII, diuji secara deterministik terhadap prompt injection/leetspeak/rot13, dan dievaluasi risikonya (Urgent Triage).
2. **Hybrid Retrieval Layer:** Jika aman, kueri diproses paralel menggunakan FAISS (Dense Search) dan Rank-BM25 (Sparse Search), kemudian diurutkan ulang menggunakan `bge-reranker-base`.
3. **Multi-Agent Generation (CrewAI):** 4 Agen Medis Spesialis (Analyst, Evidence Reviewer, Safety Validator, dan Communicator) berkolaborasi menyusun jawaban final berdasarkan konteks regulasi klinis yang valid tanpa halusinasi.

---

## 📊 Kerangka Evaluasi Otomatis (Reproducible Evaluation Script)

Saya menyediakan skrip pengujian otomatis yang independen untuk mereproduksi dan memvalidasi seluruh hasil metrik pencarian (*retrieval quality*) dan pembuatan jawaban (*generation quality*).

### 🎯 Metrik Utama yang Diukur:
* **NDCG@5 & MRR:** Mengukur ketepatan peringkat dokumen medis yang ditarik. Dalam domain medis, pedoman klinis yang paling relevan wajib berada di peringkat teratas demi keselamatan diagnosis.
* **Recall@5:** Memastikan dokumen pedoman yang dibutuhkan tidak terlewatkan.
* **Medical Evaluation Metrics (LLM-as-a-Judge):** Menilai akurasi faktual, tingkat keselamatan medis (*safety score*), dan kualitas sitasi secara otomatis.
* **Average Cost per Query:** Penghitungan estimasi biaya aktual tokenisasi secara *real-time*.

# Evaluation Guide

Proyek ini menyediakan beberapa mode evaluasi untuk mengukur performa sistem Medical AI Assistant, mulai dari kualitas retrieval hingga evaluasi komprehensif menggunakan pendekatan **LLM-as-a-Judge**.

---

## Option 1: Standard Evaluation (Retrieval + Generation)

Mode ini digunakan untuk mengevaluasi performa retrieval dan generation tanpa menggunakan evaluator berbasis LLM.

### Evaluasi yang Dilakukan

- Hybrid Retrieval Performance
- BM25 Retrieval Performance
- Dense Retrieval (FAISS) Performance
- Citation Coverage
- Token Usage Estimation
- Cost Estimation

### Menjalankan Evaluasi

```bash
python app/eval.py
```

### Kapan Digunakan?

Gunakan mode ini untuk:

- Benchmark dasar sistem RAG
- Mengukur kualitas retrieval
- Memeriksa penggunaan token dan estimasi biaya
- Evaluasi cepat tanpa biaya tambahan evaluator LLM

---

## Option 2: Comprehensive Evaluation (LLM-as-a-Judge)

Mode evaluasi paling lengkap yang memanfaatkan agen evaluator berbasis LLM untuk melakukan penilaian kualitas jawaban secara otomatis.

### Evaluasi yang Dilakukan

Selain seluruh metrik pada evaluasi standar, mode ini juga menghitung:

- Factual Accuracy
- Medical Safety Score
- Hallucination Detection
- Response Quality Assessment
- Expected Calibration Error (ECE)
- Reliability & Trustworthiness Metrics

### Menjalankan Evaluasi

Menggunakan skrip otomatisasi:

```bash
bash run_eval.sh
```


Atau secara langsung:

```bash
python app/eval.py --with-judge
```

### Kapan Digunakan?

Mode ini direkomendasikan untuk:

- Validasi sebelum deployment
- Evaluasi keselamatan medis
- Pengukuran akurasi faktual
- Analisis kalibrasi model
- Penelitian dan publikasi akademik

> **Note:** Mode ini membutuhkan token tambahan karena menggunakan model evaluator berbasis LLM.

---

## Option 3: Retrieval-Only Evaluation

Mode ini hanya mengevaluasi kualitas sistem pencarian dokumen tanpa melakukan proses generasi jawaban.

### Evaluasi yang Dilakukan

- BM25 Retrieval Metrics
- Dense Retrieval Metrics
- Hybrid Retrieval Metrics
- Recall@K
- Precision@K
- Ranking Quality

### Menjalankan Evaluasi

```bash
python app/eval.py --retrieval-only
```

### Kapan Digunakan?

Gunakan mode ini ketika:

- Mengoptimalkan indeks FAISS
- Menyetel parameter BM25
- Menguji strategi hybrid retrieval
- Ingin menghemat penggunaan token LLM
- Fokus pada kualitas pencarian dokumen

---

## Summary

| Mode | Command | Generation | LLM Judge | Cost |
|--------|---------|------------|------------|--------|
| Standard Evaluation | `python app/eval.py` | ✅ | ❌ | Low |
| Comprehensive Evaluation | `python app/eval.py --with-judge` | ✅ | ✅ | High |
| Retrieval-Only Evaluation | `python app/eval.py --retrieval-only` | ❌ | ❌ | Very Low |

## Recommended Workflow

1. Jalankan **Retrieval-Only Evaluation** saat melakukan optimasi indeks.
2. Jalankan **Standard Evaluation** untuk pengujian rutin.
3. Jalankan **Comprehensive Evaluation** sebelum deployment atau publikasi hasil penelitian.

### 🚀 Panduan Eksekusi Evaluasi Langsung di Terminal (Zero-Chmod / Plug-and-Play)

Karena seluruh konfigurasi API Key dan Environment Variables **sudah saya sediakan secara instan di dalam repositori**, pengujian dapat langsung dijalankan di terminal tanpa perlu melakukan konfigurasi file `.env` manual tambahan maupun mengubah izin eksekusi berkas (`chmod`).

#### 1. Clone Repositori & Install Dependensi
```bash
git clone <url-repo>
cd Chatbot-Medical-AI-Health
pip install -r requirements.txt

