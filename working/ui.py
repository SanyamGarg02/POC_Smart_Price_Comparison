import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from price_calculator import calculate_retail_price
from normalization import get_similar_prices
from normalization import preprocess_df

# Load datasets
gemgem_df = pd.read_csv("data/poc_gemgem.csv")
kay_df = preprocess_df(pd.read_csv("data/poc_kay.csv"))
glamira_df = preprocess_df(pd.read_csv("data/poc_glamira.csv"))
competitor_df = pd.concat([kay_df, glamira_df], ignore_index=True)

st.set_page_config(page_title="Jewelry Price Comparison POC", layout="centered")
st.title("💎 Jewelry Price Comparison Tool (POC)")

# Step 1: Input Product
listing_id = st.text_input("Enter GemGem Listing ID:", "")

if listing_id:
    # Fetch product
    product_row = gemgem_df[gemgem_df["listing_id"] == listing_id]
    if product_row.empty:
        st.error("❌ Listing ID not found in dataset.")
    else:
        st.subheader("📌 Product Details")
        st.write(product_row[["name", "details"]].iloc[0])

        # Step 2: Competitor Products
        st.subheader("🔍 Similar Competitor Products")
        similar_products = get_similar_prices(listing_id, top_n=5)

        if not similar_products["similar_products"]:
            st.warning("⚠️ No similar products found for this listing.")
        else:
            st.success(f"Found {len(similar_products['similar_products'])} similar products!")

            # Step 3: Calculate Prices
            gemgem_price = product_row["price"].iloc[0]
            competitor_avg_price = similar_products["similar_website_average_price"].mean()

            price_breakdown = calculate_retail_price(listing_id, gemgem_df)
            retail_estimate = price_breakdown.get("retail_price", 0.0)

            savings = competitor_avg_price - gemgem_price
            savings_pct = (savings / competitor_avg_price * 100) if competitor_avg_price > 0 else 0

            # Step 4: Chart
            st.subheader("📊 Price Comparison")
            fig, ax = plt.subplots()
            labels = ["GemGem Price", "Competitor Avg", "Retail Estimate"]
            values = [gemgem_price, competitor_avg_price, retail_estimate]
            bars = ax.bar(labels, values, color=["#1f77b4", "#ff7f0e", "#2ca02c"])

            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, height,
                        f"${height:,.0f}", ha="center", va="bottom", fontsize=10, weight="bold")

            ax.set_ylabel("Price (USD)")
            st.pyplot(fig)

            # Step 5: Show Savings
            st.subheader("💰 Savings")
            st.success(f"You save **${savings:.2f} ({savings_pct:.1f}%)** compared to competitors!")

            # Step 6: Transparent Calculation
            st.subheader("📖 Price Breakdown (Retail Estimate)")
            if price_breakdown:
                st.markdown(f"""
                - **Gold Cost:** {price_breakdown['gold_weight']} g × ${price_breakdown['gold_price_per_gram']}/g = **${price_breakdown['gold_cost']}**
                - **Diamond Cost:** {price_breakdown['diamond_weight']} ct × ${price_breakdown['diamond_price_per_carat']}/ct ({price_breakdown['diamond_source']}) = **${price_breakdown['diamond_cost']}**
                - **Making Charges:** {price_breakdown['gold_weight']} g × $20/g = **${price_breakdown['making_charge']}**
                - **Retail Markup ({price_breakdown['markup_pct']}%):** **${price_breakdown['markup_value']}**
                ---
                - ✅ **Final Retail Estimate: ${price_breakdown['retail_price']}**
                """)
            else:
                st.warning("⚠️ Could not calculate retail estimate for this product.")
