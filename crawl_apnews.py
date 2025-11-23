from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import time

EDGE_DRIVER_PATH = r"D:\edgedriver_win32\msedgedriver.exe"

def get_ap_news_list_selenium(topic, size):
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0")

    service = Service(EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=edge_options)

    try:
        # open search page
        url = f'https://apnews.com/search?q={topic}'
        driver.get(url)

        # wait for initial render
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # scroll to load more news (simple: scroll twice, adjustable)
        for _ in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # wait for content load

        # get page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        news_list = []

        cards = soup.find_all('div', class_='PagePromo-title')
        for card in cards:
            if len(news_list) >= size:  # stop when limit reached
                break
            a_tag = card.find('a')
            if a_tag:
                title = a_tag.get_text(strip=True)
                link = a_tag['href']
                news_list.append({'title': title, 'url': link})

        return news_list

    finally:
        driver.quit()



def get_ap_article_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        print(f"Crawling article: {url}")
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # body content
        paragraphs = soup.select("div.RichTextStoryBody p")
        content = " ".join(p.get_text(strip=True) for p in paragraphs)

        # publish time
        publish_date = ""
        t = soup.find("meta", attrs={"property": "article:published_time"})
        if t and t.get("content"):
            dt = datetime.fromisoformat(t["content"].replace("Z", "+00:00"))
            publish_date = dt.strftime("%Y-%m-%d")

        return {
            "content": content,
            "publish_date": publish_date
        }

    except Exception as e:
        print("Article parsing failed:", e)
        return {"content": "", "publish_date": ""}


def get_ap_news_with_content(topic, max_articles=100):
    news_list = get_ap_news_list_selenium(topic, max_articles)

    if not news_list:
        print("AP News found no relevant news")
        return []

    print(f"AP News found {len(news_list)} articles, starting to crawl body...")

    detailed = []
    for i, news in enumerate(news_list, 1):
        print(f"AP News progress: {i}/{min(len(news_list), max_articles)}")
        article = get_ap_article_content(news["url"])

        if article["content"]:
            detailed.append({
                "title": news["title"],
                "url": news["url"],
                "content": article["content"],
                "publish_date": article["publish_date"],
                "source": "AP News"
            })

        time.sleep(2)
    return detailed

#
#
# if __name__ == "__main__":
#     topic = "OpenAI"
#     detailed_news = get_ap_news_with_content(topic, max_articles=3)
#
#     if detailed_news:
#         print(f"\n成功爬取 {len(detailed_news)} 篇文章的详细内容:")
#         print("=" * 80)
#         for i, news in enumerate(detailed_news, 1):
#             print(f"\n{i}. 标题: {news['title']}")
#             print(f"   发布时间: {news['publish_date']}")
#             print(f"   链接: {news['url']}")
#             print(f"   内容预览: {news['content'][:200]}...")
#             print("-" * 80)
#     else:
#         print("未能获取到任何新闻内容")
