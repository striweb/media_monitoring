from flask import Flask, jsonify
from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Adjust MongoDB Connection for Docker
client = MongoClient('mongodb://mongodb:27017/')
db = client['media_monitoring']
collection = db['alerts']

# RSS Feed URLs and Keywords
sites = ['https://www.maximbehar.com/bg/blog/rss']
keywords = ['Hot21', 'Behar']

@app.route('/run-script')
def run_script():
    try:
        for site in sites:
            response = requests.get(site)
            soup = BeautifulSoup(response.content, 'xml')  # Use 'xml' parser for RSS feeds
            items = soup.findAll('item')  # RSS feeds usually contain <item> elements for each entry

            for item in items:
                title = item.find('title').text
                description_html = item.find('description').text
                description_text = BeautifulSoup(description_html, 'lxml').get_text()

                # Extract the publication date
                pub_date = item.find('pubDate').text

                # Attempt to extract media content (e.g., images, videos) from <enclosure> tags
                media_urls = []
                for enclosure in item.find_all('enclosure'):
                    if 'url' in enclosure.attrs:
                        media_urls.append(enclosure['url'])

                content = f"{title} {description_text}"

                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        copy_date = datetime.now()  # Current date and time
                        # Store in MongoDB with pubDate, media URLs, and copy date
                        collection.insert_one({
                            "site": site,
                            "keyword": keyword,
                            "title": title,
                            "description": description_text,  # Cleaned description
                            "link": item.find('link').text,  # Article/post link
                            "pub_date": pub_date,  # Publication date
                            "media_urls": media_urls,  # Media URLs
                            "copy_date": copy_date  # Copy date
                        })

        # Return a response indicating successful execution
        return jsonify({"message": "Script ran successfully!"})
    except Exception as e:
        # Log the exception and return an error response
        app.logger.error(f"An error occurred: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
