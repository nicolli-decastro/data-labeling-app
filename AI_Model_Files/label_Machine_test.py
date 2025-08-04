#!/usr/bin/env python3
import os
import csv
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import tiktoken
import google.generativeai as genai
import AI_Model_Files.config as config
import pandas as pd
import glob

# === INITIALIZE API‑KEY ROTATION & TOKENIZER ===
api_key_index = 0
num_keys = len(config.API_KEYS)

# Seed SDK with first key
first_key = config.API_KEYS[api_key_index % num_keys]
genai.configure(api_key=first_key)
api_key_index += 1

# Prepare tokenizer
encoder = tiktoken.get_encoding(config.TOKENIZER_NAME)

# Pre‑instantiate vision‑enabled models
models = [genai.GenerativeModel(model_name=m) for m in config.VISION_MODELS]

def has_correct_header(csv_path, expected_columns):
    try:
        df = pd.read_csv(csv_path, nrows=0)  # Only reads the header
        current_columns = list(df.columns)
        return current_columns == expected_columns
    except Exception as e:
        print(f"⚠️ Error reading file: {e}")
        return False

def build_prompt(title, category, price):
    """Fill in the prompt template from config."""
    return config.PROMPT_TEMPLATE.format(
        title=title,
        category=category,
        price=price
    )

def call_generate(model, img_bytes, prompt):
    """
    Select the next API key by index, reconfigure the SDK, then call.
    """
    global api_key_index
    key_idx = api_key_index % num_keys
    key = config.API_KEYS[key_idx]
    genai.configure(api_key=key)
    api_key_index += 1

    return model.generate_content(
        contents=[
            {"mime_type": "image/jpeg", "data": img_bytes},
            {"text": prompt}
        ]
    )

def run_model(input_csv: str, image_folder: str, output_path: str, max_to_process: int = None):
    config.INPUT_CSV = input_csv
    config.PHOTO_DIR = image_folder
    config.OUTPUT_CSV = output_path
    config.MAX_TO_PROCESS = max_to_process

    print("Function main being called")
    main()  # run main function
    
    print("Run Model completed successfully!")

def main():
    print("Function main called and starting")

    output_filename = config.OUTPUT_CSV
    input_filename = config.INPUT_CSV
    print("Reading from:", output_filename)

    # Load input CSV
    df_input = pd.read_csv(input_filename)

    # Checks if CSV output exists
    file_exists = os.path.exists(output_filename)

    # Header with all columns (input + extras)
    all_columns = list(df_input.columns) + [
    'model_name', 'reasoning', 'price_suspicion', 'item_bulk', 'item_new',
    'listing_tone', 'mentions_retailer', 'overall_likelihood', 'stolen',
    'timestamp', 'prompt_tokens', 'completion_tokens', 'total_tokens']

    # Check if header is correct, otherwise recreate it
    if not file_exists or not has_correct_header(output_filename, all_columns):
        # Ensure output CSV has correct header if it doesn't exist or the header is incorrect
        print("🛠 Building output file with correct header.")
        pd.DataFrame(columns=all_columns).to_csv(output_filename, index=False)

    # Load output CSVs
    df_output = pd.read_csv(output_filename)

    # Use listing_url to avoid reprocessing
    processed_ids = set(df_output['listing_url']) if not df_output.empty else set()
    df_to_process = df_input[~df_input['listing_url'].isin(processed_ids)].copy()

    print(f"🔁 Skipping {len(processed_ids)} already-labeled rows. {len(df_to_process)} remaining.")

    processed_rows = 0
    executor = ThreadPoolExecutor(max_workers=1)

    for idx, row in df_to_process.iterrows():
        if config.MAX_TO_PROCESS is not None and processed_rows >= config.MAX_TO_PROCESS:
            break

        title     = row.get('title', '').strip()
        category  = row.get('category', '').strip()
        price     = str(row.get('price', '')).strip()
        photo_url = row.get('photo_url', '').strip()

        basename = os.path.basename(photo_url)
        search_pattern = os.path.join(config.PHOTO_DIR, '**', basename)
        matches = glob.glob(search_pattern, recursive=True)

        if not matches:
            print(f"[{processed_rows+1}] ⚠️  Skipping—no file for {basename}")
            continue

        img_path = matches[0]  # Use the first match found
        idx = processed_rows % len(models)
        model = models[idx]
        model_name = config.VISION_MODELS[idx]
        prompt = build_prompt(title, category, price)
        prompt_tokens = len(encoder.encode(prompt))

        # Compute which key index will be used next
        upcoming_key_idx = api_key_index % num_keys

        # LOGGING: include API‑key index
        print(
            f"[{processed_rows+1}] → Using {model_name} "
            f"(prompt tokens: {prompt_tokens}) "
            f"[API key index: {upcoming_key_idx}]"
        )

        with open(img_path, 'rb') as f:
            img_bytes = f.read()

        # API call with timeout retry
        resp = None
        for attempt in range(3):
            future = executor.submit(call_generate, model, img_bytes, prompt)
            try:
                resp = future.result(timeout=120)
                break
            except TimeoutError:
                backoff = 2 ** attempt
                print(f"    ⏱ Timeout {attempt+1}, retrying in {backoff}s…")
                time.sleep(backoff)
            except Exception as e:
                print(f"    ❌ API error attempt {attempt+1}: {e}")
                break

        if not resp:
            print("    ❌ All retries failed; skipping this listing.")
            continue

        output = resp.text.strip()
        completion_tokens = len(encoder.encode(output))
        total_tokens = prompt_tokens + completion_tokens
        print(f"    ✔ Completed. completion: {completion_tokens}, total: {total_tokens}")
        print(f"    ➤ {output.splitlines()[0]}")

        # Parse LLM response
        extras = {
            'model_name': model_name,
            'reasoning': "N/A",
            'price_suspicion': "N/A",
            'item_bulk': "N/A",
            'item_new': "N/A",
            'listing_tone': "N/A",
            'mentions_retailer': "N/A",
            'overall_likelihood': "N/A",
            'stolen': "N/A",
            'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens
        }

        for line in output.splitlines():
            low = line.lower()
            if low.startswith("reasoning"):
                extras['reasoning'] = line.split(":", 1)[1].strip()
            elif low.startswith("price raises suspicion"):
                extras['price_suspicion'] = line.split(":", 1)[1].strip()
            elif low.startswith("item is bulk"):
                extras['item_bulk'] = line.split(":", 1)[1].strip()
            elif low.startswith("item is new"):
                extras['item_new'] = line.split(":", 1)[1].strip()
            elif low.startswith("listing tone"):
                extras['listing_tone'] = line.split(":", 1)[1].strip()
            elif low.startswith("mentions retailer"):
                extras['mentions_retailer'] = line.split(":", 1)[1].strip()
            elif low.startswith("overall likelihood shoplifted"):
                extras['overall_likelihood'] = line.split(":", 1)[1].strip()
            elif low.startswith("stolen"):
                extras['stolen'] = line.split(":", 1)[1].strip()
            elif low.startswith("timestamp"):
                extras['timestamp'] = line.split(":", 1)[1].strip()

        if extras['overall_likelihood'].isdigit():
            extras['stolen'] = 'yes' if int(extras['overall_likelihood']) >= 7 else 'no'

        # Merge row data with model output
        full_row = row.to_dict()
        full_row.update(extras)

        # Append single row to CSV
        pd.DataFrame([full_row]).to_csv(output_filename, mode='a', index=False, header=False)
        processed_rows += 1

        time.sleep(config.DELAY_SECONDS)

    executor.shutdown()

    print(f"\n✅ Done! Processed {processed_rows} listings. Output → {output_filename}")

if __name__ == "__main__":
    main()
