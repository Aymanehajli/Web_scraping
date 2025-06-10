import requests, pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_bdm_article(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        soup = BeautifulSoup(requests.get(url, headers=headers, timeout=10).text, "lxml")

        title  = (soup.find("h1") or {}).get_text(strip=True)
        date   = (soup.find("time") or {}).get("datetime", "")

        author_sel = ["span.byline", "span.author", "[rel='author']", ".author"]
        author = next((soup.select_one(s).get_text(strip=True) for s in author_sel if soup.select_one(s)), "")

        byline_sel = [".article-social-content", ".entry-meta", ".byline", ".post-meta"]
        byline = next((soup.select_one(s).get_text(" ", strip=True) for s in byline_sel if soup.select_one(s)), "")

        entry = soup.find("div", class_="entry-content") or soup.find("article") or soup.find("main")
        paragraphs = [p.get_text(" ", strip=True) for p in entry.find_all("p")] if entry else []
        list_items = [li.get_text(" ", strip=True) for li in entry.find_all("li")] if entry else []
        images = [urljoin(url, img.get("src") or img.get("data-src")) for img in entry.find_all("img", src=True)] if entry else []

        meta_desc = (soup.find("meta", attrs={"name": "description"}) or {}).get("content", "")

        return {
            "url": url,
            "title": title,
            "date": date,
            "author": author,
            "byline": byline,
            "meta_description": meta_desc,
            "paragraphs": "\n\n".join(paragraphs),
            "paragraph_count": len(paragraphs),
            "list_items": "|".join(list_items),
            "list_item_count": len(list_items),
            "image_count": len(images),
            "images": "|".join(images),
            "scraped_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(e)
        return None

def main():
    url = "https://www.blogdumoderateur.com/monde-sans-internet-jeunes-favorables/"
    data = scrape_bdm_article(url)
    if data:
        pd.DataFrame([data]).to_csv("bdm_article_internet.csv", index=False, encoding="utf-8")
        print("Sauvegardé dans bdm_article.csv")
    else:
        print("Échec du scraping")

if __name__ == "__main__":
    main()
