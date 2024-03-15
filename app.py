from flask import Flask, jsonify
from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
from datetime import datetime
import traceback

app = Flask(__name__)

# MongoDB Connection
client = MongoClient('mongodb://mongodb:27017/')
db = client['media_monitoring']
collection = db['alerts']

# RSS Feed URLs and Keywords
sites = ['https://www.maximbehar.com/bg/blog/rss', 'https://www.news24sofia.eu/feed/']
keywords = ['Hot21', 'Behar']

@app.route('/run-script')
def run_script():
    try:
        for site in sites:
            response = requests.get(site)
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.findAll('item')

            for item in items:
                title = item.find('title').text
                description_html = item.find('description').text
                description_text = BeautifulSoup(description_html, 'lxml').get_text()
                pub_date = item.find('pubDate').text
                link = item.find('link').text

                media_urls = [enclosure['url'] for enclosure in item.find_all('enclosure') if 'url' in enclosure.attrs]

                content = f"{title} {description_text}"

                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        copy_date = datetime.now()
                        # Use description as a unique identifier
                        collection.update_one(
                            {"description": description_text},
                            {"$setOnInsert": {
                                "site": site,
                                "keyword": keyword,
                                "title": title,
                                "pub_date": pub_date,
                                "link": link,
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
