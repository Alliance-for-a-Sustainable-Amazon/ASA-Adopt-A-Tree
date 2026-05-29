# ASA Adopt A Tree 

## Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [System Architecture](#system-architecture)
4. [Setup Instructions](#setup-instructions)
5. [Database Structure](#database-structure)
6. [Authentication](#authentication)
7. [Core Functionality](#core-functionality)
8. [User Interfact](#user-interface)
9. [Deployment](#depolyment)
10. [Code Structure](#code-structure)
11. [References](#references)

## Project Overview 
Django web application for managing tree adoptions and donor contributions on an interactive map.

---

## Features
- Track donors, donations, and trees
- Manage tree adoption status
- Admin dashboard for data management

---

## System Architecture
### Technology Stack
- **Frontend:** HTML, CSS, JavaScript, Django templates, Google Maps API
- **Backend:** Django 6.0.2, Python 3.14.4
- **Database:** PostgreSQL 
- **Deployment:** Azure App Service, Azure database hosting, Wix Studio

### Architecture Visualization
Wix Studio Frontend 

Django REST API

PostgreSQL Database

Stripe Webhooks

---

## Setup Instructions
### Setup Prerequisites
- Python 3.14+
- Stripe CLI 1.41+ 
- Access to the Wix Studio website
- ngrok 3.39+ (optional)

### Backend Django Setup:
#### 1. Clone the repository:
```bash
git clone https://github.com/Alliance-for-a-Sustainable-Amazon/ASA-Adopt-A-Tree.git
cd adopt-a-tree
```
#### 2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate # Windows: venv/Scripts/activate
```
#### 3. Install backend dependencies:
```bash
pip install -r requirements.txt
```
#### 4. Set up environment variables:
```bash
cp .env.example .env
```
#### 5. Run migrations:
```bash
python manage.py migrate
```
#### 6. Create superuser:
```bash
python manage.py createsuperuser
```
#### 7. Run server:
```bash
python manage.py runserver
```

### Stripe Setup:
1. Create or log into your Stripe account through the Stripe dashboard
    - Make sure you enter the Testing Suite for development
2. Obtain Stripe API keys on the Stripe dashboard:
    - Secret Key
    - Publishable Key
3. Add the Secret Key to the `.env` file under `STRIPE_SECRET_KEY`
4. In a new terminal, start Stripe webhook:
```bash
stripe listen --forward-to localhost:8000/api/stripe-webhook
```
5. Copy the generated webhook secret and add it to the `.env` file under `STRIPE_WEBHOOK_SECRET`

### ngrok Setup (optional):
If doing local development and testing, you can use ngrok to host your Django localhost.
1. In a new terminal, start ngrok:
```bash
ngrok 8000
```
2. Copy the URL that appears in the terminal to update the Wix Studio API URL

### Wix Studio Setup:
1. Open the Wix Studio site
2. Enable Velo Dev mode
3. Configure the Backend API URL
    - Update the API URL in `treeApis.jsw` to point toward:
        - Local Development:
            - ngrok URL
        - Production:
            - Azure URL
4. Publish the site
---

## Database Structure
### Database Models
- **Tree:** The core model that contains information regarding each adoptable / adopted tree
- **Donor:** Keeps each user who has donated along with their total donation amount. Each user is tied to a unique email
- **Donation:** Represents tree adoptions containing information about the donation, the donor, and which tree was adopted

### Model Relationships
- **Tree &rarr; Donation:** One to one relationship (one tree can be related to one donation)
- **Donor &rarr; Donation:** One to many relationship (one donor can be related many donations)

### Key Implementation
- **UUID:** All models contain a UUID primary key for safety due to sensitive donor information

---

## Authentication
### Django Authentications
#### User Roles
- **Admin:** Full access to user management, database management, and Django admin panel

#### API Access and Permissions
- Enforced with:
    - **Function decorators (**`@api_view(['GET'])`**,** `@api_view(['POST'])`**):** Specifies which actions are allowed for each API view
    - `CORS_ALLOWED_ORIGINS`**:** States what websites are able to access the API views

#### Creating Admin User via Environment Variables
- Automated admin creation available:
    - `DJANGO_ADMIN_EMAIL` (defaults to 'admin@example.com')
    - `DJANGO_ADMIN_USER` (defaults to 'admin')
    - `DJANGO_ADMIN_PASSWORD` (required)
    - **Management Command:** `python manage.py create_admin`

### Google Cloud Authentication

### Stripe Authentication
---

## Core Functionality
### Backend Functionality
#### Tree Management
- Add, edit, and remove trees in the admin portal
    - Adoption status automatically managed by Stripe webhook
- Organized into sections:
    - Identifiers
    - Date Information
    - Adoption Status
    - Tree Information
    - Location Information
    - Study Information
    - Notes

#### Donor Management
- Add, edit, and remove donors in the admin portal
    - Automatically created and managed through Stripe webhook
- Organized into sections:
    - Identifiers
    - Donor Information

#### Donation Management
- Add, edit, and remove donations in the admin portal
    - Automatically created through Stripe webhook
- Organized into sections:
    - Identifiers
    - Donation Date and Expiration
    - Donation Information
    - Donor Information
    - Tree Adopted
    - Notes

### Frontend Functionality
#### Map

---

## User Interface
### Frontend Interface
- **Interactive Google Map:** 
- **Tree Popups:**
- **Stripe Payment Link:**

### Backend Interface
- **Admin Panel:**
    - Tables for:
        - Trees
        - Donors
        - Donations
    - Search and filter functionality for each table
    - Ability to add new admin user accounts

---

## Deployment
### Azure
- **Prerequisites:** Azure account, Azure CLI, Git, Python 3.14+
- **Environment Variables:** `DJANGO_SECRET_KEY`, `DJANGO_SETTINGS_MODULE`, `DJANGO_DEBUG`, `DJANGO_ADMIN_EMAIL`, `DJANGO_ADMIN_USER`, `DJANGO_ADMIN_PASSWORD`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- **Steps:**
    - Create resources (resource group, app service plan, PostgreSQL server, database, web app)
    - Configure environment variables
    - Deploy code via Git
    - Authentication setup: migration, admin creation, permission setup
- **Database:** Azure PostgreSQL Flexible Server (connection pooling, SSL, env-based config)

### Google Cloud
- **Prerequisites:** Google Cloud account
- **Steps:**

### Wix Studio
- **Prerequisites:** Wix Studio account
- **Steps:**
    - Create frontend elements (iFrame for map, popup, Velo page code, Wix backend JSW file)
    - 

### Stripe
- **Prerequisites:** Stripe account
- **Steps:**

---

## Code Structure
### Backend
- `trees/`: Main app (models, views, admin, templates, static, management commands)
- `adopt_a_tree`: Project settings (development and Azure)

### Frontend
- `treeApis.jsw`: 
- Home page code:
--- 

## Coding Standards


---

## References
TBD