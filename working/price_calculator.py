import requests
import ast
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path

# Load env vars from /poc/.env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# API Setup
API_KEY = os.getenv("METAL_API_KEY")
if not API_KEY:
    raise EnvironmentError("❌ METAL_API_KEY not set in .env file.")

METAL_PRICE_URL = f"https://api.metalpriceapi.com/v1/latest?api_key={API_KEY}&base=USD&symbols=XAU"

def fetch_gold_price_usd_per_gram():
    try:
        response = requests.get(METAL_PRICE_URL)
        data = response.json()
        usd_per_xau = data['rates']['USDXAU']
        usd_per_gram_24k = usd_per_xau / 31.1035
        usd_per_gram_18k = usd_per_gram_24k * 0.75
        return usd_per_gram_18k
    except Exception as e:
        print("❌ Error fetching gold price:", e)
        return 80.0  # fallback price per gram


def extract_weights(details_str):
    try:
        if pd.isna(details_str):
            raise ValueError("Empty details string")

        details = ast.literal_eval(details_str)

        metal_weight = 0.0
        diamond_weight = 0.0
        source_type = "natural"

        # Extract metal info
        if "Specifications" in details and "Item Weight" in details["Specifications"]:
            weight_str = details["Specifications"]["Item Weight"]
            metal_weight = float(weight_str.lower().replace("g", "").strip())

        # Extract diamond info
        if "Stone(s)" in details:
            stone_info = details["Stone(s)"]
            if isinstance(stone_info, dict) and "Carat Weight" in stone_info:
                ctw_str = stone_info["Carat Weight"]
                diamond_weight = float(ctw_str.strip().split(" ")[0])

        if "source" in details:
            source_type = details["source"]

        return {
            "metal_weight": metal_weight,
            "diamond_weight": diamond_weight,
            "diamond_source": source_type
        }
    except Exception as e:
        print("❌ Error parsing weights:", e)
        print("❌ Problematic details string:", details_str)
        return {
            "metal_weight": 0.0,
            "diamond_weight": 0.0,
            "diamond_source": "natural"
        }


def calculate_retail_price(listing_id: str, gemgem_df, making_charge_per_g=20, markup_pct=15):
    row = gemgem_df[gemgem_df['listing_id'] == listing_id]
    if row.empty:
        return 0.0

    price_details = row['details'].values[0]
    weights = extract_weights(price_details)
    metal_weight = weights["metal_weight"]
    diamond_weight = weights["diamond_weight"]
    diamond_source = weights["diamond_source"]

    # Gold price
    gold_price_per_gram = fetch_gold_price_usd_per_gram()

    # Determine gold weight
    if metal_weight > 0:
        gold_weight = metal_weight
    else:
        gold_weight = diamond_weight * 1.5

    gold_cost = gold_weight * gold_price_per_gram
    making_charge = gold_weight * making_charge_per_g

    # Diamond pricing (simple fixed pricing, could be improved)
    if diamond_source.lower() == "lab":
        diamond_price_per_carat = 400
    else:
        diamond_price_per_carat = 1500

    diamond_cost = diamond_weight * diamond_price_per_carat

    # Total base price
    base_price = gold_cost + making_charge + diamond_cost

    # Apply retail markup
    retail_price = base_price * (1 + markup_pct / 100)

    return round(retail_price, 2)
