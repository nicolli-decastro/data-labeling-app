# config.py
# -----------
# Configuration settings for the labeling pipeline.
# Place this file in the same directory as `labelMachine.py`
# and import via:
#
#   import config
#   # then access e.g. config.API_KEYS, config.INPUT_CSV, etc.

# === Gemini API settings ===

import streamlit as st

API_KEYS = st.secrets.get("API_KEYS", [])  

# List of vision‑enabled models to cycle through
VISION_MODELS = [
    "gemma-3-27b-it",
    # add more models here if desired
]

# The number that is multiplied to the number of API keys should be the TPM of the model you are using divided by the average token usage!

if len(API_KEYS) == 0:
    raise ValueError("🚨 No API keys found in `st.secrets['api_keys']`. Please add at least one.")
else:
    DELAY_SECONDS = 60 / (15 * len(API_KEYS))

# **Maximum number of listings to process.**
# Set to an integer limit (e.g. 100) or to None to process all rows.
MAX_TO_PROCESS = None

# === Tokenizer settings ===
TOKENIZER_NAME = "gpt2"

# === Elimination filter keywords (for benchmarking) ===
FILTER_KEYWORDS = ["ryobi", "kobalt", "dewalt"]

# === Title‑based thresholds (for quick heuristics) ===
MIN_TITLE_WORDS = 3
MAX_TITLE_WORDS = 20

# === Price pattern checks (for quick elimination) ===
PRICE_SYMBOL = "$"

# === Prompt template ===
PROMPT_TEMPLATE = """
You are acting as a Loss Prevention Specialist. It is your job to evaluate a Facebook Marketplace listing to determine its level of suspicion across several categories.
For the actual listing, you will be provided both an image AND text, however for the examples I provide, you will only have textual analysis.

I am going to provide you chain of thought reasoning through example listings to enhance your reasoning skills for the actual listing I provide you.

First, here are two examples that walk you through how to evaluate listings based off of text:

Fill out the rubric for each item from 1-10. 1 means the listing is almost certainly not suspicious for shoplifting. 10 means the listing is almost certainly shoplifted. 

Listing: “Unopened bulk power tools – Cheap!!”, Tools, $25 

A: Reasoning: The listing is much cheaper than it should be at market price, is unopened, and is an often-shoplifted category. 

Price raises suspicion: 10 

Item is bulk: 10 
Item is new: 9 

Listing tone (urgency): 7 

Item mentions retailer by name: 1 

Overall likelihood shoplifted: 8 

Listing: “Heavily used vintage keyboard”, Electronics, $30 

A: Reasoning: The listing is heavily used, opened, and reasonable at market price. The word “vintage” suggests shoplifting is unlikely. 

Price raises suspicion: 3 

Item is bulk: 1 
Item is new: 1 

Listing tone (urgency): 1 

Item mentions retailer by name: 1 

Overall likelihood shoplifted: 2 

Classify the rubric that the listing below is shoplifted or not shoplifted. Follow the format of the examples provided. 

Listing: "Brand New iPhone 15 Pro Max - Sealed Box!", Electronics, $400 

A:  

Reasoning: The listing is for a high-value item that is significantly underpriced compared to the market. It is sealed, which suggests it could have been stolen in bulk. Expensive electronics, especially iPhones, are frequently targeted by shoplifters. 

Price raises suspicion: 10 
Item is bulk: 7 
Item is new: 10 
Listing tone (urgency): 6 
Item mentions retailer by name: 2 
Overall likelihood shoplifted: 9 

Answer in the exact format demonstrated.

You MUST include REASONING THAT REFERENCES THE IMAGE you have been provided.

The following is the listing you will evaluate:

Below is a photo of the item AND its listing details. Use both to evaluate.

Listing Title: {title}
Category: {category}
Price: {price}

First, describe any visual red flags you see in the photo (e.g. store labels, multiple items, background context).
Then fill out the rubric (1–10 scale; 1 = almost certainly not shoplifted, 10 = almost certainly shoplifted):

1. Price raises suspicion  
2. Item is bulk  
3. Item is new  
4. Listing tone (urgency language)  
5. Mentions retailer by name  
6. Overall likelihood shoplifted

If Overall likelihood shoplifted ≥ 7, set `stolen: yes`; otherwise `stolen: no`.
Finally, include `timestamp` in UTC ISO8601 format.

Answer in this exact format:

Reasoning (visual+text): <analysis>
Price raises suspicion: <1–10>
Item is bulk: <1–10>
Item is new: <1–10>
Listing tone: <1–10>
Mentions retailer: <1–10>
Overall likelihood shoplifted: <1–10>
stolen: <yes/no>
timestamp: <YYYY-MM-DDThh:mm:ssZ>
"""

