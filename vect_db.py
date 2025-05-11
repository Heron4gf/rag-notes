from document import Document
from typing import List
import numpy as np
import json
import os
from embedding import get_embedding
import logging

DB_DIR = 'vect_db'
DOC_FOLDER = os.path.join(DB_DIR, "docs")
EMB_FILE = os.path.join(DB_DIR, "embeddings.npy")
INDEX_FILE = os.path.join(DB_DIR, "embeddings_index.json")

os.makedirs(DOC_FOLDER, exist_ok=True)

def _load_index():
    if not os.path.exists(INDEX_FILE):
        return {}
    try:
        with open(INDEX_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.warning(f"Failed to decode JSON from {INDEX_FILE}. Returning empty index.")
        return {}

def _save_index(index):
    with open(INDEX_FILE, "w", encoding='utf-8') as f:
        json.dump(index, f)

def _load_embeddings():
    if not os.path.exists(EMB_FILE):
        return np.zeros((0, 1024), dtype=np.float32) 
    try:
        return np.load(EMB_FILE)
    except ValueError: 
        logging.warning(f"Failed to load embeddings from {EMB_FILE}. File might be corrupted. Re-initializing.")
        if os.path.exists(EMB_FILE):
            try:
                os.remove(EMB_FILE)
            except OSError as e:
                logging.error(f"Could not remove corrupted embeddings file {EMB_FILE}: {e}")
        if os.path.exists(INDEX_FILE):
            try:
                os.remove(INDEX_FILE)
                logging.info(f"Removed index file {INDEX_FILE} due to embedding corruption.")
            except OSError as e:
                logging.error(f"Could not remove index file {INDEX_FILE}: {e}")
        return np.zeros((0, 1024), dtype=np.float32)

def _save_embeddings(arr):
    np.save(EMB_FILE, arr)

def add_doc(doc: Document) -> None:
    doc_path = os.path.join(DOC_FOLDER, doc.id + '.txt')
    doc.to_file(doc_path)
    embedding = np.array(get_embedding(doc.content))
    embedding = embedding.reshape(1, -1)
    index = _load_index()
    embeddings = _load_embeddings()
    if doc.id in index:
        idx = index[doc.id]
        if idx < len(embeddings):
            embeddings[idx] = embedding
        else: 
            logging.warning(f"Index for doc ID {doc.id} was out of bounds. Re-adding.")
            index.pop(doc.id) 
            idx = embeddings.shape[0] 
            index[doc.id] = idx
            if embeddings.shape[0] == 0 and embedding.shape[0] > 0 :
                 embeddings = embedding
            elif embedding.shape[0] > 0 :
                 embeddings = np.vstack([embeddings, embedding])
    else:
        idx = embeddings.shape[0] 
        index[doc.id] = idx
        if embeddings.shape[0] == 0 and embedding.shape[0] > 0:
             embeddings = embedding
        elif embedding.shape[0] > 0 :
             embeddings = np.vstack([embeddings, embedding])
    _save_index(index)
    if embeddings.shape[0] > 0:
        _save_embeddings(embeddings)

def delete_doc(doc_to_delete: Document) -> None:
    doc_path = os.path.join(DOC_FOLDER, doc_to_delete.id + '.txt')
    if os.path.exists(doc_path):
        try:
            os.remove(doc_path)
        except OSError as e:
            logging.error(f"Error removing document file {doc_path}: {e}")
    index = _load_index()
    embeddings = _load_embeddings()
    if doc_to_delete.id not in index:
        return
    idx_to_delete = index.pop(doc_to_delete.id)
    if idx_to_delete < embeddings.shape[0]:
        embeddings = np.delete(embeddings, idx_to_delete, axis=0)
        new_index = {}
        for k_val, v_val in index.items(): # Renamed k,v to avoid conflict
            if v_val > idx_to_delete:
                new_index[k_val] = v_val - 1
            else:
                new_index[k_val] = v_val
        _save_index(new_index)
    else: 
        logging.warning(f"Index for deleted doc ID {doc_to_delete.id} was out of bounds of embeddings array. Saving modified index only.")
        _save_index(index)
    if embeddings.shape[0] > 0:
        _save_embeddings(embeddings)
    elif os.path.exists(EMB_FILE):
        try:
            os.remove(EMB_FILE)
        except OSError as e:
            logging.error(f"Error removing empty embeddings file {EMB_FILE}: {e}")

def update_doc(doc: Document) -> None:
    add_doc(doc)

def find_docs(query: str, k: int = 5, min_similarity_threshold: float = 0.0) -> List[Document]:
    index = _load_index()
    embeddings = _load_embeddings()
    
    if not query.strip() and k > 0: 
        all_doc_ids = list(index.keys())
        docs_to_return = []
        for doc_id in all_doc_ids[:k]: 
            doc_path = os.path.join(DOC_FOLDER, doc_id + '.txt')
            if os.path.exists(doc_path):
                 try:
                    with open(doc_path, "r", encoding='utf-8') as f:
                        content = f.read()
                    docs_to_return.append(Document(doc_id, content))
                 except Exception as e:
                    logging.error(f"Error reading document {doc_path} in find_docs (empty query): {e}")
        return docs_to_return

    if not index or embeddings.shape[0] == 0:
        return []

    try:
        query_embedding = np.array(get_embedding(query)).reshape(-1)
    except Exception as e:
        logging.error(f"Error getting embedding for query '{query[:50]}...': {e}")
        return []
    
    sorted_index_items = sorted(index.items(), key=lambda item: item[1])
    
    aligned_doc_ids_map = {emb_idx_val: doc_id for doc_id, emb_idx_val in sorted_index_items if emb_idx_val < embeddings.shape[0]}
    valid_embedding_indices = sorted(aligned_doc_ids_map.keys())

    if not valid_embedding_indices:
        return []
        
    relevant_embeddings = embeddings[valid_embedding_indices, :]

    if relevant_embeddings.shape[0] == 0: return []

    embedding_norms = np.linalg.norm(relevant_embeddings, axis=1)
    query_norm = np.linalg.norm(query_embedding)
    
    denominator = embedding_norms * query_norm
    sims_for_relevant = np.zeros(relevant_embeddings.shape[0])

    valid_mask = denominator > 1e-9 # Check for non-zero denominator
    if np.any(valid_mask):
      sims_for_relevant[valid_mask] = (relevant_embeddings[valid_mask] @ query_embedding) / denominator[valid_mask]
    
    # Get original indices in the full `embeddings` array, sorted by similarity
    # argsort sorts in ascending, so use negative sims for descending
    num_possible_results = relevant_embeddings.shape[0]
    # These are indices within `relevant_embeddings`
    sorted_indices_in_relevant = np.argsort(-sims_for_relevant) 

    docs = []
    
    # Always include the first result if available and k >= 1
    if k >= 1 and num_possible_results > 0:
        top_relevant_idx = sorted_indices_in_relevant[0]
        original_emb_idx = valid_embedding_indices[top_relevant_idx] # map back to original index
        doc_id = aligned_doc_ids_map[original_emb_idx]
        doc_path = os.path.join(DOC_FOLDER, doc_id + '.txt')
        if os.path.exists(doc_path):
            try:
                with open(doc_path, "r", encoding='utf-8') as f:
                    content = f.read()
                docs.append(Document(doc_id, content))
            except Exception as e:
                logging.error(f"Error reading document {doc_path} for top search result: {e}")

    # Add other results if they meet the threshold and k > 1
    if k > 1 and num_possible_results > 1:
        # Start from the second potential result
        for i in range(1, min(k, num_possible_results)): 
            relevant_idx = sorted_indices_in_relevant[i]
            current_score = sims_for_relevant[relevant_idx]

            if current_score >= min_similarity_threshold:
                original_emb_idx = valid_embedding_indices[relevant_idx]
                doc_id = aligned_doc_ids_map[original_emb_idx]
                doc_path = os.path.join(DOC_FOLDER, doc_id + '.txt')
                if os.path.exists(doc_path):
                    try:
                        with open(doc_path, "r", encoding='utf-8') as f:
                            content = f.read()
                        docs.append(Document(doc_id, content))
                    except Exception as e:
                        logging.error(f"Error reading document {doc_path} for subsequent search result: {e}")
            else:
                # Since results are sorted by similarity, if one doesn't meet threshold, subsequent ones won't either
                break 
    return docs