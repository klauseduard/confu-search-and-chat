# confu-search-and-chat

> **Note (2026):** This is an archived experiment from early 2023. The approach — chunking
> Confluence pages, generating OpenAI embeddings, storing them in Redis, and doing cosine-similarity
> search — was a reasonable DIY take on what is now commonly known as RAG (Retrieval-Augmented
> Generation). Today you'd reach for a framework like LangChain or LlamaIndex with a proper vector
> store instead of hand-rolling this. The code here uses `openai==0.27.4` which predates the
> breaking 1.0 rewrite and will not run against current versions without changes. Kept as-is for
> historical interest.

## What this was

An early experiment in semantic search over on-premise Confluence, built iteratively with the help
of ChatGPT (GPT-3.5 / GPT-4). The goal was to explore what could be accomplished writing and
refactoring bash and Python with LLM assistance.

The pipeline:
1. Download a Confluence page via REST API (`get_confluence_page.sh`)
2. Convert HTML body to plain text (`to_text.py`)
3. Chunk the text, separating code blocks from prose (`preprocess.py`)
4. Generate embeddings via OpenAI and store in Redis (`embeddings.py`)
5. Search by cosine similarity against stored embeddings (`semantic_search.py`)

What was never implemented: the "chat" part — using retrieved chunks as context for an LLM answer.

## Requirements

* Redis (used as a vector store via plain key-value + pickled embeddings)
* `curl`, `jq`
* Python 3 with `pip install -r requirements.txt`

## Configuration

Copy the example config files and fill in your credentials:

* `confluence.example.conf` → `confluence.conf` (username, password, base API URL)
* `openai.example.ini` → `openai.ini` (API key)
* `redis.example.ini` → `redis.ini` (host, port, db — defaults work for local Redis)


