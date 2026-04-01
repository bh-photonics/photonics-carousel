import cloudscraper
from bs4 import BeautifulSoup
import sys

PAGES = [
    "https://www.photonics.com",
    "https://www.photonics.com/BioPhotonics",
    "https://www.photonics.com/Vision-Spectra",
]

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

items = []

for url in PAGES:
    try:
        response = scraper.get(url, timeout=30)
        print(f"[{url}] status={response.status_code} length={len(response.text)}")
        print(f"[{url}] preview: {response.text[:300]}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        titles = soup.select("div.LAB_CarouselTitle")
        print(f"[{url}] found {len(titles)} LAB_CarouselTitle elements")
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
            break  # one item per publication page
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)

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
