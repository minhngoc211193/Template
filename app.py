from flask import Flask, render_template, request
import os, webbrowser, threading, json
from utils import version
from utils.process import get_results_pdf
from time import time
from datetime import datetime

app = Flask(__name__)
app.static_folder = 'static'

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

        return render_template("result.html", time=time, result=json_results, insurance_event_date=insurance_event_date)

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(debug=False)

import os
from flask import Flask, request
from datetime import datetime
import json

app = Flask(__name__)

# Đường dẫn đến file log
LOG_FILE_PATH = 'submission_logs.txt'

def log_submission(pdf_path, results):
    with open(LOG_FILE_PATH, 'a') as file:
        # Tạo bản ghi với thời gian, đường dẫn PDF và kết quả OCR
        record = f"{datetime.now()}, {pdf_path}, {json.dumps(results)}\n"
        file.write(record)

@app.route('/upload', methods=['POST'])
def upload():
    pdf = request.files['pdf']
    pdf_path = os.path.join('path/to/save', pdf.filename)
    pdf.save(pdf_path)

    # Giả sử làm OCR và lấy kết quả
    results = perform_ocr(pdf_path)

    # Ghi log vào file
    log_submission(pdf_path, results)

    return f"Uploaded and processed {pdf.filename}"

def perform_ocr(pdf_path):
    # Thực hiện xử lý OCR trên file PDF
    # Giả định trả về kết quả dưới dạng dict
    return {"text": "sample OCR text"}

if __name__ == '__main__':
    app.run(debug=True)

