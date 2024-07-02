from flask import Flask, render_template, request, redirect, url_for
import os, webbrowser, threading, json
from utils import version
from utils.process import get_results_pdf
from time import time
from datetime import datetime

app = Flask(__name__)
app.static_folder = 'static'

LOG_FILE_PATH = 'static/process.txt'

def log_submission(file_id, page, requested_date, interest, principal, insurance_balance, results):
    with open(LOG_FILE_PATH, 'a') as file:
        record = f"{datetime.now()}, {file_id}, {page}, {requested_date}, {interest}, {principal}, {insurance_balance}, {json.dumps(results)}\n"
        file.write(record)
    return record

def update_accuracy_log(file_id, accuracy):
    lines = []
    updated = False
    with open(LOG_FILE_PATH, 'r') as file:
        lines = file.readlines()
    
    for i in range(len(lines)):
        if file_id in lines[i]:
            parts = lines[i].strip().split(", ")
            if len(parts) == 8:  # Ensure it is the correct line with results
                # Append accuracy to the line
                parts.append(f"accuracy: {accuracy}")
                lines[i] = ", ".join(parts) + "\n"
                updated = True
                break
    
    if updated:
        with open(LOG_FILE_PATH, 'w') as file:
            file.writelines(lines)
    else:
        # If not found, you can decide to add new entry or handle differently
        print(f"Record for file_id {file_id} not found.")

@app.template_filter('format_number')
def format_number(value):
    """Format a number with commas as thousands separators."""
    return f"{value:,}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if request.method == 'POST':
        pdf = request.files['pdf']
        requested_date = request.form['text']
        pdf_path = "temp/input_file.pdf"
        pdf.save(pdf_path)

        print("received requested date: ", requested_date)
        output_temp_file = os.path.join("static", "output_img.png")
        if os.path.isfile(output_temp_file):
            os.remove(output_temp_file)

        ocr_result = get_results_pdf(pdf_path, requested_date, inplace_img=True)
        json_results = {
            "insurance_balance": ocr_result["insurance"],
            "insurance_event_date": ocr_result["event_date"],
            "image_quality": ocr_result["image_quality"],
            "detail_inf": ocr_result["detail_inf"],
            "version": version,
        }
        insurance_event_date = datetime.strptime(json_results['insurance_event_date'], '%Y%m%d').strftime('%d/%m/%Y')
        page = ocr_result.get('page', '')
        interest = ocr_result.get('interest', '')
        principal = ocr_result.get('principal', '')
        log_submission(pdf_path, page, requested_date, interest, principal, ocr_result["insurance"], json_results)
        return render_template("result.html", time=time, result=json_results, insurance_event_date=insurance_event_date)

@app.route("/history")
def view_history():
    with open(LOG_FILE_PATH, 'r') as file:
        logs = file.readlines()
    return '<br>'.join(logs)

@app.route('/rate', methods=['POST'])
def rate():
    file_id = request.form.get('file_id')
    accuracy = request.form.get('accuracy')
    update_accuracy_log(file_id, accuracy)

    # Get updated results
    with open(LOG_FILE_PATH, 'r') as file:
        logs = file.readlines()
    result = None
    for log in logs:
        if file_id in log:
            result = log.strip().split(", ")
            break

    if result:
        json_results = json.loads(result[7])
        insurance_event_date = datetime.strptime(json_results['insurance_event_date'], '%Y%m%d').strftime('%d/%m/%Y')
        return render_template("result.html", time=time, result=json_results, insurance_event_date=insurance_event_date, feedback="Thank you for your feedback!")
    else:
        return "Error: File ID not found"

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(debug=True)
