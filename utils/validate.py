import re

def is_url(search_terms:str):
    return re.match(r'^https?://', search_terms)