from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import json
import time

INPUT_CSV = "test_csv.csv"   #create a test_csv by picking some products from products.csv
OUTPUT_JSON = "test_output.json"
OUTPUT_CSV = "poc_kay.csv"
WAIT_TIME = 15

options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # optional: run headless
driver = webdriver.Chrome(options=options)

results = []

with open(INPUT_CSV, newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for idx, row in enumerate(reader):
        url = row["url"]
        print(f"\n[{idx+1}] Visiting: {url}")

        try:
            driver.get(url)

            # Wait until product title appears
            WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1'))
            )
            print("✅ Page loaded")

            # Scroll down to bottom to load JS content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Try to click Details button
            try:
                details_btn = WebDriverWait(driver, WAIT_TIME).until(
                    EC.element_to_be_clickable((By.XPATH, '//h4[contains(., "Details")]/ancestor::button'))
                )
                ActionChains(driver).move_to_element(details_btn).click().perform()
                print("✅ Clicked Details button")
                time.sleep(2)
            except Exception as e:
                print("⚠️ Details button not found or not clickable, skipping click:", e)

            time.sleep(2)  # wait for dynamic content

            html = driver.page_source

            # save page for debug
            dump_file = f"debug_page_{idx+1}.html"
            with open(dump_file, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"💾 Saved page to {dump_file}")

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            tables = soup.find_all("table", class_="specs-table")
            print(f"👉 Found {len(tables)} specs tables")

            product_details = {}
            for table in tables:
                thead = table.find("thead")
                header = thead.get_text(strip=True) if thead else "Unknown Section"
                items = {}
                for tr in table.find_all("tr"):
                    tds = tr.find_all("td")
                    if len(tds) >= 2:
                        key = tds[0].get_text(strip=True)
                        value = tds[1].get_text(strip=True)
                        items[key] = value
                product_details[header] = items

            record = {
                "name": row.get("name", "N/A"),
                "price": row.get("price", "N/A"),
                "url": url,
                "details": product_details
            }
            print("✅ Parsed details:", json.dumps(product_details, indent=2))
            results.append(record)

        except Exception as e:
            print(f"❌ Failed to process product at {url}: {e}")
            continue  # go to next product

# save JSON
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print(f"\n✅ JSON saved to: {OUTPUT_JSON}")

# save CSV: name, price, url, details(json)
with open(OUTPUT_CSV, "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "price", "url", "details"])
    writer.writeheader()
    for item in results:
        writer.writerow({
            "name": item["name"],
            "price": item["price"],
            "url": item["url"],
            "details": json.dumps(item["details"], ensure_ascii=False)
        })
print(f"✅ CSV saved to: {OUTPUT_CSV}")

driver.quit()
print("\n🎉 Done!")
