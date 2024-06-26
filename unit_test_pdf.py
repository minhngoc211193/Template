"""
Unit tests for the insurance extraction model
Test date: 20240531
Function to test: get_results_pdf
Features: trích xuất dư nợ bảo hiểm trên file in dọc/ngang, mẫu (1, 2), hỗ trợ file pdf nhiều trang, input dạng file pdf
By: quanvh11
"""

import os
import pandas as pd

# Function to test
from utils.process import get_results_pdf

tmp_folder = "temp\\test"
test_data_folder = "test_data\\pdf_files"
zoom = 2

# Load testcases
testcases = pd.read_csv("test_data\\testcases\\testcases_pdf.csv")
testcases = testcases[testcases["principal"].notnull()]
testcases[["requested_date", "interest", "principal"]] = testcases[["requested_date", "interest", "principal"]].astype(int)

# loop over each testcase
msgs = []
for index, row in testcases.iterrows():
    file = row["file_id"]
    pages = str(row["page"]).split(",")
    requested_date = row["requested_date"]
    interest = row["interest"]
    principal = row["principal"]

    print(f"\nTESTING IN FILE {file}")
    pdf_path = os.path.join(test_data_folder, str(file)+".pdf")

    # Perform OCR and get the results
    results = get_results_pdf(pdf_path, str(requested_date), save_image=False)

    # Show results
    if results is None:
        msg = f"Testcase {index} file {file} pages FAIL IN EXTRACT INFORMATION"
        is_extracted = False
    else:
        # Predicted results
        p_interest = int(results["interest"])
        p_principal = int(results["principal"])
        if p_interest == interest:
            if p_principal == principal:
                msg = f"Testcase {index} file {file}: PASS; interest: {interest}, principal: {principal}"
            else:
                msg = f"Testcase {index} file {file}: FAIL IN PRINCIPAL; principal true: {principal}, predicted: {p_principal}"
        else:
            if p_principal == principal:
                msg = f"Testcase {index} file {file}: FAIL IN INTEREST; true interest: {interest}, predicted: {p_interest}"
            else:
                msg = f"Testcase {index} file {file}: FAIL IN BOTH INTEREST AND PRINCIPAL; principal true - pred: {principal} - {p_principal}; interest {interest} - {p_interest}"
        is_extracted = True
            
    msgs.append(msg)
    print(msg)
    
print("\n"*5)
print("FULL RESULTS")
for i in msgs:
    print(i)