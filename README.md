# 🚀 Organization Management Backend – Internship Assignment

This project is a backend service for managing organizations and admin users using **FastAPI** and **MongoDB**.  
It includes authentication using JWT and secure protected routes for update & delete operations.

---

## 📍 Features

| Feature | Description |
|--------|-------------|
| Create Organization | Creates an organization & admin with secure password hashing |
| Admin Login | JWT-based login to access protected endpoints |
| Update Organization | Update organization name or admin details (Token required) |
| Delete Organization | Delete organization & related admin data (Token required) |
| MongoDB Health Check | Check MongoDB connection status |
| Interactive API Docs | Swagger UI available at `/docs` |

---

## 🛠️ Tech Stack

- **Python 3.12**
- **FastAPI**
- **MongoDB Community Edition**
- **Motor (Async MongoDB driver)**
- **Uvicorn**
- **bcrypt** (password hashing)
- **JWT Auth using python-jose**

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository

```bash
git init
2️⃣ Create Virtual Environment
bash
Copy code
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Mac/Linux
3️⃣ Install Requirements
bash
Copy code
pip install -r requirements.txt
4️⃣ Create .env file
env
Copy code
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=org_master_db
JWT_SECRET_KEY=some_super_secret_key
5️⃣ Run FastAPI Server
bash
Copy code
uvicorn main:app --reload
Open in browser:

👉 http://127.0.0.1:8000/docs

🔐 Authentication Flow (JWT)
1️⃣ Create organization → POST /org/create
2️⃣ Admin Login → POST /admin/login
3️⃣ Copy access_token
4️⃣ Click Authorize in /docs
5️⃣ Paste token to access:

PUT /org/update

DELETE /org/delete


🧪 Testing Guide (/docs)
Swagger UI provides:

✔ Example Request Bodies
✔ Curl Commands
✔ Token Authorization Button
✔ Response Details & Error Messages










👤 Developer Details
Name: Ambarapu Ganavarun

Education: B.Tech CSE

Role: Backend Intern (Assignment Project)

Skills Used: FastAPI, Python, MongoDB, JWT, bcrypt
