from flask import Flask, jsonify
from bs4 import BeautifulSoup, CData
import requests
from pymongo import MongoClient
from datetime import datetime
import traceback
import dateutil.parser  # You might need to add 'python-dateutil' to your requirements.txt

app = Flask(__name__)

# MongoDB Connection
client = MongoClient('mongodb://mongodb:27017/')
db = client['media_monitoring']
collection = db['alerts']

# RSS Feed URLs and Keywords
sites = ['https://www.maximbehar.com/bg/blog/rss', 'https://www.dnes.bg/rss.php?today']
keywords = ['Hot21', 'Behar', 'влюбят']

def find_pub_date(item):
    # Try various fields for publication date
    for field in ['pubDate', 'dc:date']:
        date_str = item.find(field)
        if date_str:
            return dateutil.parser.parse(date_str.text)
    return None  # or return a default date

def get_description(item):
    # Handle both CDATA and regular text
    description = item.find('description')
    if description:
        if isinstance(description.contents[0], CData):
            return description.contents[0]
        return description.text
    return ""

@app.route('/run-script')
def run_script():
    try:
        for site in sites:
            response = requests.get(site)
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.findAll('item')

            for item in items:
                title = item.find('title').text
                description_text = get_description(item)
                pub_date = find_pub_date(item)
                link = item.find('link').text

                media_urls = [enclosure['url'] for enclosure in item.find_all('enclosure') if 'url' in enclosure.attrs]
                # You might want to extend this with additional logic for <media:content>

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
