from threading import Thread
from flask import Flask

app = Flask(__name__)

def run_script_background():
    # Your script's code here or call to main script function
    pass  # Placeholder for your actual code

@app.route('/start-task')
def start_task():
    thread = Thread(target=run_script_background)
    thread.start()
    return "Task started in the background!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
