import requests
from bs4 import BeautifulSoup
import re
import dateutil.parser
from datetime import datetime

def load_config_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to load configuration")

def highlight_keywords(alert, keywords):
    for keyword in keywords:
        highlighted_keyword = f"<span class='highlight'>{keyword}</span>"
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        if 'description' in alert:
            alert['description'] = re.sub(pattern, highlighted_keyword, alert['description'])
        if 'title' in alert:
            alert['title'] = re.sub(pattern, highlighted_keyword, alert['title'])
    return alert

def process_feeds_recursive(feeds, db, index=0):
    if index >= len(feeds):
        return
    site = feeds[index]
    response = requests.get(site)
    items = BeautifulSoup(response.content, 'xml').findAll('item')
    for item in items:
        process_item(item, site, db)
    process_feeds_recursive(feeds, db, index + 1)

def process_item(item, site, db):
    title = get_clean_text(item.find('title')) if item.find('title') else 'No Title'
    description = get_clean_text(item.find('description')) if item.find('description') else 'No Description'
    pub_date = find_pub_date(item)
    link = item.find('link').text if item.find('link') else 'No Link'
    db['alerts'].update_one({"link": link}, {"$setOnInsert": {"site": site, "title": title, "description": description, "pub_date": pub_date, "link": link, "last_checked": datetime.now()}}, upsert=True)

def get_clean_text(element):
    if element and element.text:
        return ' '.join(BeautifulSoup(element.text, 'lxml').get_text().split())
    return ""

def find_pub_date(item):
    for field in ['pubDate', 'dc:date']:
        date_str = item.find(field)
        if date_str:
            return dateutil.parser.parse(date_str.text)
    return None
