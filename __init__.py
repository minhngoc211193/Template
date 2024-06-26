"""
Common functions
By: quanvh11
"""
import os
from itertools import groupby

version = '1.0.0'

def longest_constant_chain_with_indices(nums):
    max_length = 0
    start_index = 0
    end_index = 0
    
    for key, group in groupby(enumerate(nums), lambda x: x[1]):
        indices = [index for index, _ in group]
        chain_length = len(indices)
        if chain_length > max_length:
            max_length = chain_length
            start_index = indices[0]
            end_index = indices[-1]
    
    return max_length, start_index, end_index

def get_filename(file_path):
    file_name_with_ext = os.path.basename(file_path)
    file_name = os.path.splitext(file_name_with_ext)[0]
    return file_name