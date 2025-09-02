# SocietySyncERP 🏢

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)  
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12%2B-blue)](https://www.postgresql.org/)  
[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-orange)](https://streamlit.io/)  
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A **Smart Apartment ERP System** built with **Python, Streamlit, and PostgreSQL** to manage residential society operations seamlessly.  

**GitHub Repository:** [https://github.com/durgesh-v-shukla/SocietySync](https://github.com/durgesh-v-shukla/SocietySync)

---

## 📋 Table of Contents
- [Clone the Repository](#clone-the-repository)  
- [Overview](#overview)  
- [Features](#features)  
- [Prerequisites](#prerequisites)  
- [Setup & Running Instructions](#setup--running-instructions)  
- [Database Initialization](#database-initialization)  
- [Sequence Synchronization](#sequence-synchronization)  
- [Running the Application](#running-the-application)  
- [Live Database Viewer](#live-database-viewer)  
- [Project Structure](#project-structure)  
- [DBMS Concepts Demonstrated](#dbms-concepts-demonstrated)  
- [Screenshots](#screenshots)  
- [Contributing](#contributing)  
- [License](#license)

---

## 📌 Clone the Repository
To get started, clone the repository to your local machine:

```bash
git clone https://github.com/durgesh-v-shukla/SocietySync.git
cd SocietySync
````

---

## 🎯 Overview

**SocietySyncERP** is a robust apartment management solution designed for **administrators, owners, and tenants**. It centralizes society operations to save time, reduce errors, and improve communication.

---

## ✨ Features

* **Role-Based Access:** Admin, Owner, Tenant login with **bcrypt password hashing**.
* **User Management:** Add/view owners and tenants; auto-generate usernames and passwords.
* **Billing System:** Generate, filter, track bills with **status analytics**.
* **Complaint Management:** Submit, view, prioritize, and resolve complaints.
* **Visitor Logs:** Record and view visitor entries/exits with historical data.
* **Notifications:** Broadcast announcements with read-receipt tracking.
* **Polls & Voting:** Multi-option polls with real-time vote count and charts.

---

## 🛠️ Prerequisites

* **Python 3.9+**
* **PostgreSQL 12+**
* **pip** (Python package installer)
* **Git** (for cloning the repository)

---

## 🚀 Setup & Running Instructions

### **1️⃣ Install Dependencies and Setup Virtual Environment**

In **VS Code terminal**:

```bash
# Install required Python packages
pip install streamlit psycopg2-binary pandas plotly bcrypt python-dotenv

# Create a virtual environment
python -m venv societysync_env

# Activate the virtual environment
# Windows
societysync_env\Scripts\activate
# macOS/Linux
source societysync_env/bin/activate
```

Create a **.env** file in the project root:

```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/societysync
```

---

### **2️⃣ Initialize PostgreSQL Database**

In **Command Prompt** or terminal:

```bash
# Enter PostgreSQL shell
psql -U postgres

# Enter your password when prompted
# Create the database
CREATE DATABASE societysync;

# Exit psql
\q

# Apply schema and seed data
psql -U postgres -d societysync -f societysync_scheme.sql
psql -U postgres -d societysync -f societysync_data.sql
```

---

### **3️⃣ Synchronize Table Sequences**

In **pgAdmin4 query tool**, run the following queries to reset sequences:

```sql
-- Users
SELECT MAX(user_id) FROM users;
SELECT setval('users_user_id_seq', <max_user_id>);

-- Owners
SELECT MAX(owner_id) FROM owners;
SELECT setval('owners_owner_id_seq', <max_owner_id>);

-- Bills
SELECT MAX(bill_id) FROM bills;
SELECT setval('bills_bill_id_seq', <max_bill_id>);

-- Visitors
SELECT MAX(visitor_id) FROM visitors;
SELECT setval('visitors_visitor_id_seq', <max_visitor_id>);

-- Notifications
SELECT MAX(notification_id) FROM notifications;
SELECT setval('notifications_notification_id_seq', <max_notification_id>);

-- Polls
SELECT MAX(poll_id) FROM polls;
SELECT setval('polls_poll_id_seq', <max_poll_id>);

-- Votes
SELECT MAX(vote_id) FROM votes;
SELECT setval('votes_vote_id_seq', <max_vote_id>);

-- Complaints
SELECT MAX(complaint_id) FROM complaints;
SELECT setval('complaints_complaint_id_seq', <max_complaint_id>);

-- Poll Options
SELECT MAX(option_id) FROM poll_options;
SELECT setval('poll_options_option_id_seq', <max_option_id>);
```

---

### **4️⃣ Run SocietySyncERP App**

Make sure the **virtual environment is activated**.

```powershell
# Windows PowerShell
$env:DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/societysync"

# Run Streamlit app
streamlit run app.py --server.port=8502
```

Open your browser: `http://localhost:8502/`

---

### **5️⃣ Run Live Database Viewer**

In a **new terminal** (with virtual environment activated):

```powershell
# Set environment variable
$env:DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/societysync"

# Run live DB viewer
python live_database_viewer.py
```

Open your browser: `http://127.0.0.1:5000`

---

## 🗂️ Project Structure

```text
societysync-erp/
├── app.py
├── live_database_viewer.py
├── database.py
├── auth.py
├── admin_dashboard.py
├── owner_dashboard.py
├── tenant_dashboard.py
├── utils.py
├── societysync_scheme.sql
├── societysync_data.sql
├── requirements.txt
├── README.md
└── .env
```

---

## 🎓 DBMS Concepts Demonstrated

* **Schema Design & Normalization:** 3NF tables, foreign keys, cascading deletes
* **Constraints:** PRIMARY KEY, UNIQUE, NOT NULL, CHECK
* **Sequences:** SERIAL columns & manual sequence sync
* **SQL Queries:** CRUD, JOINs, aggregate functions
* **Transactions & ACID:** Autocommit, rollback on exceptions

---

## 🖼️ Screenshots

*Add your screenshots here for better visualization:*

![Login Page](screenshots/login.png)
![Dashboard](screenshots/dashboard.png)
![Visitor Logs](screenshots/visitor_logs.png)

---

## 🤝 Contributing

1. Fork the repository: [https://github.com/durgesh-v-shukla/SocietySync](https://github.com/durgesh-v-shukla/SocietySync)
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m "Add new feature"`)
4. Push to branch (`git push origin feature-name`)
5. Open a Pull Request

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

```

---

If you want, I can also **add badges for Python version, Streamlit version, PostgreSQL, and GitHub stars/forks** to make it look even more **GitHub-professional**.  

Do you want me to do that next?
```
