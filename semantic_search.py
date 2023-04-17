#!/usr/bin/env python3

"""
This script performs semantic search on Confluence pages using OpenAI's
Embeddings API. It calculates cosine similarity between the input query and
existing page embeddings stored in Redis to find similar pages.
"""

import redis
import numpy as np
import json
import pickle
import argparse
import re
import httpx
import sys
import unicodedata
import configparser

config = configparser.ConfigParser()
config.read('redis.ini')
REDIS_HOST = config.get('redis', 'host')
REDIS_PORT = config.getint('redis', 'port')
REDIS_DB = config.getint('redis', 'db')

config = configparser.ConfigParser()
config.read('openai.ini')
EMBEDDINGS_MODEL = config.get('openai', 'model')
API_KEY = config.get('openai', 'api_key')


def connect_to_redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB):
    return redis.Redis(host=host, port=port, db=db)


def normalize_quotes(text):
    quote_mapping = {
        "‘": "'", "’": "'", "“": '"', "”": '"'
    }
    return "".join(quote_mapping.get(c, c) for c in text)


def preprocess_query(query):
    """Preprocesses the query string for generating embeddings."""
    query = unicodedata.normalize('NFC', query)
    query = normalize_quotes(query)
    query_string = query.strip()
    query_string = re.sub(r"\s+", " ", query_string)
    return query_string


def normalize_embeddings(embeddings):
    return embeddings / np.linalg.norm(embeddings)


def get_embeddings(redis_client, page_id):
    key = f'confluence_embeddings:{page_id}'
    embeddings_data = redis_client.get(key)
    if embeddings_data is None:
        return None
    try:
        embedding = pickle.loads(embeddings_data)
        return normalize_embeddings(np.array(embedding))
    except (pickle.UnpicklingError, AttributeError, EOFError, ImportError, IndexError) as e:
        print(f"Warning: Failed to load pickled embeddings for key {key}. Error: {str(e)}. Skipping.", file=sys.stderr)
        return None


def cosine_similarity(a, b):
    return np.dot(a, b)
    

def search_similar_pages(query_embeddings, page_ids, redis_client, threshold=0.5):
    similar_pages = []
    for page_id in page_ids:
        page_embeddings = get_embeddings(redis_client, page_id)
        if page_embeddings is not None:
            similarity = cosine_similarity(query_embeddings, page_embeddings)
            if similarity >= threshold:
                similar_pages.append((page_id, similarity))
    similar_pages.sort(key=lambda x: x[1], reverse=True)
    return similar_pages


def get_all_page_ids(redis_client, pattern='confluence_embeddings:*_embedding'):
    keys = redis_client.keys(pattern)
    page_ids = [key.decode('utf-8').split(':')[1] for key in keys]
    return page_ids
    
    
async def get_openai_embeddings(text, api_key):
    async with httpx.AsyncClient() as client:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        data = {
            "model": EMBEDDINGS_MODEL,
            "input": [text]
        }
        response = await client.post('https://api.openai.com/v1/embeddings', headers=headers, json=data)
        response.raise_for_status()
        return normalize_embeddings(np.array(response.json()['data'][0]['embedding']))


async def main(input_string, api_key):
    try:
        preprocessed_input = preprocess_query(input_string)
        query_embeddings = await get_openai_embeddings(preprocessed_input, api_key)

        with connect_to_redis() as redis_client:
            page_ids = get_all_page_ids(redis_client)
            threshold = 0.5
            similar_pages = search_similar_pages(query_embeddings, page_ids, redis_client, threshold)

        for page_id, similarity in similar_pages:
            print(f'Page ID: {page_id}, Similarity: {similarity:.8f}')
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform semantic search with OpenAI Embeddings API")
    parser.add_argument('input_string', type=str, help="The input string to search for similar Confluence pages")
    parser.add_argument("--api_key", default=API_KEY, help="OpenAI API key")
    args = parser.parse_args()

    input_string = args.input_string
    api_key = args.api_key

    import asyncio
    asyncio.run(main(input_string, api_key))        
