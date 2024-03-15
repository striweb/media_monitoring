from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/run-script')
def run_script():
    # Place your script code here or call it as a function
    # For demonstration, let's say your script returns a dictionary of data
    data = {"message": "Script ran successfully!"}
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
