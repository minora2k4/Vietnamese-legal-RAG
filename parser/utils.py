import os
import json
import re
# import html_to_markdown # type: ignore
from pprint import pprint

def load_json(path):
    """ Load data from local json file """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def save_json(path, data):
    """ Save data to local json file """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def clean_newlines(text):
    # 1. Remove markdown traces (Images and Footnotes/References)
    # Matches: ![](path) or [2](#link) or [[2]](#link)
    text = re.sub(r'!\[.*?\]\(.*?\)|\[{1,2}.*?\]{1,2}\(.*?\)', ' ', text)
    # 2. Replace 2 or more newlines with a unique temporary placeholder
    # This prevents paragraph breaks from getting flattened in the next step
    protected_text = re.sub(r'\n{2,}', '___PARAGRAPH_BREAK___', text)
    # 3. Replace any remaining single newlines with a space
    cleaned_text = protected_text.replace('\n', ' ')
    # 4. Restore the paragraph breaks back to a single newline
    final_text = cleaned_text.replace('___PARAGRAPH_BREAK___', '\n')
    return final_text

def html2markdown(html):
    """ HTML to Markdown Conversion Pipeline """
    # markdown = html_to_markdown.convert(html).content
    markdown = markdown.replace("*", "").replace("## ", "").replace("“", "\"").replace("”", "\"").strip()
    markdown = clean_newlines(markdown)
    return markdown