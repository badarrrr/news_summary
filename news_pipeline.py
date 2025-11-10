import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from jinja2 import Template
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from crawl_cnn import get_cnn_news_with_content
from langchain.schema import BaseOutputParser
from prompts import summary_prompt


class SummaryParser(BaseOutputParser):

    def parse(self, text: str) -> Dict[str, Any]:
        try:
            data = json.loads(text)

            # 验证必需字段
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
        初始化新闻摘要管道
        在实际应用中，这里会集成AskNews API
        这里使用模拟数据作为演示
        """
        self.llm = ChatOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
        )
        self.topic = topic

    def fetch_news_data(self, topic: str) -> List[Dict]:
        """
        获取新闻数据
        在实际应用中，这里会调用AskNews API
        这里返回模拟数据
        """
        # 模拟从多个来源获取的新闻数据
        print('开始从CNN获取数据')
        cnn_news = get_cnn_news_with_content(topic)
        print(f'成功从CNN获取{len(cnn_news)}条数据')

        return cnn_news

    def deduplicate_news(self, news_list: List[Dict]) -> List[Dict]:
        """
        去重和合并相似新闻
        """
        # 简单的基于标题相似度的去重
        unique_news = []
        seen_titles = set()

        for news in news_list:
            # 简化的去重逻辑 - 实际应用中可以使用更复杂的相似度检测
            title_key = news['title'][:50]  # 取前50个字符作为关键标识
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)

        return unique_news

    def extract_entities_and_summary(self, news_list: List[Dict]) -> Dict[str, Any]:
        """
        提取实体和生成摘要 - 带文件保存调试版本
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
        生成HTML页面
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
            generated_date=datetime.now().strftime("%Y年%m月%d日 %H:%M")
        )

        return html_content

    def run_pipeline(self, output_file: str = "news_summary.html") -> str:
        """
        运行完整的数据管道
        """
        print(f"开始处理主题: {self.topic}")

        # 1. 获取新闻数据
        print("获取新闻数据...")
        news_data = self.fetch_news_data(self.topic)

        # 2. 去重处理
        print("去重处理...")
        unique_news = self.deduplicate_news(news_data)

        # 3. 提取实体和生成摘要
        print("生成摘要和提取实体...")
        processed_data = self.extract_entities_and_summary(unique_news)

        # 4. 生成HTML
        print("生成HTML页面...")
        html_content = self.generate_html(processed_data, unique_news)

        # 5. 保存文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"处理完成！输出文件: {output_file}")
        return output_file


if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    pipeline = NewsSummaryPipeline(topic="OpenAI")
    pipeline.run_pipeline("demo_output.html")
