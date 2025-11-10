from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import time


def get_article_content(url):
    """爬取单个新闻文章的详细内容"""
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0")

    service = Service('/Users/jeremy/Downloads/edgedriver_mac64_m1/msedgedriver')
    driver = webdriver.Edge(service=service, options=edge_options)

    try:
        print(f"正在爬取文章: {url}")
        driver.get(url)

        # 等待文章内容加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # 获取页面源码
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 提取文章内容
        content_parts = []

        # 方法1: 查找article标签内的所有p标签
        paragraphs = soup.find_all('p', class_='paragraph-elevate inline-placeholder vossi-paragraph')
        if paragraphs:
            for p in paragraphs:
                text = p.get_text(strip=True)
                content_parts.append(text)

        # 合并所有内容
        full_content = ' '.join(content_parts)

        # 提取发布日期
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
        print(f"爬取文章内容时出错 {url}: {e}")
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

    service = Service('/Users/jeremy/Downloads/edgedriver_mac64_m1/msedgedriver')
    driver = webdriver.Edge(service=service, options=edge_options)

    try:
        url = f'https://edition.cnn.com/search?q={topic}&from=0&size={size}&page=1&sort=newest&types=article'
        driver.get(url)

        # 等待页面加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "container__headline"))
        )

        # 获取页面源码
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        news_list = []
        # 查找新闻标题元素
        headlines = soup.find_all(['span', 'a'], class_=lambda x: x and 'headline' in x)

        for headline in headlines[:10]:  # 取前10个
            title = headline.get_text(strip=True)
            if title and len(title) > 10:  # 过滤太短的标题
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
        print(f"搜索新闻列表时出错: {e}")
        return []
    finally:
        driver.quit()


def get_cnn_news_with_content(topic, max_articles=5):
    """获取新闻列表并爬取每个新闻的详细内容"""
    # 获取新闻列表
    news_list = get_news_list_selenium(topic, max_articles)

    if not news_list:
        print("CNN未找到相关新闻")
        return []

    print(f"CNN找到 {len(news_list)} 条新闻，开始爬取详细内容...")

    # 爬取每个新闻的详细内容
    detailed_news = []
    for i, news in enumerate(news_list, 1):
        print(f"CNN进度: {i}/{min(len(news_list), max_articles)}")

        # 爬取文章内容
        article_content = get_article_content(news['url'])
        if article_content['content']:
            # 合并信息
            detailed_news.append({
                'title': news['title'],
                'url': news['url'],
                'content': article_content['content'],
                'publish_date': article_content['publish_date'],
                'source': 'CNN',
            })


        time.sleep(3)

    return detailed_news


# 测试
if __name__ == "__main__":
    topic = "OpenAI"
    detailed_news = get_cnn_news_with_content(topic, max_articles=10)  # 限制为3篇文章进行测试

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
    # get_article_content('https://edition.cnn.com/2025/11/03/business/david-solomon-goldman-sachs-ai')