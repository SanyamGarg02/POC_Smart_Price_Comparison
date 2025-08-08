from fastapi import FastAPI
from fastapi.responses import FileResponse
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from normalization import get_similar_prices
from price_calculator import calculate_retail_price
import pandas as pd
import uuid
import os
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env vars from ../.env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Use env var for CSV path
GEMGEM_CSV_PATH = os.getenv("GEMGEM_CSV_PATH")
if not GEMGEM_CSV_PATH or not os.path.exists(GEMGEM_CSV_PATH):
    raise FileNotFoundError(f"GEMGEM_CSV_PATH not found: {GEMGEM_CSV_PATH}")

# Load data
gemgem_df = pd.read_csv(GEMGEM_CSV_PATH)

app = FastAPI()

@app.get("/pricing-chart/{listing_id}")
def generate_chart(listing_id: str):
    # Get GEMGEM price
    row = gemgem_df[gemgem_df["listing_id"] == listing_id]
    if row.empty:
        return {"error": "Listing not found"}

    gemgem_price = row["price"].values[0]

    # Retail price
    retail_price = calculate_retail_price(listing_id, gemgem_df)
    price_info = get_similar_prices(listing_id)
    competitor_price = price_info['similar_website_average_price']

    # Create chart
    labels = ["Retail Price", "GEMGEM Price", "Other Platforms"]
    values = [retail_price, gemgem_price, competitor_price]
    colors = ["#d4a5a5", "#3cb371", "#d4a5a5"]

    plt.figure(figsize=(6, 5))
    plt.bar(labels, values, color=colors)
    plt.ylabel("Price (USD)")
    plt.title("Smart Pricing Comparison")

    # Save chart
    chart_filename = f"{uuid.uuid4()}.png"
    chart_path = f"/tmp/{chart_filename}"
    plt.savefig(chart_path)
    plt.close()

    return FileResponse(chart_path, media_type="image/png", filename="chart.png")

