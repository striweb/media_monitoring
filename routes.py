from flask import Blueprint, jsonify, render_template, request, current_app
from .utils import process_feeds_recursive, load_config_from_url, highlight_keywords
import bleach

main = Blueprint('main', __name__)

@main.route('/alerts')
def show_alerts():
    collection = current_app.db['alerts']
    page = int(request.args.get('page', 1))
    per_page = 20
    skip = (page - 1) * per_page
    search_query = request.args.get('search', '')
    query = {}
    if search_query:
        regex_pattern = f".*{search_query}.*"
        query = {"$or": [{"title": {"$regex": regex_pattern, "$options": "i"}}, {"description": {"$regex": regex_pattern, "$options": "i"}}]}
    alerts = collection.find(query).skip(skip).limit(per_page)
    total_alerts = collection.count_documents(query)
    total_pages = (total_alerts + per_page - 1) // per_page
    sanitized_alerts = [highlight_keywords(alert, current_app.db['config']['keywords']) for alert in alerts]
    return render_template('alerts.html', alerts=sanitized_alerts, total_pages=total_pages, current_page=page, search_query=search_query)

@main.route('/run-script')
def run_script():
    try:
        sites = load_config_from_url('https://striweb.com/media_monitoring_info.json')['sites']
        process_feeds_recursive(sites, current_app.db)
        return jsonify({"message": "The script was executed successfully!"})
    except Exception as e:
        return jsonify({"error": "An internal error occurred."})
