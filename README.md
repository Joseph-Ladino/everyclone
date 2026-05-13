# EveryClone

## Description

EveryClone is a full-stack web application built to replicate, manage, and enhance the meal-kit delivery experience. It acts as a centralized hub for recipe management, automated meal planning, and grocery logistics. The system calculates portion scaling, consolidates overlapping ingredients, handles unit conversions, and generates structured prep sheets to optimize cooking workflows.

The application is decoupled, utilizing a Vue.js 3 frontend and a Python FastAPI backend, backed by a PostgreSQL database. It is fully containerized for both local development and production deployment.

## Features

* **Menu Generator:** Automatically proposes weekly meal plans based on target meal counts, minimum ratings, and mandatory anchor ingredients.
* **Smart Grocery Engine:** Consolidates ingredients across multiple recipes into a single shopping list. Automatically normalizes volume metrics (e.g., combining tablespoons and cups) and categorizes items by supermarket aisle.
* **Dynamic Portion Scaling:** Users can scale recipes up or down. The system recalculates all core ingredients, staples, and spice blends in real-time using native fraction formatting.
* **Prep Sheets:** Extracts and aggregates raw spices and base ingredients needed to recreate proprietary meal-kit blends.
* **Data Portability:** Supports stateless sharing of meal plans via URL parameters, as well as full JSON import and export for saving weekly setups.
* **Print-Optimized Views:** Generates clean, CSS-optimized printable pages for grocery lists and recipe instructions.

### Motivation
This project aims to land halfway between the convenience of a meal-kit subscription and the cost of planning your own meals. Down the line, I intend to build another application to help automate purchasing the groceries from exported JSON files.

## Prerequisites

* Docker and Docker Compose
* PostgreSQL (Containerized)
* Node.js (For local development only)

---

## Environment Configuration

Before building the application for production, create an environment files in the root directory.
**.env**

```env
DB_USER=your_prod_user
DB_PASSWORD=your_prod_password
FRONTEND_URL=https://app.yourdomain.com

```

---

## Local Development

The development environment utilizes Vite's Hot Module Replacement (HMR) via polling and FastAPI's auto-reload.

To start the local development server:

```bash
docker-compose -f docker-compose.dev.yml up -d

```

* Frontend: `http://localhost:5173`
* Backend API: `http://localhost:8000`

---

## Production Deployment

The production environment uses a multi-stage Docker build, compiling the Vue frontend into static files served by an internal Nginx container.

### 1. Build and Push Images

Compile the frontend and backend images locally, then push them to your container registry (e.g., Docker Hub). Replace `<username>` with your registry username.

```bash
# Build the Backend
docker build -t <username>/ep-backend:latest ./backend

# Build the Frontend
docker build -t <username>/ep-frontend:latest ./frontend

# Push to Registry
docker push <username>/ep-backend:latest
docker push <username>/ep-frontend:latest

```

### 2. Database Initialization

Ensure your production database dump (`init_prod.sql`) is located in the same directory as your production compose file on the server. The Postgres container will automatically ingest this file on its first boot.

### 3. Deploy

On your production server, pull the images and spin up the stack:

```bash
docker-compose -f docker-compose.prod.yml up -d

```

---

## Development Approach

This application was developed using AI-driven code generation. The system architecture, feature requirements, and production deployment pipeline were human-directed, while the core codebase was written by an AI assistant in a rapid-prototyping environment.
