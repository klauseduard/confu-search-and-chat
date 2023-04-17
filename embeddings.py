#!/usr/bin/env python3
import argparse
import openai
import os
import pickle
import redis
import configparser


# Load OpenAI API credentials and other parameters from the configuration file
config = configparser.ConfigParser()
config.read('openai.ini')
model = config.get('openai', 'model')
api_key = config.get('openai', 'api_key')

config = configparser.ConfigParser()
config.read('redis.ini')
redis_host = config.get('redis', 'host')
redis_port = config.get('redis', 'port')
redis_db = config.get('redis', 'db')


# Function to generate embeddings using the OpenAI API
def generate_embeddings(lines, model, api_key):

    openai.api_key = api_key
    embeddings = []
    metadata = []

    # Process lines in batches
    batch_size = 10  # Adjust this value depending on the rate limits of the OpenAI API
    for i in range(0, len(lines), batch_size):
        batch_lines = lines[i:i + batch_size]

        # Call the OpenAI API for generating embeddings
        try:
            response = openai.Embedding.create(
                input=[line['text'] for line in batch_lines],
                model=model
            )
        except Exception as e:
            for line in batch_lines:
                error_message = f"Error generating embedding: {str(e)}"
                embeddings.append(None)
                metadata.append({
                    'url': line['url'],
                    'line_number': line['line_number'],
                    'error': error_message
                })
        else:
            for idx, embedding_data in enumerate(response['data']):
                embedding = embedding_data['embedding']
                embeddings.append(embedding)
                metadata.append({
                    'url': batch_lines[idx]['url'],
                    'line_number': batch_lines[idx]['line_number']
                })

    return embeddings, metadata

def main(args):
    # Read the input file
    try:
        with open(args.input_file, 'r', encoding='utf-8') as infile:
            lines = [{'text' : line.strip(), 'url': 'confluence.nortal.com', 'line_number': i} for i, line in enumerate(infile)]
    except IOError:
        print(f'Error: Cannot open input file {args.input_file}')
        return

    embeddings, metadata = generate_embeddings(lines, args.model, args.api_key)

    try:
        with open(args.output_file, "wb") as f:
            pickle.dump({'embeddings': embeddings, 'metadata': metadata}, f)
    except IOError:
        print(f'Error: Cannot open output file {args.output_file} for writing')
        return

    # Connect to Redis
    r = redis.Redis(host=args.redis_host, port=args.redis_port, db=args.redis_db)

    # Store embeddings and metadata in Redis
    for embedding, meta in zip(embeddings, metadata):
        key_prefix = f"confluence_embeddings:page_{args.page_id}_line_{meta['line_number']}"
        r.set(f"{key_prefix}_embedding", pickle.dumps(embedding))
        r.set(f"{key_prefix}_metadata", pickle.dumps(meta))

    try:
        with open(args.output_file, "rb") as f:
            data = pickle.load(f)
    except IOError:
        print(f'Error: Cannot open output file {args.output_file} for reading')
        return

    embeddings = data['embeddings']
    metadata = data['metadata']

    # Print the metadata for each embedding
    for embedding, meta in zip(embeddings, metadata):
        if meta.get('error'):
            print(f"Error on line {meta['line_number']}: {meta['error']}")
        else:
            print(f"Embedding for line {meta['line_number']}: {embedding}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed chunks in input file, write embeddings to output file")
    parser.add_argument('input_file', type=str, help="Path to the input text file")
    parser.add_argument('output_file', type=str, help="Path to the output text file")
    parser.add_argument('page_id', type=str, help="Confluence page ID")
    parser.add_argument("--model", default=model, help="OpenAI API model to use for generating embeddings")
    parser.add_argument("--api_key", default=api_key, help="OpenAI API key")
    parser.add_argument("--redis_host", default=redis_host, help="Redis host")
    parser.add_argument("--redis_port", default=redis_port, type=int, help="Redis port")
    parser.add_argument("--redis_db", default=redis_db, type=int, help="Redis database number")

    args = parser.parse_args()

    main(args)




# Save embeddings to a local file using NumPy
#np.save("embeddings.npy", embeddings)
