# Micro-Service Implementation 
**Subject:** Information Management & Retrieval  
**Author:** Chai Yee Pei  
**Institution:** Peninsula College Georgetown  
**Programme:** BSc (Hons) Computer Science (Software Engineering)

---

## Overview  
This project is a micro-service backend API developed using Flask, SQLAlchemy, and Marshmallow.

The micro-service manages data related to:   
- Trail
- User
- Location
- RouteType
- Difficulty
- TrailTag
- Waypoint
- Activity
- Photo
- UserList

The API provides structured endpoints for efficient information retrieval, with validation, error-handling, and clean JSON responses.

---

## Key Features  

### CRUD Functionalities  
- All major modules include Create, Read, Update, Delete operations.  
- Responses remove internal database IDs.

### Input Validation & Data Integrity  
- Visibility accepts only: `Public`, `Private`, `Friends`  
- Difficulty accepts only: `Easy`, `Moderate`, `Hard`  
- Route type accepts only: `Loop`, `Out & Back`, `Point to Point`  
- Clear error messages for invalid inputs.

### Data Privacy Measures  
- Response objects exclude internal IDs such as:  
  - `user_id`  
  - `trail_id`  
  - `location_id`  
- Returns user-friendly fields (`user_name`, `trail_name`, `location_name`).

### Swagger UI Integration  
- Built-in documentation to test endpoints.  
- Shows request and response structures clearly.

---


## Technologies Used  
- Python 3  
- Flask  
- Flask-SQLAlchemy  
- Marshmallow  
- Azure Data Studio 
- Swagger UI

---

## How to Run  

### 1. Install dependencies  
```bash
pip install -r requirements.txt
```

### 2. Build or initialize the database
```bash
python build_database.py
```

### 3. Start the microservice
```bash
python app.py
```

### 4. Access the API
Once the server starts, Flask will show the URLs where your service is running.
Example output:
```bash
Running on http://127.0.0.1:8001
Running on http://192.168.1.58:8001
```
Use the displayed link (commonly http://127.0.0.1:8001) to access the API endpoints.

---

## API Modules Summary

### **Activity Service**
- Create, update, delete, and list activities  
- Supports multiple photo uploads  
- Validates:
  - Visibility (`Public`, `Private`, `Friends`)
- Returns clean output:
  - `user_name`
  - `trail_name`
  - `photos`
  - `visibility`


### **User List Service**
- Create and manage user-defined lists  
- Allows attaching trails to lists  
- Validates visibility (`Public`, `Private`, `Friends`)  
- JSON responses do **not** expose internal IDs  


### **Trail Service**
- Manage trail information
- Validates:
  - Difficulty (`Easy`, `Moderate`, `Hard`)
  - Route Type (`Loop`, `Out & Back`, `Point to Point`)
- Returns only `location_name` instead of full location object  


### **Authentication Service**
- Uses external API for login: https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users
- Request: POST JSON with email and password
- Responses:
  - 200 OK → returns username, email, access_token
  - 400 → missing email/password
  - 401 → invalid credentials
  - 500 → auth service error
- Passwords are not stored locally.

---

## Validation Rules

### **Visibility**
Public / Private / Friends


### **Difficulty**
Easy / Moderate / Hard


### **Route Type**
Loop / Out & Back / Point to Point

---

### **Clean JSON Output**
- All internal IDs removed  
- Names shown instead of numeric identifiers  

---

## Error Handling
- `abort(400)` → invalid input, uniqueness violations, or validation errors  
- `abort(404)` → resource not found  
- `abort(500)` → unexpected internal errors  
- Messages avoid exposing database internals or stack traces  
