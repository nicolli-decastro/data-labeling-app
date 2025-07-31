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

    # df_results = pd.read_csv(output_path)  # load whatever was written
    # df_results.to_csv(config.OUTPUT_CSV, index=False)
    
    print("Run Model completed successfully!")


def main():

    print("Function main called")

    # Where the output file will be placed
    output_filename = config.OUTPUT_CSV

    processed = 0
    
    # Creating output file in the correct place from the output_path
    with open(config.INPUT_CSV, newline='', encoding='utf-8') as inf, \
         open(output_filename, 'w', newline='', encoding='utf-8') as outf:

        reader = csv.DictReader(inf)
        fieldnames = reader.fieldnames + [
            'model_name',
            'reasoning',
            'price_suspicion',
            'item_bulk',
            'item_new',
            'listing_tone',
            'mentions_retailer',
            'overall_likelihood',
            'stolen',
            'timestamp',
            'prompt_tokens',
            'completion_tokens',
            'total_tokens'
        ]
        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        writer.writeheader()

        executor = ThreadPoolExecutor(max_workers=1)

        for row in reader:
            # stop if we've hit the user‑defined limit
            if config.MAX_TO_PROCESS is not None and processed >= config.MAX_TO_PROCESS:
                break

            title     = row.get('title','').strip()
            category  = row.get('category','').strip()
            price     = row.get('price','').strip()
            photo_url = row.get('photo_url','').strip()

            basename = os.path.basename(photo_url)
            search_pattern = os.path.join(config.PHOTO_DIR, '**', basename)
            matches = glob.glob(search_pattern, recursive=True)

            if not matches:
                print(f"[{processed+1}] ⚠️  Skipping—no file for {basename}")
                continue

            img_path = matches[0]  # Use the first match found

            idx        = processed % len(models)
            model      = models[idx]
            model_name = config.VISION_MODELS[idx]

            prompt = build_prompt(title, category, price)
            prompt_tokens = len(encoder.encode(prompt))

            # Compute which key index will be used next
            upcoming_key_idx = api_key_index % num_keys

            # LOGGING: include API‑key index
            print(
                f"[{processed+1}] → Using {model_name} "
                f"(prompt tokens: {prompt_tokens}) "
                f"[API key index: {upcoming_key_idx}]"
            )

            with open(img_path, 'rb') as f:
                img_bytes = f.read()

            # retry with executor‑enforced timeout
            resp = None
            for attempt in range(3):
                future = executor.submit(call_generate, model, img_bytes, prompt)
                try:
                    resp = future.result(timeout=120)
                    break
                except TimeoutError:
                    backoff = 2 ** attempt
                    print(f"    ⏱ Attempt {attempt+1} timed out, retrying in {backoff}s…")
                    time.sleep(backoff)
                except Exception as e:
                    print(f"    ❌ API error on attempt {attempt+1}: {e}")
                    break

            if not resp:
                print("    ❌ All retries failed; skipping this listing.")
                continue

            output = resp.text.strip()
            completion_tokens = len(encoder.encode(output))
            total_tokens      = prompt_tokens + completion_tokens
            print(f"    ✔ Completed. completion: {completion_tokens}, total: {total_tokens}")
            print(f"    ➤ {output.splitlines()[0]}")
            print(f"Delay = {config.DELAY_SECONDS}")

            # parse the response
            reasoning = price_suspicion = item_bulk = item_new = listing_tone = mentions_retailer = overall_likelihood = stolen = timestamp = "N/A"
            for line in output.splitlines():
                low = line.lower()
                if low.startswith("reasoning"):
                    reasoning = line.split(":",1)[1].strip()
                elif low.startswith("price raises suspicion"):
                    price_suspicion = line.split(":",1)[1].strip()
                elif low.startswith("item is bulk"):
                    item_bulk = line.split(":",1)[1].strip()
                elif low.startswith("item is new"):
                    item_new = line.split(":",1)[1].strip()
                elif low.startswith("listing tone"):
                    listing_tone = line.split(":",1)[1].strip()
                elif low.startswith("mentions retailer"):
                    mentions_retailer = line.split(":",1)[1].strip()
                elif low.startswith("overall likelihood shoplifted"):
                    overall_likelihood = line.split(":",1)[1].strip()
                elif low.startswith("stolen"):
                    stolen = line.split(":",1)[1].strip()
                elif low.startswith("timestamp"):
                    timestamp = line.split(":",1)[1].strip()

            # default stolen & timestamp if not provided
            try:
                if overall_likelihood.isdigit():
                    stolen = 'yes' if int(overall_likelihood) >= 7 else 'no'
                timestamp = timestamp if timestamp != "N/A" else time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            except:
                pass

            row.update({
                'model_name':         model_name,
                'reasoning':          reasoning,
                'price_suspicion':    price_suspicion,
                'item_bulk':          item_bulk,
                'item_new':           item_new,
                'listing_tone':       listing_tone,
                'mentions_retailer':  mentions_retailer,
                'overall_likelihood': overall_likelihood,
                'stolen':             stolen,
                'timestamp':          timestamp,
                'prompt_tokens':      prompt_tokens,
                'completion_tokens':  completion_tokens,
                'total_tokens':       total_tokens
            })
            writer.writerow(row)

            processed += 1
            time.sleep(config.DELAY_SECONDS)

        executor.shutdown()

    print(f"\n✅ Done! Processed {processed} listings. Output → {output_filename}")

if __name__ == "__main__":
    main()
