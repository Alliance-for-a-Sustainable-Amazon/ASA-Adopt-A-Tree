# ASA Adopt A Tree 

Django web application for managing tree adoptions and donor contributions on an interactive map.

---

## Features
- Track donors, donations, and trees
- Manage tree adoption status
- Admin dashboard for data management

---

## System Architecture
### Technology Stack
- Python
- Django
- PostgreSQL
- Azure

---

## Setup Instructions
### 1. Clone the repository:
```bash
git clone https://github.com/Alliance-for-a-Sustainable-Amazon/ASA-Adopt-A-Tree
cd adopt-a-tree
```
### 2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate # Windows: venv/Scripts/activate
```
### 3. Install dependencies:
```bash
pip install -r requirements.txt
```
### 4. Set up environment variables:
```bash
cp .env.example .env
```
### 5. Run migrations:
```bash
python manage.py migrate
```
### 6. Setup superuser:
```bash
python manage.py createsuperuser
```
### 7. Run server:
```bash
python manage.py runserver
```
