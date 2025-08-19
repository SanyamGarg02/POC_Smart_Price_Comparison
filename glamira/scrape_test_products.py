#run this script to get poc_glamira.csv ie test glamira dataset. 
#Unable to use scraping to get urls first, so used manually added urls for now.

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import json
import csv

def extract_product_details(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # ✅ Extract name
    name_tag = soup.find("span", {"data-ui-id": "page-title-wrapper"})
    name = name_tag.get_text(strip=True) if name_tag else "N/A"

    # ✅ Extract price
    price_tag = soup.find("span", class_="price")
    price = price_tag.get_text(strip=True) if price_tag else "N/A"

    # ✅ Extract details
    details_dict = {}

    # General details
    tables = soup.find_all("table", class_="table-detail")
    for table in tables:
        first_row = table.find("tr")
        if first_row and "item-sku" in first_row.get("class", []):
            for row in table.find_all("tr"):
                label = row.find("td", class_="detail-label")
                value = row.find("td", class_="detail-value")
                if label and value:
                    key = label.text.strip().strip(":").replace("?", "").replace("[]", "")
                    val = value.text.strip()
                    details_dict[key] = val

    # Center Stone
    stone_section = soup.find("div", id="stone1_detail")
    if stone_section:
        table = stone_section.find("table", class_="table-detail")
        if table:
            for row in table.find_all("tr"):
                label = row.find("td", class_="detail-label")
                value = row.find("td", class_="detail-value")
                if label and value:
                    key = label.text.strip().strip(":").replace("?", "").replace("[]", "")
                    val = value.text.strip()
                    details_dict[key] = val

    return {
        "name": name,
        "price": price,
        "url": url,
        "details": json.dumps(details_dict, ensure_ascii=False),
    }

def save_to_csv(data_list, filename):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "price", "url", "details"])
        writer.writeheader()
        for row in data_list:
            writer.writerow(row)

if __name__ == "__main__":
    urls = [
        "https://www.glamira.com/glamira-bracelet-fouett.html?alloy=white-750&stone1=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-fionnuala-3-5-mm.html?alloy=yellow-585&stone1=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-fionnuala-3-0-mm.html?alloy=white-585&stone1=lab-grown-diamond",
        "https://www.glamira.com/glamira-bracelet-clasia.html?alloy=white-585&stone1=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-fionnuala-4-5-mm.html?alloy=yellow-585&stone1=ruby",
        "https://www.glamira.com/glamira-bracelet-denyse.html?alloy=yellow-585&stone1=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-tressa.html?alloy=white-375&stone1=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-tamesha.html?alloy=yellow-585&stone1=diamond-Brillant&stone2=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-fionnuala-2-5-mm.html?alloy=yellow-585&stone1=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-amazzi.html?alloy=yellow-585&pearl=white_pearl&stone1=lab-grown-diamond"
        "https://www.glamira.com/glamira-bracelet-iliana.html?alloy=white-585&stone1=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-astropel.html?alloy=white-silber&stone1=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-unerka.html?alloy=white-585&stone1=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-waren.html?alloy=red-585&stone1=lab-grown-diamond&stone2=lab-grown-diamond",
        "https://www.glamira.com/glamira-bangle-song.html?alloy=white-585&stone1=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-caoimhe-2-0-mm.html?alloy=white-585&stone1=diamond-Brillant",
        "https://www.glamira.com/glamira-bracelet-celesia.html?alloy=white-silber&stone1=blackdiamond"
    ]

    results = []
    for i, url in enumerate(urls):
        print(f"Scraping {i+1}/{len(urls)}: {url}")
        try:
            data = extract_product_details(url)
            results.append(data)
        except Exception as e:
            print(f"❌ Failed to scrape {url}: {e}")

    save_to_csv(results, "poc_glamira.csv")
    print("✅ Saved to poc_glamira.csv")
