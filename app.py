from flask import Flask, jsonify, render_template, request
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import traceback
import dateutil.parser
import re

app = Flask(__name__)

client = MongoClient('mongodb://mongodb:27017/')
db = client['media_monitoring']
collection = db['alerts']

def load_config_from_url(url):
    response = requests.get(url, headers={'Accept-Charset': 'UTF-8'})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to load configuration from {url}")

config_url = 'http://striweb.com/media_monitoring_info.json'
config = load_config_from_url(config_url)
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

@app.route('/alerts')
def show_alerts():
    page = int(request.args.get('page', 1))
    per_page = 5
    skip = (page - 1) * per_page

    alerts = collection.find({}).skip(skip).limit(per_page)
    total_alerts = collection.count_documents({})
    total_pages = (total_alerts + per_page - 1) // per_page

    return render_template('alerts.html', alerts=list(alerts), total_pages=total_pages, current_page=page)

@app.route('/run-script')
def run_script():
    try:
        process_feeds_recursive(sites)
        return jsonify({"message": "Script ran successfully!"})
    except Exception as e:
        error_info = traceback.format_exc()
        app.logger.error(f"An error occurred: {e}\nDetails:\n{error_info}")
        return jsonify({"error": "An internal error occurred."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
