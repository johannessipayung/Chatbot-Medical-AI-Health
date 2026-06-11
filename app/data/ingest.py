import os
import re
import pickle
import faiss
import numpy as np
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from app.config.settings import settings


print(f"Memuat model embedding: {settings.EMBEDDING_MODEL}...")
embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)

def clean_text(text: str) -> str:
    """Fungsi untuk melakukan Text Normalization (Pembersihan Data)"""
    if not text:
        return ""
    text = text.replace("jdih.kemkes.go.id", "")
    text = re.sub(r'-\s*\d+\s*-', '', text)
    text = " ".join(text.split())
    return text

if __name__ == '__main__':
    texts = []
    metadatas = []
    PDF_DIR = "data/pdfs"
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    if not os.path.exists(PDF_DIR):
        print(f"Folder direktori {PDF_DIR} tidak ditemukan!")
        exit(1)

    print("Memulai proses Data Preparation & Ingestion...")
    
    for file in os.listdir(PDF_DIR):
        if file.endswith(".pdf"):
            path = os.path.join(PDF_DIR, file)
            print(f"Memproses file: {file}")
            
            loader = PyPDFLoader(path)
            pages = loader.load()
            
            for page_idx, page_doc in enumerate(pages):
                actual_page = page_doc.metadata.get("page", page_idx) + 1
                
                raw_content = page_doc.page_content
                
                cleaned_content = clean_text(raw_content)
                
                if not cleaned_content.strip():
                    continue
                
                chunks = splitter.split_text(cleaned_content)
                
                for chunk_text in chunks:
                    texts.append(chunk_text)
                    
                    year_match = re.search(r'(20\d{2})', file)
                    doc_year = int(year_match.group(1)) if year_match else None
                    
                    authority = "KEMENKES" if "MENKES" in file.upper() or "KEPMENKES" in file.upper() else "WHO"
                    
                    metadatas.append({
                        "source": file,
                        "page": actual_page,      
                        "year": doc_year,        
                        "authority": authority   
                    })

    print(f"\nEkstraksi selesai! Total chunks bersih di database: {len(texts)}")

    print("Memulai ekstraksi embedding vektor...")
    embeddings = embedding_model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True
    )

    # Inisialisasi FAISS IndexFlatL2
    print("Menyimpan indeks ke dalam Vectorstore lokal...")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    os.makedirs("vectorstore", exist_ok=True)
    
    faiss.write_index(index, "vectorstore/faiss.index")

    with open("vectorstore/texts.pkl", "wb") as f:
        pickle.dump(texts, f)

    with open("vectorstore/metadatas.pkl", "wb") as f:
        pickle.dump(metadatas, f)

    print("Datastore berhasil diperbarui dengan struktur bagus!")