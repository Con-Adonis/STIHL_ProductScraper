from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time, csv, json

# ====== Configuration ======
CHROMEDRIVER_PATH = "./chromedriver"
BASE_URL = "https://loja.stihl.com.br/todos-os-produtos"

# ====== Setup Chrome driver ======
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
wait = WebDriverWait(driver, 15)

# ====== Collect all product links ======
def collect_product_links():
    print("Loading all products.")
    driver.get(BASE_URL)
    time.sleep(2)

    # Click "Load More" until all products are visible
    while True:
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='Mostrar Mais']]"))
            )
            driver.execute_script("arguments[0].click();", btn)
            print("Clicked 'Load more'")
            time.sleep(2)
        except TimeoutException:
            print("All products loaded.")
            break

    # Get product page URLs
    links = driver.find_elements(By.CSS_SELECTOR, "a.vtex-product-summary-2-x-clearLink")
    urls = list({link.get_attribute("href") for link in links if link.get_attribute("href")})
    print(f"Found {len(urls)} product URLs.")
    return urls

# ====== Scrape product data from one page ======
def scrape_product(url):
    print(f"Scraping: {url}")
    driver.get(url)
    time.sleep(2)

    # Title
    title = wait.until(EC.presence_of_element_located(
        (By.CLASS_NAME, "vtex-store-components-3-x-productNameContainer"))).text.strip()

    # Price
    price_script = """
    const container = document.querySelector('.vtex-product-price-1-x-currencyContainer--spotPricepdp');
    if (!container) return null;
    return Array.from(container.querySelectorAll('span')).map(el => el.textContent.trim()).filter(Boolean);
    """
    price_parts = driver.execute_script(price_script)
    price = "".join(price_parts) if price_parts else ""

    # Description
    try:
        desc = wait.until(EC.presence_of_element_located((
            By.CLASS_NAME, "stihlferramentas-loja-stihlferramentas-13-x-additionalDescriptionPDPText")))
        description = desc.text.strip()
    except:
        description = ""

    # Technical Specs
    specs = {}
    try:
        spec_list = wait.until(EC.presence_of_element_located((
            By.CLASS_NAME, "stihlferramentas-loja-stihlferramentas-13-x-TechnicalSpecificationList")))
        items = spec_list.find_elements(By.CLASS_NAME,
            "stihlferramentas-loja-stihlferramentas-13-x-TechnicalSpecificationItem")

        for item in items:
            name = item.find_element(By.CLASS_NAME,
                "stihlferramentas-loja-stihlferramentas-13-x-TechnicalSpecificationName"
            ).get_attribute("textContent").strip()

            value = item.find_element(By.CLASS_NAME,
                "stihlferramentas-loja-stihlferramentas-13-x-TechnicalSpecificationValue"
            ).get_attribute("textContent").strip()

            specs[name] = value
    except:
        pass

    # Images
    images = []
    image_elements = driver.find_elements(By.CLASS_NAME, "vtex-store-components-3-x-productImageTag--main")
    for img in image_elements:
        src = img.get_attribute("src")
        if src:
            images.append(src)

    return {
        "title": title,
        "price": price,
        "description": description,
        "specs": specs,
        "images": images,
        "url": url
    }

# ====== Main Execution ======
try:
    all_products = []
    product_links = collect_product_links()

    for link in product_links:
        try:
            product = scrape_product(link)
            all_products.append(product)
        except Exception as e:
            print(f"Error scraping {link}: {e}")

    # Export to CSV
    with open("all_products.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Price", "Description", "Specifications", "Image URLs", "Product URL"])
        for p in all_products:
            writer.writerow([
                p["title"],
                p["price"],
                p["description"],
                json.dumps(p["specs"], ensure_ascii=False),
                "; ".join(p["images"]),
                p["url"]
            ])

    # Export to JSON
    with open("all_products.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print("Export complete: JSON & CSV")

finally:
    driver.quit()
