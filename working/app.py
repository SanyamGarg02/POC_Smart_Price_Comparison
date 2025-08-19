from fastapi import FastAPI
from fastapi.responses import FileResponse
import pandas as pd
import uuid
import time
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # Prevent GUI windows from opening in FastAPI
import matplotlib.pyplot as plt
from normalization import get_similar_prices
from price_calculator import calculate_retail_price

# Load datasets
gemgem_df = pd.read_csv("data/poc_gemgem.csv")

app = FastAPI()


@app.get("/pricing-chart/{listing_id}")
def generate_chart(listing_id: str):
    start_time = time.time()  # Start performance timer

    try:
        # Get GEMGEM price
        row = gemgem_df[gemgem_df["listing_id"] == listing_id]
        if row.empty:
            return {"error": "Listing not found"}

        gemgem_price = row["price"].values[0]

        # Retail price
        retail_price = calculate_retail_price(listing_id, gemgem_df)

        # Competitor price
        price_info = get_similar_prices(listing_id)
        competitor_price = price_info["similar_website_average_price"]

        # Savings Calculations
        competitor_savings = competitor_price - gemgem_price
        competitor_savings_percent = (competitor_savings / competitor_price) * 100 if competitor_price else 0

        retail_savings = retail_price - gemgem_price
        retail_savings_percent = (retail_savings / retail_price) * 100 if retail_price else 0

        # Save results for analysis
        processing_time = round(time.time() - start_time, 3)  # seconds
        results_row = {
            "listing_id": listing_id,
            "retail_price": retail_price,
            "gemgem_price": gemgem_price,
            "competitor_price": competitor_price,
            "competitor_savings": competitor_savings,
            "competitor_savings_percent": competitor_savings_percent,
            "retail_savings": retail_savings,
            "retail_savings_percent": retail_savings_percent,
            "match_rate": price_info.get("match_rate", None),  # From normalization.py
            "processing_time_sec": processing_time
        }

        csv_path = Path("poc_test_results.csv")
        if csv_path.exists():
            df_existing = pd.read_csv(csv_path)
            df_existing = pd.concat([df_existing, pd.DataFrame([results_row])], ignore_index=True)
            df_existing.to_csv(csv_path, index=False)
        else:
            pd.DataFrame([results_row]).to_csv(csv_path, index=False)

        # Create chart
        labels = ["Retail Price", "GEMGEM Price", "Other Platforms"]
        values = [retail_price, gemgem_price, competitor_price]
        colors = ["#d4a5a5", "#3cb371", "#d4a5a5"]

        plt.figure(figsize=(6, 5))
        bars = plt.bar(labels, values, color=colors)
        plt.ylabel("Price (USD)")
        plt.title("Smart Pricing Comparison & Savings")

        # Annotate prices on top of bars
        for bar, val in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, val, f"${val:,.2f}",
                     ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Add savings info as a note below chart
        savings_text = (
            f"Savings vs Competitors: ${competitor_savings:,.2f} ({competitor_savings_percent:.1f}%)\n"
            f"Savings vs Retail: ${retail_savings:,.2f} ({retail_savings_percent:.1f}%)"
        )
        plt.gcf().text(0.5, -0.15, savings_text, ha='center', fontsize=9)

        plt.tight_layout()

        # Save chart
        chart_filename = f"{uuid.uuid4()}.png"
        chart_path = f"/tmp/{chart_filename}"
        plt.savefig(chart_path, bbox_inches="tight")
        plt.close()

        return FileResponse(chart_path, media_type="image/png", filename="chart.png")

    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"{listing_id} - {str(e)}\n")
        return {"error": str(e)}
