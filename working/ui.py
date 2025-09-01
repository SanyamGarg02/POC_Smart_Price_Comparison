import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
import numpy as np

from price_calculator import calculate_retail_price
from normalization import get_similar_prices, preprocess_df

st.subheader("📈 System Flow Overview")
st.graphviz_chart("""
digraph {
    node [shape=rect, style=filled, color=black, fontcolor=white]

    input [label="User Input:\nGemGem Listing ID", shape=ellipse, fillcolor="#4e79a7"]

    fetch [label="Fetch Product Details\nfrom GemGem Dataset", shape=box, fillcolor="#f28e2b", fontcolor="black"]
    retail [label="Calculate Retail Price\n(Gold API + Diamond + Making Charges + Markup)", shape=box, fillcolor="#f28e2b", fontcolor="black"]
    competitors [label="Find Similar Competitor\nProducts (Embeddings)", shape=box, fillcolor="#f28e2b", fontcolor="black"]
    avg [label="Retrieve Competitor Prices\n& Compute Average", shape=box, fillcolor="#f28e2b", fontcolor="black"]
    chart [label="Generate Price\nComparison Chart", shape=box, fillcolor="#f28e2b", fontcolor="black"]

    out1 [label="GemGem Price vs Competitor Avg vs Retail Estimate", shape=ellipse, fillcolor="#76b7b2", fontcolor="black"]
    out2 [label="Savings + Savings %", shape=ellipse, fillcolor="#76b7b2", fontcolor="black"]
    out3 [label="Match Rate & Processing Time", shape=ellipse, fillcolor="#76b7b2", fontcolor="black"]

    input -> fetch
    fetch -> retail
    fetch -> competitors
    competitors -> avg
    retail -> chart
    avg -> chart
    chart -> out1 -> out2 -> out3
}
""")

# Load datasets
gemgem_df = pd.read_csv("data/poc_gemgem.csv")
kay_df = preprocess_df(pd.read_csv("data/poc_kay.csv"))
glamira_df = preprocess_df(pd.read_csv("data/poc_glamira.csv"))

# Merge into one dataframe
competitor_df = pd.concat([kay_df, glamira_df], ignore_index=True)

st.set_page_config(page_title="Jewelry Price Comparison POC", layout="centered")
st.title("💎 Jewelry Price Comparison Tool (POC)")

# Input Listing ID
listing_id = st.text_input("Enter GemGem Listing ID:", "")

if listing_id:
    # Fetch product
    product_row = gemgem_df[gemgem_df["listing_id"] == listing_id]
    if product_row.empty:
        st.error("❌ Listing ID not found in dataset.")
    else:
        st.subheader("📌 Product Details")
        st.write(product_row[["name", "details"]].iloc[0])

        # Get similar competitor products
        st.subheader("🔍 Similar Competitor Products")
        similar_products = get_similar_prices(listing_id, top_n=5)

        if "similar_products" not in similar_products or not similar_products["similar_products"]:
            st.warning("⚠️ No similar products found for this listing.")
        else:
            st.success(f"Found {len(similar_products['similar_products'])} similar products!")

            # Prices
            gemgem_price = float(product_row["price"].iloc[0])
            competitor_avg_price = float(
                pd.DataFrame(similar_products["similar_products"])["price"].mean()
            )

            retail_data = calculate_retail_price(listing_id, gemgem_df)
            retail_estimate = float(retail_data["retail_price"])

            savings = competitor_avg_price - gemgem_price
            savings_pct = (savings / competitor_avg_price * 100) if competitor_avg_price > 0 else 0

            # ---- NEW FEATURE: Log JSON if GemGem price > competitor avg ----
            if gemgem_price > competitor_avg_price:
                def convert(o):
                    if isinstance(o, (np.int64, np.int32)):
                        return int(o)
                    if isinstance(o, (np.float64, np.float32)):
                        return float(o)
                    return str(o)

                log_data = {
                    "gemgem_listing_id": str(listing_id),
                    "gemgem_price": float(gemgem_price),
                    "competitor_avg_price": float(competitor_avg_price),
                    "similar_products": [
                        {k: convert(v) for k, v in product.items()}
                        for product in similar_products["similar_products"]
                    ]
                }

                os.makedirs("logs", exist_ok=True)
                with open("logs/price_mismatch_log.json", "a") as f:
                    f.write(json.dumps(log_data) + "\n")

                st.error("⚠️ GemGem price is higher than competitor average!")
                st.subheader("📋 Logged Competitor Prices for Review")
                df_log = pd.DataFrame(log_data["similar_products"])
                st.dataframe(df_log)
            # ----------------------------------------------------------------

            # Chart
            st.subheader("📊 Price Comparison")
            fig, ax = plt.subplots()
            labels = ["GemGem Price", "Competitor Avg", "Retail Estimate"]
            values = [gemgem_price, competitor_avg_price, retail_estimate]
            bars = ax.bar(labels, values, color=["#1f77b4", "#ff7f0e", "#2ca02c"])

            # Show values on top of bars
            for bar in bars:
                yval = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, yval + 50, f"${yval:.2f}",
                        ha="center", va="bottom", fontsize=9)

            ax.set_ylabel("Price (USD)")
            st.pyplot(fig)

            # Show savings
            st.subheader("💰 Savings")
            st.success(f"You save **${savings:.2f} ({savings_pct:.1f}%)** compared to competitors!")

            # Breakdown
            st.subheader("📖 Price Breakdown (Retail Estimate)")
            st.markdown(f"""
            - **Gold Cost:** ${retail_data['gold_cost']:.2f}  
            - **Diamond Cost:** ${retail_data['diamond_cost']:.2f}  
            - **Making Charges:** ${retail_data['making_charge']:.2f}  
            - **Retail Markup (50%)**  
            - **Final Retail Estimate:** **${retail_data['retail_price']:.2f}**
            """)
