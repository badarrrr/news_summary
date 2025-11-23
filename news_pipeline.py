import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from jinja2 import Template
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# from langchain.prompts import PromptTemplate
# from langchain.schema import BaseOutputParser

# 上面识别不到的可以用下面这种
from langchain_core.prompts import PromptTemplate  # PromptTemplate
from langchain_core.output_parsers.base import BaseOutputParser  # BaseOutputParser
from prompts import summary_prompt


from crawl_cnn import get_cnn_news_with_content
from crawl_apnews import get_ap_news_with_content
from crawl_bbc import get_bbc_news_with_content

class SummaryParser(BaseOutputParser):

    def parse(self, text: str) -> Dict[str, Any]:
        try:
            data = json.loads(text)

            # validate required fields
            required_fields = ['topic', 'entities', 'summary', 'timeline']
            for field in required_fields:
                if field not in data:
                    print(f"{field} is not in result")
                    data[field] = 'na'

            return data
        except json.JSONDecodeError:
            return {
                'topic': 'na',
                'entities': 'na',
                'summary': 'na',
                'timeline': 'na',
            }


class NewsSummaryPipeline:
    def __init__(self, topic: str = None):
        """
        Initialize the news-summary pipeline.
        In production you would plug in AskNews API; here we demo with crawled data.
        """
        self.llm = ChatOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
        )
        self.topic = topic

    def fetch_news_data(self, topic: str) -> List[Dict]:
        """
        Fetch news data from multiple sources.
        """
        # each method defaults to max_articles=100 internally
        cnn_news = get_cnn_news_with_content(topic)
        print(f'Successfully obtained {len(cnn_news)} items from CNN')

        ap_news = get_ap_news_with_content(topic)
        print(f'Successfully obtained {len(ap_news)} items from AP News')

        bbc_news = get_bbc_news_with_content(topic)
        print(f'Successfully obtained {len(bbc_news)} items from BBC News')

        all_news = cnn_news + ap_news + bbc_news
        return all_news

    def deduplicate_news(self, news_list: List[Dict]) -> List[Dict]:
        """
        Deduplicate & merge similar news using TF-IDF + cosine similarity.
        """
        if not news_list:
            return []

        # merge title + body as text representation
        texts = [news['title'] + ' ' + news.get('content', '') for news in news_list]

        # compute TF-IDF vectors
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)

        # cosine similarity matrix
        similarity_matrix = cosine_similarity(tfidf_matrix)

        # deduplication logic
        unique_news = []
        seen_indices = set()
        threshold = 0.85  # high threshold for strict dedup

        for i, news in enumerate(news_list):
            if i in seen_indices:
                continue

            # Mark the current news as saved
            seen_indices.add(i)

            # init url list. By default it contains the url of the current news.
            news['urls'] = [news['url']]

            # find similar items
            for j in range(i + 1, len(news_list)):
                if j not in seen_indices and similarity_matrix[i, j] >= threshold:
                    # Add the urls of news that are similar to the current news to the url list.
                    # The content of the similar news are discarded.
                    news['urls'].append(news_list[j]['url'])

                    # merge source if not duplicate
                    if news_list[j]['source'] not in news['source']:
                        news['source'] += ', ' + news_list[j]['source']

                    seen_indices.add(j)

            unique_news.append(news)

        return unique_news

    def extract_entities_and_summary(self, news_list: List[Dict]) -> Dict[str, Any]:
        """
        Extract entities and generate summary.
        """
        prompt = PromptTemplate(
            input_variables=["key_event", "news_list"],
            template=summary_prompt
        )

        llm_chain = prompt | self.llm | SummaryParser()

        try:
            result = llm_chain.invoke({"key_event": self.topic, "news_list": news_list})

            return result

        except Exception as e:
            print(f"Error: {str(e)}\n\n")

    def generate_html(self, processed_data: Dict, news_list: List[Dict]) -> str:
        """
        Generate HTML page.
        """
        with open('template.html', 'r', encoding='utf-8') as f:
            template_str = f.read()

        template = Template(template_str)

        html_content = template.render(
            topic=processed_data['topic'],
            summary=processed_data['summary'],
            entities=processed_data['entities'],
            timeline=processed_data['timeline'],
            news_articles=news_list,
            generated_date=datetime.now().strftime("%B %d, %Y %H:%M")
        )

        return html_content

    def run_pipeline(self, output_file: str = "news_summary.html") -> str:
        """
        Run the complete data pipeline.
        """
        print(f"Starting topic: {self.topic}")

        # 1. fetch news data
        print("Fetching news data...")
        news_data = self.fetch_news_data(self.topic)

        # 2. deduplication
        print("Deduplicating...")
        unique_news = self.deduplicate_news(news_data)

        # 3. extract entities & summary
        print("Generating summary & entities...")
        processed_data = self.extract_entities_and_summary(unique_news)

        # 4. generate HTML
        print("Generating HTML page...")
        html_content = self.generate_html(processed_data, unique_news)

        # 5. save file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Pipeline finished! Output file: {output_file}")
        return output_file


if __name__ == "__main__":
    # load env vars (commented because I set them in IDE)
    # load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if api_key:
        print("API Key loaded successfully!")
    else:
        print("API Key not found, please check environment variables")

    pipeline = NewsSummaryPipeline(topic="Tesla")
    pipeline.run_pipeline("lwx_test1.html")