#!/usr/bin/env python3

import argparse
import json
import re
import sys
import unicodedata

class Token:
    def __init__(self, text, token_type):
        self.text = text
        self.token_type = token_type

class TokenType:
    TEXT = "TEXT"
    CODE_BLOCK = "CODE_BLOCK"

class Parser:
    def __init__(self, text):
        self.text = text
        self.index = 0

    def parse(self):
        tokens = []
        while self.index < len(self.text):
            if self.text[self.index:self.index+3] == "```":
                self.index += 3
                code_block_text = self.parse_code_block()
                tokens.append(Token(code_block_text, TokenType.CODE_BLOCK))
            else:
                text = self.parse_text()
                tokens.append(Token(text, TokenType.TEXT))
        return tokens

    def parse_text(self):
        start_index = self.index
        while self.index < len(self.text) and self.text[self.index:self.index+3] != "```":
            self.index += 1
        return self.text[start_index:self.index]

    def parse_code_block(self):
        start_index = self.index
        while self.index < len(self.text) and self.text[self.index:self.index+3] != "```":
            self.index += 1
        if self.index >= len(self.text):
            raise Exception("Unterminated code block.")
        self.index += 3
        return self.text[start_index:self.index-3]

def get_arguments():
    parser = argparse.ArgumentParser(description='Preprocess text for generating embeddings.')
    parser.add_argument('input_file', type=str, help='path to input file')
    parser.add_argument('output_file', type=str, help='path to output file')
    parser.add_argument('--chunk_size', type=int, default=2048, help='maximum chunk size')
    return parser.parse_args()

def get_tokens(text):
    parser = Parser(text)
    return parser.parse()


def get_chunks(tokens, chunk_size):
    chunks = []
    current_chunk = ""
    start_indexes = []
    end_indexes = []
    current_start_index = 0
    for token in tokens:
        if token.token_type == TokenType.CODE_BLOCK:
            if current_chunk:
                chunks.append(current_chunk)
                start_indexes.append(current_start_index)
                current_start_index += len(current_chunk)
                end_indexes.append(current_start_index-1)
                current_chunk = ""
            start_indexes.append(current_start_index)
            chunks.append(token.text)
            current_start_index += len(token.text)
            end_indexes.append(current_start_index-1)
        else:
            if len(current_chunk) + len(token.text) > chunk_size:
                chunks.append(current_chunk)
                start_indexes.append(current_start_index)
                current_start_index += len(current_chunk)
                end_indexes.append(current_start_index-1)
                current_chunk = ""
            current_chunk += token.text
    if current_chunk:
        chunks.append(current_chunk)
        start_indexes.append(current_start_index)
        current_start_index += len(current_chunk)
        end_indexes.append(current_start_index-1)
    return chunks, start_indexes, end_indexes


def normalize_quotes(text):
    quote_mapping = {
        "‘": "'", "’": "'", "“": '"', "”": '"'
    }
    return "".join(quote_mapping.get(c, c) for c in text)


def preprocess(text, chunk_size):
    """Preprocesses the input text for generating embeddings."""
    # Normalize Unicode characters
    text = unicodedata.normalize('NFC', text)

    # Normalize quotes
    text = normalize_quotes(text)

    # Tokenize input text
    tokens = get_tokens(text)

    # Split tokens into chunks of size CHUNK_SIZE
    chunks, start_indexes, end_indexes = get_chunks(tokens, chunk_size)

    # Remove leading/trailing whitespace and replace consecutive whitespace with a single space
    cleaned_chunks = []
    for chunk in chunks:
        stripped_chunk = chunk.strip()
        cleaned_chunk = re.sub(r"\s+", " ", stripped_chunk)
        cleaned_chunks.append(cleaned_chunk)
    return cleaned_chunks, start_indexes, end_indexes


if __name__ == "__main__":
    try:
        args = get_arguments()
        with open(args.input_file, "r", encoding="utf-8") as input_file:
            text = input_file.read()
            chunks, start_indexes, end_indexes = preprocess(text, args.chunk_size)
        with open(args.output_file, "w", encoding="utf-8") as output_file:
            for chunk in chunks:
                output_file.write(chunk + "\n") # Add newline character between chunks
        with open(args.output_file + ".metadata", "w", encoding="utf-8") as metadata_file:
            for i in range(len(chunks)):
                metadata_file.write(f"{start_indexes[i]},{end_indexes[i]}\n")
    except FileNotFoundError as e:
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

