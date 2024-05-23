# Langchain-TPB
A langchain python project that connects to ThePirateBay and SubHD to find best video source and traditional chinese subtitle. Optionally downloads them using aria2 RPC and chrome download.

# Requirements
1. GroqCloud API key: https://console.groq.com/keys
2. Self hosted aria2 server and RPC
3. Python3

# Install
1. `$ git clone langchain-tpb && cd langchain-tpb`
2. `$ python3 -m venv venv`
3. `$ source venv/bin/activate`
4. `$ pip install -r requirements.txt`
5. Apply secrets to env variables, by either
   1. `$ cp secrets-template.sh secrets.sh`, then edit `secrets.sh`, then `$ source secrets.sh`
   2. or prepend `GROQ_API_KEY=XXX ARIA2_RPC_URL=YYY ARIA2_RPC_SECRET=ZZZ` at every python command

# Search for video and sub
`$ python3 search.py` then enter movie name in input. For example, "Frozen 2013". After `search-result.json` is dumped, proceed to download.

# Download video and sub
`$ python3 download.py`. Your Aria2 RPC will be called and the magnet link will be added as a job, then optionally complete subHD captcha.
