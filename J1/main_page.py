import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_bdm_web():
    """Scrape articles from the Web section of Blog du Modérateur."""
    
    url = "https://www.blogdumoderateur.com/web/"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; scraper-example/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"
    }
    
    try:
        logger.info(f"Fetching Web section: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        
        archive_desc_elem = soup.select_one(".archive-description p")
        archive_desc = archive_desc_elem.get_text(" ", strip=True) if archive_desc_elem else "No description found"
        
        
        popular_topics_links = soup.select(".popular-topics.pt-4.pb-md-1 a")
        popular_topics = "|".join(a.get_text(strip=True) for a in popular_topics_links) if popular_topics_links else "No popular topics found"
        
        rows = []
        articles = soup.select("article")
        
        logger.info(f"Found {len(articles)} articles")
        
        for i, art in enumerate(articles, 1):
            
            title_elem = art.select_one(".entry-title")
            title = title_elem.get_text(" ", strip=True) if title_elem else f"No title - Article {i}"
            
            
            time_el = art.select_one("time")
            date = ""
            if time_el:
                if time_el.has_attr("datetime"):
                    date = time_el["datetime"]
                else:
                    date = time_el.get_text(strip=True)
            
            
            favtag_elem = art.select_one(".favtag.color-b")
            favtag = favtag_elem.get_text(strip=True) if favtag_elem else "No tag"
            
            
            header_elem = art.select_one(".entry-header.pt-1")
            header = header_elem.get_text(" ", strip=True) if header_elem else "No header"
            
            
            excerpt_elem = art.select_one(".entry-excerpt.t-def.t-size-def.pt-1")
            excerpt = excerpt_elem.get_text(" ", strip=True) if excerpt_elem else "No excerpt"
            
            
            link_el = art.select_one("a")
            if link_el and link_el.has_attr("href"):
                link = urljoin(url, link_el["href"])
            else:
                link = "No link found"
            
            
            author_elem = art.select_one(".author, .entry-meta .author")
            author = author_elem.get_text(strip=True) if author_elem else "No author found"
            
            rows.append({
                "title": title,
                "date": date,
                "author": author,
                "favtag": favtag,
                "entry_header": header,
                "excerpt": excerpt,
                "url": link,
                "archive_description": archive_desc,
                "popular_topics": popular_topics,
                "scraped_at": datetime.now().isoformat()
            })
            
            logger.debug(f"Scraped article {i}: {title[:50]}...")
        
        
        df = pd.DataFrame(rows)
        output_file = "bdm_web_archive.csv"
        df.to_csv(output_file, index=False, encoding="utf-8")
        
        logger.info(f"Successfully scraped {len(rows)} articles")
        print(f"Web section scraped successfully!")
        print(f"Total articles: {len(rows)}")
        print(f"Archive description: {archive_desc[:100]}...")
        print(f"Popular topics: {popular_topics}")
        print(f"Saved to {output_file}")
        
        return df
        
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        print(f"Failed to fetch the page: {e}")
        return None
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"Scraping error: {e}")
        return None

def main():
    """Main function to run the scraper."""
    print("Starting Blog du Modérateur Web section scraper...")
    result = scrape_bdm_web()
    
    if result is not None:
        print("\nFirst few articles:")
        print(result[['title', 'date', 'favtag']].head())
    else:
        print("Scraping failed!")

if __name__ == "__main__":
    main()