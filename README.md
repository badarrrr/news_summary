# News Summary System

A tool for automatically generating structured news summaries from multiple news articles, providing topic overviews, key entities, timelines, and source articles in a user-friendly HTML format.

## Features

- **Automated Topic Identification**: Extracts concise and representative topic names from news content
- **Entity Extraction**: Identifies and categorizes key organizations, people, locations, and terms
- **Comprehensive Summaries**: Generates structured summaries with key developments and data points
- **Timeline Creation**: Organizes major events in chronological order
- **Responsive HTML Output**: Presents information in a clean, mobile-friendly format
- **Source Attribution**: Includes links to original articles for further reading

## Requirements

```
langchain==0.3.27
langchain-community==0.3.30
jinja2==3.1.6
requests==2.32.5
python-dotenv==1.1.1
openai==1.100.2
bs4==4.12.3
selenium==4.24.0
```

Install dependencies with:
```bash
pip install -r requirements.txt
```

## Usage

1. Prepare news articles related to a specific topic
2. Configure API keys and environment variables in `.env`
3. Run the main processing script to analyze articles
4. Generate HTML output with the structured summary

The system will process the input articles and produce an HTML file containing:
- Topic summary section
- Key entities categorized by type
- Timeline of major developments
- Source articles with links and brief excerpts

## Output Example

The generated HTML includes sections for:
- Topic header with generation date
- Detailed topic summary
- Key entities (organizations, people, locations, terms)
- Chronological timeline of events
- Source articles with metadata and links

Example outputs can be found in the `html` directory.

## Notes

- All summaries are generated based solely on provided news content
- The system maintains objectivity and neutrality in all generated content
- Dates are formatted consistently as YYYY-MM-DD
- Entity extraction focuses on accuracy and relevance to the topic

This tool is designed to help users quickly grasp the key points of multiple news articles on a specific topic, providing context and structure to complex news stories.