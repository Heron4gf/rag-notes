from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)

def get_embedding(text):
    """
    This function takes a text input and returns its embedding.
    """
    embedding = model.encode(text)["dense_vecs"]
    return embedding