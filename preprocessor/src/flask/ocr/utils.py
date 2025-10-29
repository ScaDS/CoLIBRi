import string

from rapidfuzz import fuzz


def get_numbers(text):
    """
    Get the numbers in a text in a sequential order they show up
    """
    number = ""
    for char in text:
        if char in string.digits + ".":
            number += char
    return number


def fuzzy_match(text, wordlist):
    """
    Fuzzily match a wordlist against a text
    :param text: string to find matches against
    :param wordlist: a list of words to find in the text
    :return: id of the word that matches
    """
    return_id = None
    if len(text) < 5:  # don't bother with really short texts
        return None
    for i, wordlist_word in enumerate(wordlist):
        # get correlation between the word and the text
        ratio = fuzz.partial_ratio(wordlist_word.lower(), text.lower())
        # if its better than 85%, assume a match
        if ratio >= 85:
            return_id = i
    return return_id
