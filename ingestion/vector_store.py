"""
Vector Store
------------
Embeds chunks using Amazon Bedrock Titan and saves to FAISS.
Also builds a BM25 index for hybrid search.
"""

import os
import pickle
from pathlib import Path

import boto3
from dotenv import load_dotenv
from langchain.schema import Document
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

load_dotenv()

def get_embeddings():
    client = boto3.client(
        "bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
    return BedrockEmbeddings(
        client=client,
        model_id=os.getenv("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0"),
    )

def build_and_save_index(documents: list[Document], index_path: str) -> FAISS:
    print(f"Embedding {len(documents)} chunks with Bedrock Titan...")
    embeddings = get_embeddings()

    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(index_path)
    print(f"  FAISS index saved → {index_path}")

    bm25 = BM25Retriever.from_documents(documents, k=5)
    bm25_path = index_path + "_bm25.pkl"
    with open(bm25_path, "wb") as f:
        pickle.dump(bm25, f)
    print(f"  BM25 index saved → {bm25_path}")

    return vectorstore

def load_hybrid_retriever(index_path: str, k: int = 6) -> EnsembleRetriever:
    embeddings = get_embeddings()

    vectorstore = FAISS.load_local(
        index_path,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": k})

    bm25_path = index_path + "_bm25.pkl"
    with open(bm25_path, "rb") as f:
        bm25_retriever = pickle.load(f)
    bm25_retriever.k = k

    return EnsembleRetriever(
        retrievers=[faiss_retriever, bm25_retriever],
        weights=[0.6, 0.4],
    )