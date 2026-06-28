import os
import sys
import random
import requests

def get_user_data(user_id):
    # No docstring, missing validation
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()

def calculate_average(numbers):
    total=0
    for num in numbers:
        total += num
    return total / len(numbers)

def process_data(user_id):
    # No handling of exceptions, no input sanitization
    user = get_user_data(user_id)
    avg = calculate_average(user['scores'])
    print("Average score for", user['name'], "is", avg)
    # Potential SQL injection if used in a DB query (just for demonstration)
    sql = "SELECT * FROM users WHERE id = " + str(user_id)
    # This is a dummy line to show security issue
    return sql

def main():
    # Unused variable 'random' imported but never used
    data = process_data(123)
    print(data)

if __name__ == "__main__":
    main()