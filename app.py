from flask import Flask, jsonify
from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
from datetime import datetime
import traceback
import dateutil.parser

app = Flask(__name__)

client = MongoClient('mongodb://mongodb:27017/')
db = client['media_monitoring']
collection = db['alerts']

# Function to load configuration from a JSON URL
def load_config_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to load configuration from {url}")

# Load sites and keywords from the JSON URL
config_url = 'http://striweb.com/media_monitoring_info.json'
config = load_config_from_url(config_url)
sites = config['sites']
keywords = config['keywords']

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

@app.route('/run-script')
def run_script():
    try:
        for site in sites:
            response = requests.get(site)
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.findAll('item')

            for item in items:
                title_element = item.find('title')
                title = get_clean_text(title_element) if title_element else 'No Title'

                description_element = item.find('description')
                description_text = get_clean_text(description_element) if description_element else 'No Description'

                pub_date = find_pub_date(item)
                
                link_element = item.find('link')
                link = link_element.text if link_element else 'No Link'

                media_urls = [enclosure['url'] for enclosure in item.find_all('enclosure') if 'url' in enclosure.attrs]

                content = f"{title} {description_text}"

                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        copy_date = datetime.now()
                        collection.update_one(
                            {"link": link},
                            {"$setOnInsert": {
                                "site": site,
                                "keyword": keyword,
                                "title": title,
                                "pub_date": pub_date if pub_date else datetime.now(),
                                "description": description_text,
                                "media_urls": media_urls,
                                "copy_date": copy_date
                            }},
                            upsert=True
                        )

        return jsonify({"message": "Script ran successfully!"})
    except Exception as e:
        error_info = traceback.format_exc()
        app.logger.error(f"An error occurred: {e}\nDetails:\n{error_info}")
        return jsonify({"error": "An internal error occurred."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
