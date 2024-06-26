"""
METRICS
Metric for evaluating performance of the model
By: quanvh11
"""

import numpy as np

def levenshtein_distance(s1, s2):
    """
    Computes the Levenshtein distance between two strings.
    
    Parameters:
    s1 (str): The first string.
    s2 (str): The second string.
    
    Returns:
    int: The Levenshtein distance between the two strings.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    # Distance matrix
    distances = np.zeros((len(s1) + 1, len(s2) + 1), dtype=int)

    # Initial values for the distance matrix
    for i in range(len(s1) + 1):
        distances[i][0] = i
    for j in range(len(s2) + 1):
        distances[0][j] = j

    # Compute distances
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i - 1] == s2[j - 1]:
                cost = 0
            else:
                cost = 1
            distances[i][j] = min(distances[i - 1][j] + 1,      # Deletion
                                  distances[i][j - 1] + 1,      # Insertion
                                  distances[i - 1][j - 1] + cost)  # Substitution

    return distances[len(s1)][len(s2)]

def character_error_rate(true_text, predicted_text):
    """
    Calculates the Character Error Rate (CER).
    
    Parameters:
    true_text (str): The ground truth text.
    predicted_text (str): The predicted text.
    
    Returns:
    float: The Character Error Rate.
    """
    distance = levenshtein_distance(true_text, predicted_text)
    return distance / len(true_text)

def word_error_rate(true_text, predicted_text):
    """
    Calculates the Word Error Rate (WER).
    
    Parameters:
    true_text (str): The ground truth text.
    predicted_text (str): The predicted text.
    
    Returns:
    float: The Word Error Rate.
    """
    true_words = true_text.split()
    predicted_words = predicted_text.split()
    distance = levenshtein_distance(true_words, predicted_words)
    return distance / len(true_words)
