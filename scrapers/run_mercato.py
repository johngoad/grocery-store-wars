from scrapers.db import execute

# Update thriftway store to Mercato platform
execute(
    "UPDATE stores SET platform = ?, base_url = ?, product_count = 0 WHERE id = ?",
    ["mercato", "https://www.mercato.com/shop/vashon-thriftway", "thriftway-vashon"]
)
print("Updated thriftway-vashon to mercato platform")

# Run the scraper
from scrapers.mercato import scrape_all
scrape_all(delay=0.3, batch_limit=5000)
