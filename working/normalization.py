import pandas as pd
import json
from sentence_transformers import SentenceTransformer, util
import numpy as np
import re
from price_calculator import calculate_retail_price
import time

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

def clean_price(value):
    """
    Clean and convert price string to float.
    Removes currency symbols, words, commas.
    """
    if pd.isna(value):
        return None
    if isinstance(value, str):
        # Remove $, commas, words like 'rupees', 'Rs', etc.
        value = re.sub(r'[^\d.]', '', value)  # Keep only digits and dot
    try:
        return float(value)
    except ValueError:
        return None

def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    # Clean and convert price column
    df['price'] = df['price'].apply(clean_price).astype('float64')
    
    # Remove products with price < 1000
    df = df[df['price'] >= 1000]

    # Lowercase name and details for filtering
    df['name'] = df['name'].astype(str)
    df['details'] = df['details'].astype(str)
    name_lower = df['name'].str.lower()
    details_lower = df['details'].str.lower()

    # Keywords indicating non-natural diamonds
    exclusion_keywords = [
        'lab grown', 'lab-created', 'lab created',
        'simulated', 'artificial', 'moissanite', 'man made', 'synthetic'
    ]
    pattern = '|'.join(exclusion_keywords)

    # Filter out non-natural diamond products
    mask = ~(
        name_lower.str.contains(pattern, na=False) |
        details_lower.str.contains(pattern, na=False)
    )
    df = df[mask].copy()

    return df

# Load datasets
kay_df = preprocess_df(pd.read_csv("data/poc_kay.csv"))
glamira_df = preprocess_df(pd.read_csv("data/poc_glamira.csv"))
gemgem_df = preprocess_df(pd.read_csv("data/poc_gemgem.csv"))


# Clean price columns
kay_df['price'] = pd.to_numeric(kay_df['price'], errors='coerce')
glamira_df['price'] = pd.to_numeric(glamira_df['price'], errors='coerce')
gemgem_df['price'] = pd.to_numeric(gemgem_df['price'], errors='coerce')

# Combine competitors
competitor_df = pd.concat([kay_df, glamira_df], ignore_index=True)

# --- Parsing and embedding preparation ---

def parse_details(details_str):
    try:
        return json.loads(details_str.replace("'", '"'))
    except (json.JSONDecodeError, TypeError):
        return {}

def details_to_text(details_dict):
    return ', '.join([f"{k}: {v}" for k, v in details_dict.items()])

# Prepare competitor embeddings
competitor_df['parsed_details'] = competitor_df['details'].apply(parse_details)
competitor_df['embedding_text'] = competitor_df['parsed_details'].apply(details_to_text)
competitor_embeddings = model.encode(competitor_df['embedding_text'].tolist(), convert_to_tensor=True)

# Prepare GemGem embeddings
gemgem_df['parsed_details'] = gemgem_df['details'].apply(parse_details)
gemgem_df['embedding_text'] = gemgem_df['parsed_details'].apply(details_to_text)

# --- Similar price function ---

def get_similar_prices(listing_id: str, top_n: int = 5):
    start_time = time.time()

    gem_row = gemgem_df[gemgem_df['listing_id'] == listing_id]
    if gem_row.empty:
        return {"error": f"No GemGem product found with listing ID {listing_id}"}

    gem_text = gem_row['embedding_text'].values[0]
    gem_price = gem_row['price'].values[0]
    gem_name = gem_row['name'].values[0]

    # Compute similarity
    gem_embedding = model.encode(gem_text, convert_to_tensor=True)
    cos_scores = util.pytorch_cos_sim(gem_embedding, competitor_embeddings)[0]
    top_indices = np.argsort(-cos_scores.cpu().numpy())[:top_n]

    # Get top similar products
    similar = competitor_df.iloc[top_indices].copy()
    similar['similarity_score'] = cos_scores[top_indices].cpu().numpy()
    similar['price'] = pd.to_numeric(similar['price'], errors='coerce')
    avg_similar_price = similar['price'].dropna().mean()

        # Debug: Show similarity scores for all competitors
    all_scores = pd.DataFrame({
        'name': competitor_df['name'],
        'source': competitor_df['url'].apply(lambda x: 'Kay' if 'kay' in x.lower() else 'Glamira'),
        'price': competitor_df['price'],
        'url': competitor_df['url'],
        'similarity_score': cos_scores.cpu().numpy()
    }).sort_values(by='similarity_score', ascending=False)
    print(f"Total rows in all_scores: {len(all_scores)}")

    print("\n--- All Similarity Scores ---")
    print(all_scores[['name', 'source', 'price', 'similarity_score']])
    processing_time = round(time.time() - start_time, 3)

    threshold = 0.05
    matches_above_threshold = (similar['similarity_score'] >= threshold).sum()
    total_competitors = len(competitor_df)
    match_rate = round((matches_above_threshold / total_competitors) * 100, 2)

    return {
        "competitor_df": competitor_df,
        "gemgem_listing_id": listing_id,
        "gemgem_name": gem_name,
        "gemgem_price": gem_price,
        "similar_website_average_price": round(avg_similar_price, 2),
        "similar_products": similar[['name', 'price', 'url', 'similarity_score']].to_dict(orient="records"),
        "processing_time_seconds": processing_time,
        "match_rate": match_rate
    }

# --- Run example ---

if __name__ == "__main__":
    listing_id = "L2025071241181"  # Replace with desired listing_id
    result = get_similar_prices(listing_id)
    retail_price = calculate_retail_price(listing_id, gemgem_df)

    print("\n=== Price Summary ===")
    print(f"GemGem Price: ${result['gemgem_price']}")
    print(f"Competitor Avg Price: ${result['similar_website_average_price']}")
    print(f"Calculated Retail Price (USD): ${retail_price}")
    
