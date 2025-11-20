# crawl_reuters.py

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
    """爬取Reuters单篇新闻内容"""
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
    )

    service = Service(EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=edge_options)

    try:
        print(f"正在爬取文章: {url}")
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        content_parts = []

        paragraphs = soup.find_all('p', class_='article-body__content__text')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text:
                content_parts.append(text)

        full_content = ' '.join(content_parts)

        publish_date = ''
        date_tag = soup.find('meta', attrs={'name': 'article:published_time'})
        if date_tag and date_tag.has_attr('content'):
            dt = datetime.fromisoformat(date_tag['content'].replace('Z', '+00:00'))
            publish_date = dt.strftime("%Y-%m-%d")

        return {'content': full_content, 'publish_date': publish_date}

    except Exception as e:
        print(f"爬取文章内容时出错 {url}: {e}")
        return {'content': '', 'publish_date': ''}
    finally:
        driver.quit()


def get_news_list_selenium(topic, size):
    """获取Reuters新闻列表"""
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
    )

    service = Service(EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=edge_options)

    try:
        search_url = f'https://www.reuters.com/site-search/?query={topic}'
        driver.get(search_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'search-result-title'))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        news_list = []

        headlines = soup.find_all('h3', class_='search-result-title')
        for h in headlines[:size]:
            link_tag = h.find('a')
            if link_tag:
                title = link_tag.get_text(strip=True)
                url = link_tag['href']
                if url and not url.startswith('http'):
                    url = 'https://www.reuters.com' + url

                if title and len(title) > 10:
                    news_list.append({'title': title, 'url': url})

        return news_list

    except Exception as e:
        print(f"搜索新闻列表时出错: {e}")
        return []
    finally:
        driver.quit()


def get_reuters_news_with_content(topic, max_articles=5):
    """获取Reuters新闻列表并爬取详细内容"""
    news_list = get_news_list_selenium(topic, max_articles)
    if not news_list:
        print("Reuters未找到相关新闻")
        return []

    print(f"Reuters找到 {len(news_list)} 条新闻，开始爬取详细内容...")
    detailed_news = []

    for i, news in enumerate(news_list, 1):
        print(f"Reuters进度: {i}/{min(len(news_list), max_articles)}")
        article_content = get_article_content(news['url'])
        if article_content['content']:
            detailed_news.append({
                'title': news['title'],
                'url': news['url'],
                'content': article_content['content'],
                'publish_date': article_content['publish_date'],
                'source': 'Reuters',
            })
        time.sleep(3)

    return detailed_news

if __name__ == "__main__":
    topic = "OpenAI"
    detailed_news = get_reuters_news_with_content(topic, max_articles=3)  # 限制为3篇文章进行测试

    if detailed_news:
        print(f"\n成功爬取 {len(detailed_news)} 篇文章的详细内容:")
        print("=" * 80)

        for i, news in enumerate(detailed_news, 1):
            print(f"\n{i}. 标题: {news['title']}")
            print(f"   发布时间: {news['publish_date']}")
            print(f"   链接: {news['url']}")
            print(f"   内容预览: {news['content']}...")
            print("-" * 80)
    else:
        print("未能获取到任何新闻内容")
