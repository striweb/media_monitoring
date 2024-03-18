from datetime import datetime
import traceback
import dateutil.parser
import re

app = Flask(__name__)

	@@ -23,7 +23,7 @@ def load_config_from_url(url):
config_url = 'http://striweb.com/media_monitoring_info.json'
config = load_config_from_url(config_url)
sites = config['sites']
keywords = [keyword.lower() for keyword in config['keywords']]

def find_pub_date(item):
    for field in ['pubDate', 'dc:date']:
	@@ -41,15 +41,15 @@ def get_clean_text(element):
def check_words_recursive(words, keywords, index=0):
    if index >= len(words):
        return False
    word = words[index].lower()
    if word in keywords:
        print(f"Keyword '{word}' found.")
        return True
    return check_words_recursive(words, keywords, index + 1)

def process_items_recursive(items, site, index=0):
    if index >= len(items):
        return
    item = items[index]
    title = get_clean_text(item.find('title')) if item.find('title') else 'No Title'
    description = get_clean_text(item.find('description')) if item.find('description') else 'No Description'
	@@ -59,7 +59,6 @@ def process_items_recursive(items, site, index=0):
    content = f"{title} {description}".lower()
    words = content.split()

    if check_words_recursive(words, keywords):
        print(f"Inserting/updating MongoDB for title: {title}")
        collection.update_one(
	@@ -76,18 +75,18 @@ def process_items_recursive(items, site, index=0):
            upsert=True
        )

    process_items_recursive(items, site, index + 1)

def process_feeds_recursive(feeds, index=0):
    if index >= len(feeds):
        return
    site = feeds[index]
    print(f"Processing feed: {site}")
    response = requests.get(site)
    soup = BeautifulSoup(response.content, 'xml')
    items = soup.findAll('item')
    process_items_recursive(items, site)
    process_feeds_recursive(feeds, index + 1)

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
