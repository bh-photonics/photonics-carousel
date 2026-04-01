import sys
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

PAGES = [
    "https://www.photonics.com",
    "https://www.photonics.com/BioPhotonics",
    "https://www.photonics.com/Vision-Spectra",
]

items = []

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
        ]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
    )

    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    for url in PAGES:
        try:
            print(f"Fetching {url}...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for Cloudflare challenge to pass if present
            for _ in range(15):
                title = page.title()
                print(f"  Page title: {title}")
                if "just a moment" not in title.lower():
                    break
                time.sleep(2)

            # Wait for the carousel to appear
            try:
                page.wait_for_selector("div.LAB_CarouselTitle", timeout=15000)
            except PlaywrightTimeoutError:
                print(f"  Carousel not found on {url}", file=sys.stderr)
                continue

            soup = BeautifulSoup(page.content(), "html.parser")
            titles = soup.select("div.LAB_CarouselTitle")
            print(f"  Found {len(titles)} LAB_CarouselTitle elements")

            for title_el in titles:
                parent = title_el.parent
                if not parent:
                    continue
                label_el = parent.select_one("div.LAB_CarouselLabel")
                link_el = parent.select_one("a.BTN_CarouselSlide")
                if not (label_el and link_el):
                    continue
                items.append({
                    "title": title_el.get_text(strip=True),
                    "label": label_el.get_text(strip=True),
                    "href": link_el.get("href", ""),
                })
                break

        except Exception as e:
            print(f"Error fetching {url}: {e}", file=sys.stderr)

    browser.close()

# Build HTML in the same structure the Android app expects
html_items = "\n".join(
    f'  <div class="carousel-item">\n'
    f'    <div class="LAB_CarouselLabel">{item["label"]}</div>\n'
    f'    <div class="LAB_CarouselTitle">{item["title"]}</div>\n'
    f'    <a class="BTN_CarouselSlide" href="{item["href"]}">Read</a>\n'
    f'  </div>'
    for item in items
)

html = f"""<!DOCTYPE html>
<html>
<body>
{html_items}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Wrote {len(items)} carousel items to index.html")
