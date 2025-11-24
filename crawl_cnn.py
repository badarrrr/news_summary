from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import time

EDGE_DRIVER_PATH = r"D:\edgedriver_win32\msedgedriver.exe"

def get_article_content(url):
    """Crawl single CNN article content"""
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0")

    service = Service(EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=edge_options)

    try:
        print(f"Crawling article: {url}")
        driver.get(url)

        # Wait until the article content is loaded.
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Obtain the page source.
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # extract content
        content_parts = []

        # Method 1: finding all the p elements of within the article elements.
        paragraphs = soup.find_all('p', class_='paragraph-elevate inline-placeholder vossi-paragraph')
        if paragraphs:
            for p in paragraphs:
                text = p.get_text(strip=True)
                content_parts.append(text)

        # Merge all the content.
        full_content = ' '.join(content_parts)

        # extract publish date
        publish_date = soup.find('span', class_="timestamp__time-since")
        if publish_date:
            publish_date = publish_date['data-first-publish']
            dt = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
            formatted_date = dt.strftime("%Y-%m-%d")
            publish_date = formatted_date
        else:
            publish_date = ''

        return {
            'content': full_content,
            'publish_date': publish_date,
        }

    except Exception as e:
        print(f"Error crawling article {url}: {e}")
        return {
            'content': '',
            'publish_date': '',
        }
    finally:
        driver.quit()


def get_news_list_selenium(topic, size):
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0")

    service = Service(EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=edge_options)

    try:
        url = f'https://edition.cnn.com/search?q={topic}&from=0&size={size}&page=1&sort=newest&types=article'
        driver.get(url)

        # wait for page load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "container__headline"))
        )

        # get page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        news_list = []
        # find headline elements
        headlines = soup.find_all(['span', 'a'], class_=lambda x: x and 'headline' in x)

        for headline in headlines[:10]:  # Get the top 10 headlines.
            title = headline.get_text(strip=True)
            if title and len(title) > 10:  # filter too short
                link = headline.find_parent('a')
                url = link.get('href') if link else ''
                if url and not url.startswith('http'):
                    url = 'https://edition.cnn.com' + url

                news_list.append({
                    'title': title,
                    'url': url
                })

        return news_list

    except Exception as e:
        print(f"Error searching news list: {e}")
        return []
    finally:
        driver.quit()


def get_cnn_news_with_content(topic, max_articles=100):
    """Fetch news list and crawl full content"""
    # get news list
    news_list = get_news_list_selenium(topic, max_articles)

    if not news_list:
        print("CNN found no relevant news")
        return []

    print(f"CNN found {len(news_list)} articles, starting to crawl full content...")

    # crawl each article
    detailed_news = []
    for i, news in enumerate(news_list, 1):
        print(f"CNN progress: {i}/{min(len(news_list), max_articles)}")

        # crawl article content
        article_content = get_article_content(news['url'])
        if article_content['content']:
            # merge info
            detailed_news.append({
                'title': news['title'],
                'url': news['url'],
                'content': article_content['content'],
                'publish_date': article_content['publish_date'],
                'source': 'CNN',
            })


        time.sleep(3)

    return detailed_news


# test
if __name__ == "__main__":
    topic = "OpenAI"
    detailed_news = get_cnn_news_with_content(topic, max_articles=10)  # limit to 10 articles for test

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
    # get_article_content('https://edition.cnn.com/2025/11/03/business/david-solomon-goldman-sachs-ai')