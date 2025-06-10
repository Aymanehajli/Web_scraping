import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_bdm_article(url, output_filename="bdm_ios_article.csv"):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        logger.info(f"Fetching {url}")
        soup = BeautifulSoup(requests.get(url, headers=headers, timeout=10).text, "lxml")

        title   = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
        date    = soup.find("time")["datetime"] if soup.find("time") else ""
        
        author_selectors = ["span.byline", "span.author", "[rel='author']", ".author"]
        author = next((soup.select_one(sel).get_text(strip=True) for sel in author_selectors if soup.select_one(sel)), "")
        
        byline_selectors = [".article-social-content", ".entry-meta", ".byline", ".post-meta"]
        byline = next((soup.select_one(sel).get_text(" ", strip=True) for sel in byline_selectors if soup.select_one(sel)), "")
        
        entry = soup.find("div", class_="entry-content") or soup.find("article") or soup.find("main")
        paragraphs = [p.get_text(" ", strip=True) for p in entry.find_all("p")] if entry else []
        images     = [urljoin(url, img.get("src") or img.get("data-src")) for img in entry.find_all("img", src=True)] if entry else []

        meta_desc = (soup.find("meta", attrs={"name": "description"}) or {}).get("content", "")
        
        category_selectors = [".post-categories a", ".entry-categories a", ".tags a", ".category a"]
        categories = next(([c.get_text(strip=True) for c in soup.select(sel)] for sel in category_selectors if soup.select(sel)), [])
        
        data = {
            "url": url,
            "title": title,
            "date": date,
            "author": author,
            "byline": byline,
            "meta_description": meta_desc,
            "categories": "|".join(categories) if categories else "",
            "text": "\n\n".join(paragraphs),
            "paragraph_count": len(paragraphs),
            "image_count": len(images),
            "images": "|".join(images),
            "scraped_at": datetime.now().isoformat()
        }
        return data, output_filename
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return None, output_filename

def main():
    url = "https://www.blogdumoderateur.com/ios-26-modeles-iphone-compatibles/"
    data, filename = scrape_bdm_article(url)
    if data:
        pd.DataFrame([data]).to_csv(filename, index=False, encoding="utf-8")
        print(f"Saved to {filename}")
    else:
        print("Failed to scrape article")

if __name__ == "__main__":
    main()
