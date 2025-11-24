# crawl_bbc.py
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import time

EDGE_DRIVER_PATH = r'D:\edgedriver_win32\msedgedriver.exe'

def get_article_content(url):
    """Crawl single BBC News article content"""
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
    )

    service = Service(EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=edge_options)

    try:
        print(f"Crawling article: {url}")
        driver.get(url)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # extract body
        content_parts = []
        paragraphs = soup.select('div[data-component="text-block"] p.ssrcss-1q0x1qg-Paragraph')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text:
                content_parts.append(text)
        full_content = ' '.join(content_parts)

        # extract publish time
        publish_date = ''
        time_tag = soup.select_one('time[data-testid="timestamp"]')
        if time_tag and time_tag.has_attr('datetime'):
            dt = datetime.fromisoformat(time_tag['datetime'].replace('Z', '+00:00'))
            publish_date = dt.strftime("%Y-%m-%d")

        return {'content': full_content, 'publish_date': publish_date}

    except Exception as e:
        print(f"Error crawling article {url}: {e}")
        return {'content': '', 'publish_date': ''}
    finally:
        driver.quit()


def get_news_list_selenium(topic, size):
    """Fetch BBC News list"""
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0")

    service = Service(EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=edge_options)

    try:
        search_url = f'https://www.bbc.co.uk/search?q={topic}'
        driver.get(search_url)

        # Wait for the initial rendering finished.
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="default-promo"]'))
        )

        # scroll to load more news (simple: scroll twice)
        for _ in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # extract news list
        items = soup.select("li")
        news_list = []

        for it in items:
            if len(news_list) >= size:  # Stop when upper bound is reached.
                break
            link_tag = it.select_one("a.ssrcss-163mj99-PromoLink")
            if not link_tag:
                continue

            url = link_tag["href"]
            title_tag = link_tag.select_one("p.ssrcss-1b1mki6-PromoHeadline")
            title = title_tag.get_text(strip=True) if title_tag else ""

            news_list.append({
                "title": title,
                "url": url
            })

        return news_list

    except Exception as e:
        print(f"Error searching news list: {e}")
        traceback.print_exc()
        return []
    finally:
        driver.quit()


def get_bbc_news_with_content(topic, max_articles=100):
    """Fetch BBC News list and crawl full content"""
    news_list = get_news_list_selenium(topic, max_articles)
    if not news_list:
        print("BBC News found no relevant news")
        return []

    print(f"BBC News found {len(news_list)} articles, crawling full content...")
    detailed_news = []

    for i, news in enumerate(news_list, 1):
        print(f" Progress: {i}/{min(len(news_list), max_articles)}")
        article_content = get_article_content(news['url'])
        if article_content['content']:
            detailed_news.append({
                'title': news['title'],
                'url': news['url'],
                'content': article_content['content'],
                'publish_date': article_content['publish_date'],
                'source': 'BBC News',
            })
        time.sleep(3)

    return detailed_news

if __name__ == "__main__":
    topic = "OpenAI"
    detailed_news = get_bbc_news_with_content(topic, max_articles=3)  # limit to 3 articles for test

    if detailed_news:
        print(f"\nSuccessfully crawled {len(detailed_news)} articles:")
        print("=" * 80)

        for i, news in enumerate(detailed_news, 1):
            print(f"\n{i}. Title: {news['title']}")
            print(f"   Publish Date: {news['publish_date']}")
            print(f"   URL: {news['url']}")
            print(f"   Content Preview: {news['content']}...")
            print("-" * 80)
    else:
        print("No articles retrieved")