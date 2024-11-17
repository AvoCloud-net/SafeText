import hashlib

def hash_string(string):
    hashed = hashlib.sha256(string.encode()).hexdigest()
    return hashed

input_string = input("Enter Text: ")

hashed_output = hash_string(input_string)
print(f"Hash: {hashed_output}")
