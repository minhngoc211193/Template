"""
TEXT ANALYSIS
Analyzing the text results extracted from the OCR model
By: quanvh11
"""
import pandas as pd
import copy
import re
from utils import longest_constant_chain_with_indices

def check_is_same_line(yt1, yb1, yt2, yb2, xb1=None, xb2=None, overlap_threshold=0.8):
    """Check if 2 data points is a same line
    if 2 data point overlaping more than overlap_threshold => in the same line
    cor1: list of [(x11, y11), (x12, y12),...(x14, y14)]: coordinates of the 1st data point
    cor2: list of [(x21, y21), (x22, y22),...(x24, y24)]: coordinates of the 2nd data point
    """
    if (xb1 is not None) and (xb2 is not None):
        if xb2 < xb1:
            # Nếu một box nằm trước box trước đó => đã chuyển sang line mới
            return 0
    overlap = min(yt1-yb2, yt2-yb1)
    if overlap < 0:
        return 0
    heigh_1 = yt1-yb1
    heigh_2 = yt2-yb2
    if heigh_1>0 and heigh_2>0:
        pct_overlap = overlap/(min(heigh_1, heigh_2))
        if pct_overlap >= overlap_threshold:
            return 1
        else:
            return 0
    else:
        print("There is a box that has heigh = 0")
        return None
    

def map_textboxes_to_lines(text_boxes):
    # Put the text boxes to lines
    lines = {}
    line = []
    pre_box = None
    line_id = 0
    for box_id, box in enumerate(text_boxes):
        if pre_box is None:
            line.append(box)
            pre_box = box 
            continue
        else:
            yt1 = pre_box[0][3][1]
            yb1 = pre_box[0][0][1]
            xb1 = pre_box[0][1][0]
            yt2 = box[0][3][1]
            yb2 = box[0][0][1]
            xb2 = box[0][0][0]
            is_same_line = check_is_same_line(yt1, yb1, yt2, yb2, xb1, xb2, overlap_threshold=0.6)
            if is_same_line:
                line.append(box)
            else:
                # Next line
                lines[line_id] = line
                line = [box]
                line_id += 1
            pre_box = box 
    return lines

def form_detection(lines):
    """
    Classifying the form of the payment schedule
    Form 1: columns orders: [date, to_pay, principal, interest, remain_principal]
    Form 2: columns orders: [date, principal, interest, to_pay, remain_principal]
    Solution: rule-based: check if found column names CLM => Form 2, otherwise, form 1
    Return:
        Fromtype:
            1: form 1
            2: form 2
    """
    formtype = 1
    ind = None
    for ind, line in enumerate(lines):
        line_str = "".join(line)
        count_clm = line_str.count("CLM")
        if count_clm >= 4:
            formtype = 2
            break
    return formtype, ind


def clean_numeric_text(t):
    numeric = ''.join(char for char in str(t) if char.isdigit())
    try:
        out = int(numeric)
    except:
        out = 0
    return out

def human_number(num):
    return "{:,}".format(int(num))

def table_reconstruction(text_boxes):
    """
    Reconstruct a table from text boxes collected from OCR models
    """
    # MAP TEXT BOXES TO LINES
    lines = map_textboxes_to_lines(text_boxes)
    text_lines = [[i[-2] for i in v] for _, v in lines.items()]

    # Extract additional information:
    additional_info = get_additional_information(text_lines)

    # Check Form type:
    formtype, pred_first_line_ind = form_detection(text_lines)
    if formtype == 2:
        # [date, principal, interest, to_pay, remain_principal]
        metadata_inds = (0, 2, 4)
        col_names = ["date", "principal_to_pay", "interest", "to_pay", "principal", "metadata"]
    else:
        # If formtype ==1
        # [date, to_pay, principal, interest, remain_principal]
        metadata_inds = (0, 3, 4)
        col_names = ["date", "to_pay", "principal_to_pay", "interest", "principal", "metadata"]

    # TABLE CONSTRUCTION
    # The table has the longest line in the 
    # list_len = [len(lines[i]) for i in range(len(lines))]
    # table_len, table_start, table_end = longest_constant_chain_with_indices(list_len)

    # 2024.06.07: thay đổi giải pháp tái tạo bảng dùng align theo text boxes
    standard_line, first_ind = None, None
    table_list = []
    for k, line_i in lines.items():
        if standard_line is not None:
            checked, aligned_line = align_a_line(line_i, standard_line)
            if checked>=4:
                table_list.append(aligned_line)

        if len(line_i)==5:
            if len(str(clean_numeric_text(line_i[0][-2])))>=7:
                if standard_line is None:
                    table_list.append(line_i)
                standard_line = line_i

        if len(table_list) == 0:
            first_ind = k

    # Add the first row if doable
    # First row thường bị lỗi không nhận diện được lãi phải trả =0
    # checked, aligned_line = align_a_line(lines[first_ind], standard_line)
    # if checked>=4:
    #     table_list.insert(0,aligned_line)
    # Nhiều bảng có first row không align được với phần còn lại của bảng 
    # => Force fill theo form
    if first_ind is not None:
        numeric_count_ind_date = len(str(clean_numeric_text(lines[first_ind][0][-2])))
        if (len(lines[first_ind]) == 4) and (numeric_count_ind_date>=7):
            if formtype ==2:
                interest_ind = 2
            else:
                interest_ind = 3
            x0 = standard_line[interest_ind][0][0][0]
            x1 = standard_line[interest_ind][0][1][0]
            y0 = lines[first_ind][0][0][0][1]
            y3 = lines[first_ind][0][0][3][1]
            interest_val = ([[x0, y0], [x1, y0], [x1, y3], [x0, y3]], "0", 0)
            to_insert_line = copy.copy(lines[first_ind])
            
            to_insert_line.insert(interest_ind, interest_val)
            table_list.insert(0, to_insert_line)
            
    # Select the table which has index from ithe range 
    # table_values = {k: [t[-2] for t in v]+[v] for k, v in lines.items() if table_start <= k <= table_end}
    get_text = lambda t: t[-2] if t is not None else t
    table_values = {k: [get_text(t) for t in v]+[v] for k, v in enumerate(table_list)}
    table = pd.DataFrame.from_dict(table_values,orient='index')

    # TABLE FORMATTING
    table = table.iloc[:, 0:6]
    table = table.set_axis(col_names, axis=1)
    return table, metadata_inds, additional_info

def clean_date_text(date):
    if date is not None:
        date_ = ''.join(char for char in str(date) if char.isdigit())
        year = date_[-4:]
        month = date_[-6:-4]
        day = date_[-8:-6]
        if len(day)<2:
            day = "0"+day
        out = year + month + day
    else:
        out = ""
    return out

def clean_table(table_inp):
    """
    Clean values in the constructed table, 
    Fix to best candidate values:
    E.g: for a date: 25*06/2024 => fix to 20240625
    """
    table = table_inp.copy()
    # convert date format to %y%m%d for easier filtering
    
    table["date"] = table["date"].apply(clean_date_text)
    table["prev_principal"] = table["principal"].shift(1)
    table["prev_metadata"] = table["metadata"].shift(1)
    table = table.fillna(0)

    table["prev_end_date"] = table["date"].shift(1)
    return table

# Extract insurance deposit balance
def get_insurance_balance(table, day):
    """
    This table is assump that the columns in the table has the structure of:
    [date (start), to_pay, principal_to_pay, interest, remain_principal]
    Args:
        table: pd.DataFrame
        day: string in %y%m%d of the date the insurance event occurs
    """
    table_ = table.copy()
    # Get the referenced date
    # Handle missing values (consider N/A as True for comparison)
    # 20240610: fix testcase 26_2
    condition1 = table_['prev_end_date'].isna() | (table_['prev_end_date'] <= day)
    condition2 = table_['date'].isna() | (table_['date'] > day)
    filtered_table = table_[condition1 & condition2]

    return filtered_table

def check_2box_align(box_i, box_j, threshold=5):
    """
    Check if 2 boxes are align:
    return: [is_left, is_center, is_right]
    """
    x0i = box_i[0][0]
    x1i = box_i[1][0]
    xci = (x0i+x1i)/2
    
    x0j = box_j[0][0]
    x1j = box_j[1][0]
    xcj = (x0j+x1j)/2

    left_delta = x0i - x0j
    right_delta = x1i - x1j 
    center_delta = xci - xcj
    
    return [ left_delta<=threshold, center_delta<=threshold, right_delta<=threshold]

def check_2line_align(line1, line2):
    """
    Check 2 lines have align in column-wise table or not
    line_: text boxes of a line
    return: number of text boxes in line1 align with text boxes in line2
    """
    line_align = 0
    for box_i in line1:
        box_i_coordinates = box_i[0]
        for box_j in line2:
            box_j_coordinates = box_j[0]
            alignment = check_2box_align(box_i_coordinates, box_j_coordinates, threshold=5)
            if sum(alignment):
                line_align += 1
                break
    return line_align

def align_a_line(line_to_align, standard):
    """
    align a new line to a standard line
    Align is defined as:
        - Add N/A value to unrecognized OCR value
        - Remove none-alignable value
    Input:
        line_to_align: list: line that need to align
    Output:
        aligned_line: list: aligned line
    """
    value_list = copy.copy(line_to_align)
    aligned_line = []
    is_align =0
    for box_i in standard:
        box_i_coordinates = box_i[0]
        is_box_i_matched = 0
        for ind, box_j in enumerate(value_list):
            box_j_coordinates = box_j[0]
            alignment = check_2box_align(box_i_coordinates, box_j_coordinates, threshold=5)
            if sum(alignment):
                aligned_line.append(box_j)
                is_align += 1
                is_box_i_matched = 1
                value_list.pop(ind)
                break
        
        # If unable to map with any box
        if not is_box_i_matched:
            aligned_line.append(None)
    return is_align, aligned_line

def image_quality_map(prob):
    if prob >= 0.7:
        return "good"
    if prob >= 0.6:
        return "fair"
    if prob >= 0.5:
        return "bad"
    return "very_bad"

def normalize_text(text):
    # Mapping of Vietnamese characters to English characters
    vietnamese_to_english = {
        'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a', 'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e', 'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o', 'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u', 'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'đ': 'd'
    }

    # Step 1: Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)

    # Step 2: Convert to lowercase
    text = text.lower()

    # Step 3: Map Vietnamese characters to English characters
    normalized_text = ''.join(vietnamese_to_english.get(char, char) for char in text)
    
    return normalized_text

def get_additional_information(text_lines):
    """
    Get additional details from the payment schedule
    """
    contract_id, soTienVay, thoiHanChoVay = None, None, None
    name, address, cmnd, cmnd_date = None, None, None, None

    def get_text_by_key(text_line, searching, result_ind=1, searching_ind=0):
        first_box = text_line[searching_ind]
        first_box_text = normalize_text(first_box)
        if searching in first_box_text:
            return text_line[result_ind]
        else:
            return None

    for line in text_lines:
        if contract_id is None:
            contract_id = get_text_by_key(line, "hop dong tin dung nay so", 1)
        if name is None:
            name = get_text_by_key(line, "ho ten", 1)
        if address is None:
            address = get_text_by_key(line, "dia chi", 1)
        if cmnd is None:
            cmnd = get_text_by_key(line, "cmnd so", 1)
            if cmnd is not None:
                cmnd_date = get_text_by_key(line, "cap ngay", result_ind=3, searching_ind=2)
        if soTienVay is None:
            soTienVay = get_text_by_key(line, "so tien vay")
        if thoiHanChoVay is None: 
            thoiHanChoVay = get_text_by_key(line, "thoi han cho vay")
    return {
        "borrower": {
            "name": name,
            "address": address, 
            "id_card": cmnd,
            "issued_date": cmnd_date
        },
        "contract":{
            "contract_id": contract_id,
            "loan_amount": soTienVay,
            "duration": thoiHanChoVay
        }
    }