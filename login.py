# login.py
import requests
from flask import request, jsonify

AUTH_URL = "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users"

def login():
    # Get JSON from incoming request
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "Missing email or password"}, 400

    # Send POST request to external auth service
    response = requests.post(AUTH_URL, json={"email": email, "password": password})

    if response.status_code == 200:
        try:
            return response.json(), 200
        except ValueError:
            return {"error": "Invalid JSON from auth server"}, 500
    elif response.status_code == 401:
        return {"error": "Invalid credentials"}, 401
    else:
        return {"error": "Authentication service error"}, 500
