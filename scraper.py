from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time, csv, json

# ======= Setup =======
CHROMEDRIVER_PATH = "./chromedriver"

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
wait = WebDriverWait(driver, 15)

# ======= Helper: Wait for text =======
def wait_for_text(by, value):
    return wait.until(lambda d: (
        el := d.find_element(by, value)) and el.text.strip() != "" and el)

# ======= Load all products and collect URLs =======
def collect_product_links(base_url):
    print("Collecting product URLs")
    driver.get(base_url)
    time.sleep(2)

    # Keep clicking "Load More" until it disappears
    while True:
        try:
            load_more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='Mostrar Mais']]"))
            )
            driver.execute_script("arguments[0].click();", load_more_button)
            print("Clicked \"Load more\"")
            time.sleep(3)
        except TimeoutException:
            print("All products loaded.")
            break

    # Collect product links
    links = driver.find_elements(By.CSS_SELECTOR, "a.vtex-product-summary-2-x-clearLink")
    product_urls = list({link.get_attribute("href") for link in links if link.get_attribute("href")})
    print(f"Total product URLs found: {len(product_urls)}")
    return product_urls

# ======= Scrape product data =======
def scrape_product(url):
    print(f"Scraping: {url}")
    driver.get(url)
    time.sleep(2)

    # Title
    title = wait.until(EC.presence_of_element_located(
        (By.CLASS_NAME, "vtex-store-components-3-x-productNameContainer"))).text.strip()

    # Price
    script = """
    const container = document.querySelector('.vtex-product-price-1-x-currencyContainer--spotPricepdp');
    if (!container) return null;
    const parts = Array.from(container.querySelectorAll('span')).map(el => el.textContent.trim()).filter(Boolean);
    return parts;
    """
    price_parts = driver.execute_script(script)
    price = "".join(price_parts) if price_parts else ""

    # Description
    try:
        desc_element = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "stihlferramentas-loja-stihlferramentas-13-x-additionalDescriptionPDPText")))
        description = desc_element.text.strip()
    except:
        description = ""

    # Tech Specs
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
    image_urls = []
    images = driver.find_elements(By.CLASS_NAME, "vtex-store-components-3-x-productImageTag--main")
    for img in images:
        src = img.get_attribute("src")
        if src:
            image_urls.append(src)

    return {
        "title": title,
        "price": price,
        "description": description,
        "specs": specs,
        "images": image_urls,
        "url": url
    }

# ======= Main Process =======
try:
    all_products = []
    base_url = "https://loja.stihl.com.br/todos-os-produtos"
    product_links = collect_product_links(base_url)

    for link in product_links:
        try:
            product_data = scrape_product(link)
            all_products.append(product_data)
        except Exception as e:
            print(f"Failed on {link}: {e}")

    # === Export CSV ===
    with open("all_products.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
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
    print("CSV export done: all_products.csv")

    # === Export JSON ===
    with open("all_products.json", "w", encoding="utf-8") as jsonfile:
        json.dump(all_products, jsonfile, indent=2, ensure_ascii=False)
    print("JSON export done: all_products.json")

finally:
    driver.quit()
    
