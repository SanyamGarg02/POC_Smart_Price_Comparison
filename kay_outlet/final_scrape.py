#this script scrapes all products from kay outlet and saves them to a csv file, you can use some of those urls to create a test_csv.csv and pass it to testing_parser2.py and get something like poc_kay.csv. or directly use the poc_kay.csv to run the app.py

import requests
import csv
from dotenv import load_dotenv
import os
from pathlib import Path


# All your category IDs - add or remove as needed
category_ids = [
    "8000000245",  # Example: Women's Engagement Rings
    "8000000365",  # Example: Men's Jewelry
    # add more here...
]

# Load .env from poc/ (the parent directory of current script)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

api_base = os.getenv("UNBXD_API_BASE")

# Fields to request
fields = "v_MSRP,v_allCategories,v_availableSwatchesCode,v_availableSwatchesValues,v_badgeId,v_badgeText,v_badgeImageAltText,v_bopisPOS,v_category,v_custom_discount_amount,v_custom_discount_percentage,v_custom_discount_percentage_string,v_stockLevel,v_url,v_variant_code,v_sku,v_productUrl,v_stockLevelStatus,v_title,v_specials,v_numberOfRatings,v_avgRating,v_imgx100,v_imgx135,v_imgx260,v_imgx320,v_imageUrl,v_price,v_financePaymentApr,v_lowestFinanceAmountPerMonth,v_isFinancingAvailable,v_availableToRent,v_rentalPrice,v_moreOptions,v_isPJProduct,v_vendorID,v_ampProductType,v_categoryPromotion"

# To store final deduplicated products
all_products = {}
total_count = 0

for cat_id in category_ids:
    print(f"\n🚀 Scraping category {cat_id} ...")
    start = 0
    rows = 42

    while True:
        params = {
            "p": f"v_categoryPathId:{cat_id}",
            "pagetype": "boolean",
            "version": "V2",
            "start": str(start),
            "rows": str(rows),
            "format": "json",
            "user-type": "first-time",
            "fields": fields,
            "uid": "uid-1754128934137-70560"
        }
        response = requests.get(api_base, params=params)
        data = response.json()

        products = data.get("response", {}).get("products", [])
        print(f"  ✅ Found {len(products)} products at offset {start}")

        if not products:
            break

        for p in products:
            # products often have multiple variants; pick first
            v = p["variants"][0]

            product_id = v.get("v_url") or v.get("v_productUrl")
            if not product_id:
                continue

            # Use full URL
            full_url = "https://www.kayoutlet.com" + product_id

            # Deduplicate: store by URL
            all_products[full_url] = {
                "name": v.get("v_title", "N/A"),
                "price": v.get("v_price", "N/A"),
                "url": full_url,
                
            }

        start += rows

print(f"\n🎉 Done! Total unique products scraped: {len(all_products)}")

# Write to CSV
with open("all_products.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "name", "price", "url"
    ])
    writer.writeheader()
    writer.writerows(all_products.values())

print("✅ CSV saved as all_products.csv")
