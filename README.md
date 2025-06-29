# STIHL Brazil Product Scraper

This Python-based web scraper extracts product data from the official STIHL Brazil web store using Selenium. The scraper collects:
- Product title
- Price (formatted for Brazilian locale)
- Description
- Technical specifications (as a dictionary)
- Image URLs
- Product page URL

## Features
- Navigates the product catalog by simulating "Load More" interactions
- Extracts structured data per product page
- Exports output as both CSV and JSON
- Headless mode for automated execution

## Output
- `all_products.json` — Machine-readable data format
- `all_products.csv` — Human-readable spreadsheet format

## ▶Usage
1. Ensure you have [ChromeDriver](https://chromedriver.chromium.org/) installed and accessible via `CHROMEDRIVER_PATH`.
2. Install dependencies:
   ```bash
   pip install selenium
