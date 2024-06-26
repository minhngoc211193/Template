"""
Unit tests for the insurance extraction model
Test date: 20240527
Function to test: get_results_image
Features: trích xuất dư nợ bảo hiểm trên file in dọc, mẫu 1 (tên cột rõ ràng, 5 cột), không hỗ trợ lịch trả nợ nhiều trang
By: quanvh11
"""
import os
import pandas as pd
from utils.pdf import pdf_page_to_image

# Function to test
from utils.process import get_results_image


tmp_folder = "temp\\test"
test_data_folder = "data" #"test_data\\pdf_files"
zoom = 2

# Load testcases
testcases = pd.read_csv("test_data\\testcases\\testcases.csv")
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

    # get test_image
    for page in pages:
        print(f"\nTESTING IN FILE {file} PAGE {page}")
        page = int(page)
        # Extract the image from the pdf
        image_path = os.path.join(tmp_folder, str(file)+"_"+str(page)+".png")
        pdf_path   = os.path.join(test_data_folder, str(file)+".pdf")
        
        if not os.path.isfile(image_path):
            # Nếu chưa có file thì trích xuất từ pdf, nếu có rồi thì thôi
            pdf_page_to_image(pdf_path, page, image_path, zoom)

        # Perform OCR and get the results
        # results = get_results_image(image_path, str(requested_date), save_image=False)
        try:
            results = get_results_image(image_path, str(requested_date), save_image=False)
        except:
            results = None

        # Show results
        if results is None:
            msg = f"Testcase file {file} pages {page} FAIL IN EXTRACT INFORMATION"
            is_extracted = False
        else:
            # Predicted results
            p_interest = int(results["insurance"]["interest"])
            p_principal = int(results["insurance"]["principal"])
            if p_interest == interest:
                if p_principal == principal:
                    msg = f"Testcase file {file} pages {page} PASS; interest: {interest}, principal: {principal}"
                else:
                    msg = f"Testcase file {file} pages {page} FAIL IN PRINCIPAL; principal true: {principal}, predicted: {p_principal}"
            else:
                if p_principal == principal:
                    msg = f"Testcase file {file} pages {page} FAIL IN INTEREST; true interest: {interest}, predicted: {p_interest}"
                else:
                    msg = f"Testcase file {file} pages {page} FAIL IN BOTH INTEREST AND PRINCIPAL; principal true - pred: {principal} - {p_principal}; interest {interest} - {p_interest}"
            is_extracted = True
             
        msgs.append(msg)
        print(msg)

        # If results are extracted => no need to test with the next page
        if is_extracted:
            break

print("\n"*5)
print("FULL RESULTS")
for i in msgs:
    print(i)