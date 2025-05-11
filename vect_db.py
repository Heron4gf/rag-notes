from document import Document
from typing import List
import numpy as np
import json
import os
from embedding import get_embedding

# Percorsi
DB_DIR = 'vect_db'
DOC_FOLDER = os.path.join(DB_DIR, "docs")
EMB_FILE = os.path.join(DB_DIR, "embeddings.npy")
INDEX_FILE = os.path.join(DB_DIR, "embeddings_index.json")

os.makedirs(DOC_FOLDER, exist_ok=True)

# =========== Gestione dati su disco ===========

def _load_index():
    if not os.path.exists(INDEX_FILE):
        return {}
    with open(INDEX_FILE, "r") as f:
        return json.load(f)

def _save_index(index):
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f)

def _load_embeddings():
    if not os.path.exists(EMB_FILE):
        return np.zeros((0, 1024), dtype=np.float32)  # 1024 è la dimensione standard bge-m3, aggiorna se necessario
    return np.load(EMB_FILE)

def _save_embeddings(arr):
    np.save(EMB_FILE, arr)

def _embedding_dim():
    # assume almeno un embedding già calcolato oppure default
    embeddings = _load_embeddings()
    if embeddings.shape[0]:
        return embeddings.shape[1]
    # fallback: esempio 1024 (bge-m3 dim), aggiorna se hai un'altra dimensione
    return 1024

# ============ API =============

def add_doc(doc: Document) -> None:
    """
    Salva il documento (come file), calcola e aggiunge il suo embedding nel file globale.
    Se il documento esiste, aggiorna embedding e contenuto.
    """
    # Salva documento testo
    doc_path = os.path.join(DOC_FOLDER, doc.id + '.txt')
    doc.to_file(doc_path)

    # Calcola embedding
    embedding = np.array(get_embedding(doc.content))
    embedding = embedding.reshape(1, -1)  # (1, D)

    # Aggiorna database
    index = _load_index()
    embeddings = _load_embeddings()

    if doc.id in index:
        idx = index[doc.id]
        embeddings[idx] = embedding
    else:
        idx = len(embeddings)
        index[doc.id] = idx
        if embeddings.shape[0] == 0:
            embeddings = embedding
        else:
            embeddings = np.vstack([embeddings, embedding])

    # Scrivi su disco
    _save_index(index)
    _save_embeddings(embeddings)

def delete_doc(doc: Document) -> None:
    """
    Rimuove il documento e il suo embedding.
    """
    # Rimuovi file di testo
    doc_path = os.path.join(DOC_FOLDER, doc.id + '.txt')
    if os.path.exists(doc_path):
        os.remove(doc_path)

    # Aggiorna index/embedding globali
    index = _load_index()
    embeddings = _load_embeddings()

    if doc.id not in index:
        return

    idx = index.pop(doc.id)
    embeddings = np.delete(embeddings, idx, axis=0)
    # Aggiorna indici rimanenti
    for k, v in list(index.items()):
        if v > idx:
            index[k] = v - 1
    _save_index(index)
    _save_embeddings(embeddings)

def update_doc(doc: Document) -> None:
    """
    Aggiorna il contenuto e l'embedding di un documento esistente.
    """
    add_doc(doc)  # stesso comportamento della add_doc

def find_docs(query: str, k: int = 5) -> List[Document]:
    """
    Restituisce i top-k documenti più simili (cosine distance) alla query.
    """
    index = _load_index()
    embeddings = _load_embeddings()
    if not len(index):
        return []

    query_embedding = np.array(get_embedding(query)).reshape(-1)
    doc_ids = sorted(index, key=lambda i: index[i])  # ordinati come array

    # Cosine similarity
    embedding_norms = np.linalg.norm(embeddings, axis=1)
    query_norm = np.linalg.norm(query_embedding)
    sims = embeddings @ query_embedding / (embedding_norms * query_norm + 1e-12)
    best_idx = np.argsort(-sims)[:k]  # ordine decrescente

    # Recupera documenti
    docs = []
    for idx in best_idx:
        if idx >= len(doc_ids):
            continue
        doc_id = doc_ids[idx]
        doc_path = os.path.join(DOC_FOLDER, doc_id + '.txt')
        with open(doc_path, "r") as f:
            content = f.read()
        docs.append(Document(doc_id, content))
    return docs