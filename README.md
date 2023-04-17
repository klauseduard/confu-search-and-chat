# confu-search-and-chat

## Intro
Wannabe semantic search and chat experiment on top of on-premise Confluence installation.

Please note that I'm not publishing the full pipeline before I'm relatively satisfied with it.

I am publishing parts of it because I intend to use it as an example of what can be accomplished
writing and refactoring code (well, bash and python) with the help of chatGPT (or certain OpenAI
APIs).

Currently available:
* download and preprocess (break into chunks) of a Confluence page,
* create embeddings with chunks prefixed by page title
* store pickled embeddings and metadata in Redis
* semantic search returning relevant Redis keys

Currently not available:
* the chat or search summary or whatever
* niceties like page title and url in search results
* exagerations like the chunk sequence number in search results
* time to implement these simple things 


## Requirements 

I will document the requirements later but for now:
* You need Redis -- to be used as vector database.
* You need curl and whatever utilities the remaining shell scripts require.
* You need pip and possibly install a couple of python libraries required by various scripts.

## Configuration

copy confluence.example.conf to confluence.conf, define your api key and a url

copy openai.example.ini to openai.ini and modify it (api key only I guess)

copy redis.example.ini to redis.ini and modify it if you really need to

