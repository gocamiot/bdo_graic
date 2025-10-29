# vectorize.py

import sys
import json
import numpy as np
from sentence_transformers import SentenceTransformer

# model_name: str = "BAAI/bge-base-en-v1.5",
def get_model(name="BAAI/bge-large-en-v1.5"):
    return SentenceTransformer(name)

def to_sql_vector(text, model=None):
    if model is None:
        model = get_model()
    vec = model.encode([text], normalize_embeddings=True)[0].astype(np.float32)
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vectorize.py \"your text here\"")
        sys.exit(1)

    input_text = sys.argv[1]
    sql_vector = to_sql_vector(input_text)
    print(sql_vector)
