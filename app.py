from flask import Flask, jsonify, render_template, request
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import traceback
import dateutil.parser
import bleach
import re

app = Flask(__name__)

client = MongoClient('mongodb://mongodb:27017/')
db = client['media_monitoring']
collection = db['alerts']

def load_config_from_db():
    config = db['configurations'].find_one({"name": "default"})
    if config:
        return config
    else:
        raise Exception("Failed to load configuration from MongoDB")

config = load_config_from_db()
sites = config['sites']
keywords = [keyword.lower() for keyword in config['keywords']]

def find_pub_date(item):
    for field in ['pubDate', 'dc:date']:
        date_str = item.find(field)
        if date_str:
            return dateutil.parser.parse(date_str.text)
    return None

def get_clean_text(element):
    if element and element.text:
        soup = BeautifulSoup(element.text, 'lxml')
        return ' '.join(soup.get_text().split())
    return ""

def check_words_recursive(words, keywords, index=0):
    if index >= len(words):
        return False
    word = words[index].lower()
    if word in keywords:
        return True
    return check_words_recursive(words, keywords, index + 1)

def process_items_recursive(items, site, index=0):
    if index >= len(items):
        return
    item = items[index]
    title = get_clean_text(item.find('title')) if item.find('title') else 'No Title'
    description = get_clean_text(item.find('description')) if item.find('description') else 'No Description'
    pub_date = find_pub_date(item)
    link = item.find('link').text if item.find('link') else 'No Link'
    media_urls = [enclosure['url'] for enclosure in item.find_all('enclosure') if 'url' in enclosure.attrs]
    content = f"{title} {description}".lower()
    words = content.split()
    if check_words_recursive(words, keywords):
        collection.update_one(
            {"link": link}, 
            {"$setOnInsert": {
                "site": site,
                "title": title,
                "description": description,
                "pub_date": pub_date,
                "link": link,
                "media_urls": media_urls,
                "last_checked": datetime.now()
            }}, 
            upsert=True
        )
    process_items_recursive(items, site, index + 1)

def process_feeds_recursive(feeds, index=0):
    if index >= len(feeds):
        return
    site = feeds[index]
    response = requests.get(site)
    soup = BeautifulSoup(response.content, 'xml')
    items = soup.findAll('item')
    process_items_recursive(items, site)
    process_feeds_recursive(feeds, index + 1)

def highlight_keywords(text, keywords):
    for keyword in keywords:
        highlighted_keyword = f"<span class='highlight'>{keyword}</span>"
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        text = pattern.sub(highlighted_keyword, text)
    return text

@app.route('/alerts')
def show_alerts():
    page = int(request.args.get('page', 1))
    per_page = 20
    skip = (page - 1) * per_page
    search_query = request.args.get('search', '')
    query = {}
    if search_query:
        regex_pattern = f".*{search_query}.*"
        query = {"$or": [
            {"title": {"$regex": regex_pattern, "$options": "i"}},
            {"description": {"$regex": regex_pattern, "$options": "i"}}
        ]}
    alerts = collection.find(query).skip(skip).limit(per_page)
    total_alerts = collection.count_documents(query)
    total_pages = (total_alerts + per_page - 1) // per_page
    sanitized_alerts = []
    for alert in alerts:
        alert['description'] = highlight_keywords(alert.get('description', ''), keywords)
        alert['title'] = highlight_keywords(alert.get('title', ''), keywords)
        alert['description'] = bleach.clean(alert['description'], tags=['span'], attributes={'span': ['class']}, strip=True)
        alert['title'] = bleach.clean(alert['title'], tags=['span'], attributes={'span': ['class']}, strip=True)
        sanitized_alerts.append(alert)
    return render_template('alerts.html', alerts=sanitized_alerts, total_pages=total_pages, current_page=page, search_query=search_query)

@app.route('/run-script')
def run_script():
    try:
        process_feeds_recursive(sites)
        return jsonify({"message": "The script was executed successfully!"})
    except Exception as e:
        error_info = traceback.format_exc()
        app.logger.error(f"An error occurred: {e}\nDetails:\n{error_info}")
        return jsonify({"error": "An internal error occurred."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
