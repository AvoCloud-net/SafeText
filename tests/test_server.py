import pytest
from server import check_chatfilter

badwords = ["bastard", "idiot", "stupid"]
goodwords = ["bass", "idiotic"]

def test_no_badwords():
    input_str = "Hello, how are you?"
    results = check_chatfilter(input_str, badwords, goodwords)
    assert results == [] 

def test_direct_badword_match():
    input_str = "You are such an idiot!"
    results = check_chatfilter(input_str, badwords, goodwords)
    assert len(results) == 1
    assert results[0][0] == "idiot"
    assert results[0][1] == "idiot"
    assert results[0][2] == 0  

def test_similar_badword():
    input_str = "You are bastardo!"
    results = check_chatfilter(input_str, badwords, goodwords)
    assert len(results) == 1
    assert results[0][0] == "bastardo"  
    assert results[0][1] == "bastard" 
    assert results[0][2] > 0 

def test_goodword_filtering():
    input_str = "This bass is amazing!"
    results = check_chatfilter(input_str, badwords, goodwords)
    assert results == []

def test_multiple_badwords():
    input_str = "You idiot, bastard!"
    results = check_chatfilter(input_str, badwords, goodwords)
    assert len(results) == 2 
    flagged_words = [match[0] for match in results]
    assert "idiot" in flagged_words
    assert "bastard" in flagged_words
