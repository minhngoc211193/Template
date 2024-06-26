# OPES INSURANCE BALANCE EXTRACTION
This service is for extracting information from loan payment schedules to calculate insured balance.

Input/Output
---

Input: 
- Insurance event date: inputted string
- Loan payment schedule: pdf file
- Credit institutions: string: VPB/FEC/MAFC

Output:
- Insured balance, insured interest, insured principal

Structure
---
- app.py: running POC web-portal UI for demo
- test.py: running unit tests

How to run
---
1. Download the EasyOCR `latin_g2.pth` and `craft_mlt_25k.pth` models fromm https://jaided.ai/easyocr/modelhub/ and save them in the `./model` folder
2. Run `pip install requirements.txt` to install necessary packages
3. Run `python app.py` to run the application

Export project to a Stand alone
---
To export this project to a stand alone:
1. Run `pyinstaller opes_ocr.spec`
2. Find the `opes_ocr.exe` in the folder `disk\opes_ocr\opes_ocr.exe`