from flask import Flask, request, jsonify, send_file
import os
from flask_cors import CORS, cross_origin
from flask.helpers import send_from_directory
import fitz
import re
import pandas as pd
import tempfile

app = Flask(__name__, static_folder="ocr-frontend/build", static_url_path='')
CORS(app)

app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_data(text):
    data = {
        "Transaction Status": re.search(r"Transaction\s+status\s*[:\-]?\s*(.+)", text, re.IGNORECASE),
        "Employer's Code No": re.search(r"Employer's\s+Code\s+No\s*[:\-]?\s*(\d+)", text, re.IGNORECASE),
        "Employer's Name": re.search(r"Employer's\s+Name\s*[:\-]?\s*(.+)", text, re.IGNORECASE),
        "Challan Period": re.search(r"Challan\s+Period\s*[:\-]?\s*(.+)", text, re.IGNORECASE),
        "Challan Number": re.search(r"Challan\s+Number\s*[:\-]?\s*(\d+)", text, re.IGNORECASE),
        "Challan Created Date": re.search(r"Challan\s+Created\s+Date\s*[:\-]?\s*(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})", text, re.IGNORECASE),
        "Challan Submitted Date": re.search(r"Challan\s+Submitted\s+Date\s*[:\-]?\s*(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})", text, re.IGNORECASE),
        "Amount Paid": re.search(r"Amount\s+Paid\s*[:\-]?\s*(.+)", text, re.IGNORECASE),
        "Transaction Number": re.search(r"Transaction\s+Number\s*[:\-]?\s*(\d+)", text, re.IGNORECASE)
    }

    for key in data:
        if data[key]:
            data[key] = data[key].group(1).strip()
        else:
            data[key] = None

    return data

def write_data_to_excel(data):
    df = pd.DataFrame(data)
    temp_excel_file = os.path.join(tempfile.gettempdir(), 'extracted_data.xlsx')
    df.to_excel(temp_excel_file, index=False)
    return temp_excel_file
 
@app.route('/upload', methods=['POST'])
@cross_origin()
def upload_file():
    uploaded_files = request.files.getlist("file")
    if not uploaded_files:
        return jsonify({"error": "No files uploaded"}), 400

    all_extracted_data = []
    for file in uploaded_files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        text = extract_text_from_pdf(file_path)
        extracted_data = extract_data(text)
        all_extracted_data.append(extracted_data)

    excel_file_path = write_data_to_excel(all_extracted_data)

    for file in uploaded_files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        os.remove(file_path)

    return send_file(excel_file_path, as_attachment=True)

@app.route('/')

def server():
    return send_from_directory(app.static_folder, 'index.html')
if __name__ == '__main__':
    app.run(debug=True)
