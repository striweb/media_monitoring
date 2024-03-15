from bs4 import BeautifulSoup 
import requests
from pymongo import MongoClient

# MongoDB Connection
client = MongoClient('mongodb://localhost:27017/')
db = client['media_monitoring']
collection = db['alerts']

# RSS Feed URLs and Keywords
sites = ['https://www.maximbehar.com/bg/blog/rss']
keywords = ['Hot21', 'Behar']

for site in sites:
    response = requests.get(site)
    soup = BeautifulSoup(response.content, 'xml')  # Use 'xml' parser for RSS feeds
    items = soup.findAll('item')  # RSS feeds usually contain <item> elements for each entry

    for item in items:
        title = item.find('title').text
        # Use BeautifulSoup to parse the description and get text to remove HTML
        description_html = item.find('description').text
        description_text = BeautifulSoup(description_html, 'lxml').get_text()

        # Combine title and description for keyword search
        content = f"{title} {description_text}"

        for keyword in keywords:
            if keyword.lower() in content.lower():
                # Store in MongoDB - Adjusted to include more relevant fields
                collection.insert_one({
                    "site": site,
                    "keyword": keyword,
                    "title": title,
                    "description": description_text,  # Save cleaned description
                    "link": item.find('link').text  # Include link to the original article/post
                })
