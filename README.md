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
Django web application for managing tree adoptions and donor contributions on an interactive map hosted through Wix Studio. The frontend allows donors to view a variety of trees within the Alliance for a Sustainable Amazon's property as well as adopt them for one year. The backend allows administrators to view, add, edit, and remove trees and donations from the database. 

**Important:** Although this repository only contains the Django app service, the following README file documents the entire project. The final product can be found on the [official Alliance for a Sustainable Amazon website](https://www.sustainableamazon.org/reforestation).

---

## Features
### Backend
- Django:
    - Track donors, donations, and trees
    - Manage tree adoption status
    - Admin dashboard for data management
- Wix Studio:
    - Obtain basic information about all trees or detailed information about individual trees
    - Create Stripe checkout sessions

### Frontend
- View tree locations on interactive map
- Access specific tree data (name, diameter at breast height, height, tag number, image)
- Adopt trees and view already adopted trees

---

## System Architecture
### Technology Stack
- **Frontend:** HTML, CSS, JavaScript, Django templates, Google Maps API, Stripe payment links
- **Backend:** Django 6.0.2, Python 3.14.4, Wix Studio backend
- **Database:** PostgreSQL 
- **Deployment:** Azure App Service, Azure database hosting, Wix Studio, Stripe

### Architecture Visualization
Wix Studio Frontend 

Wix Studio Backend      Stripe Webhooks

Django REST API

PostgreSQL Database

---

## Setup Instructions
**Important:** These setup explinations pertain to local development and testing. For information on how to configure each part for deployment, see [Deployment](#deployment).

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
2. Obtain Stripe secret key on the dashboard
3. Add the secret key to the `.env` file under `STRIPE_SECRET_KEY`
4. Open the Developer tab
5. Create a new webhook:
    - Set the URL: `your-local-or-production-link/api/stripe-webhook/`
    - Copy the webhook signing secret
6. Add the webhook signing secret to the `.env` file under `STRIPE_WEBHOOK_SECRET`

### Wix Studio Setup:
1. Open Wix Studio site
2. Enable Velo Dev mode
3. Duplicate the current page containing the map
4. Make the duplicated page unindexable and set the set the URL to some random string
3. Configure the Backend API URL:
    - Update `ADD_VAR_NAME_HERE` in `treeApis.jsw` to point toward hosting service URL (ngrok, etc)
4. Publish site

### ngrok Setup (optional):
**Important:** Although ngrok is marked as optional, some form of hosting is necessary to allow Wix Studio and Stripe to access the localhost.

1. In a new terminal, start ngrok:
```bash
ngrok 8000
```
2. Copy the URL that appears in the terminal and update `ADD_VAR_NAME_HERE` in `treeApis.jsw` on Wix Studio
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
    - `DJANGO_API_KEY`**:** Prevents API views from being accessable without providing a secret key

#### Creating Admin User via Environment Variables
- Automated admin creation available:
    - `DJANGO_ADMIN_EMAIL` (defaults to 'admin@example.com')
    - `DJANGO_ADMIN_USER` (defaults to 'admin')
    - `DJANGO_ADMIN_PASSWORD` (required)
    - **Management Command:** `python manage.py create_admin`

### Google Cloud Authentication
- Enforced with:
    - **API restrictions:** Maps Javascript API, Maps Static API
    - **Website restrictions:** Google Map API can only be called by the provided website urls

### Stripe Authentication
- Enforced with:
    - **Secret Keys:** `STRIPE_WEBHOOK_SECRET`, `STRIPE_SECRET_KEY`
    - **Stripe Header:** Stripe webhooks provide a secret header to prevent data from being edited or accessed by outside sources
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
- Move the map around and see the surrounding area in satellite view
- See exact locations of pins on the map

#### Popup
- View detailed tree data as well as an image of the tree
- Button to open the adoption checkout session if adoptable, donor name if not

#### Stripe Checkout
- Pricing information
- Terms and Conditions
- Boxes to fill out payment information

---

## User Interface
### Backend Interface
- **Admin Panel:**
    - Tables for:
        - Trees
        - Donors
        - Donations
    - Search and filter functionality for each table
    - Ability to add new admin user accounts

### Frontend Interface
- **Wix Studio:**
    - Interactive Google Map
    - Tree popups
- **Stripe Checkout:**
    - Checkout session with payment information
    - Payment result page (redirected to Wix Studio)

---

## Deployment
### Azure
- **Prerequisites:** Azure account, Azure CLI, Git, Python 3.14+
- **Environment Variables:** `DJANGO_SECRET_KEY`, `DJANGO_API_KEY`, `DJANGO_SETTINGS_MODULE`, `DJANGO_DEBUG`, `DJANGO_ADMIN_EMAIL`, `DJANGO_ADMIN_USER`, `DJANGO_ADMIN_PASSWORD`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `AZURE_BLOB_STORAGE`, `AZURE_BLOB_CONTAINER`, `AZURE_CONNECTION_STRING`
- **Steps:**
    - Create resources (resource group, app service plan, PostgreSQL server, database, web app)
    - Configure environment variables
    - Deploy code via Git
    - Authentication setup: migration, admin creation, permission setup
- **Database:** Azure PostgreSQL Flexible Server (connection pooling, SSL, env-based config)

### Google Cloud
- **Prerequisites:** Google Cloud account
- **Steps:**
    - Configure restrictions:
        - API restrictions: Maps JavaScript API, Maps Static API
        - Application restrictions (Websites): Add the necessary websites to this section
            - **Important:** Wix Studio requires a **fileusr** link, not just the website domain. This can be found using Inspect Element and copying the link provided by the Google Maps error message when the map is not loading.
    - Copy API key
    - Add key into the map iframe on Wix Studio

### Wix Studio
- **Prerequisites:** Wix Studio account
- **Wix Studio Secret Manager:** `DJANGO_API_KEY`
- **Steps:**
    - Create frontend elements (iframe for map, popup, Velo page code, Wix Studio backend JSW file)
    - Configure Wix Studio secrets
    - Publish site

### Stripe
- **Prerequisites:** Stripe account
- **Environment Variables:** `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- **Steps:** 
    - Create a webhook pointed to backend
    - Obtain environment variables and add them to Azure

---

## Code Structure
### Backend
- Django:
    - `trees/`**:** Main app (models, views, admin, templates, static, management commands)
    - `adopt_a_tree/`**:** Project settings
    - `staticfiles/`**:** Collection of files from `trees/static/` for production use
- Wix Studio:
    - `treeApis.jsw`**:** API calls to Django backend


### Frontend
- **Home page code:** Contains all button functionality and Wix Studio backend calls 
- `html1` **iframe:** Map settings (Google Maps loading, pin loading)
- `adoptionButton` **iframe:** Holds payment link functionality
- `treeImage` **iframe:** Image monitoring and deployment
--- 

## Coding Standards
TBD

---

## References
- [Official Django documentation](https://docs.djangoproject.com/en/6.0/)

- [Official Django tutorial](https://docs.djangoproject.com/en/6.0/intro/tutorial01/)

- [Official Wix Studio documentation](https://support.wix.com/en/wix-studio)

- [Official Stripe documentation](https://docs.stripe.com)

- [Official Google Maps documentation](https://developers.google.com/maps/documentation)

- [Official Azure documentation](https://learn.microsoft.com/en-us/azure/?product=popular)

- [Microsoft documentation on setting up a Django app service](https://learn.microsoft.com/en-us/azure/app-service/tutorial-python-postgresql-app-django?tabs=copilot&pivots=azure-portal)

- ASA Adopt-A-Tree maintainers

- More information pertaining to setup and functionality of the project can be found on the [official final report]()