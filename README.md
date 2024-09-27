# Incident Management System

This is a social networking application built using Django Rest Framework (DRF) with features like user authentication, friend request management, user search, and activity tracking. The application is designed for scalability, security, and optimized performance using techniques like query optimization, caching, and rate limiting.

## Features

- User Authentication & Authorization
- User Management
- Friend Request Management
- Friends List
- Pending Friend Requests
- Role-based access
- Performance Optimization
- Security & Scalability Features

## Technologies Used

- **Backend:** Python 3.11+, Django, Django REST Framework
- **Database:** PostgreSQL
- **Frontend:** Postman


## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL
- Postman

### Installation

2. Create and activate the virtual environment:

   - python -m venv venv
   - source venv/bin/activate  # On Windows use `venv\Scripts\activate`


3. Install the required packages:

   - pip install -r requirements.txt

4. Make the .env file

   - Make the .env file in the proejct dir and configure the database credentials as I have attached the .env.example file for your reference.

5. Run database migrations and create superuser:

   - python manage.py makemigrations
   - python manage.py migrate

   - python manage.py createsuperuser

6. Access the application:

   - Open your web browser and navigate to http://127.0.0.1:8000/.


7. API Documentation link : I have shared the postman collection with you and also attached the API documentation.


8. Design Choices:

   - Authentication: JWT-based token authentication is implemented to secure API access and support token refreshing.
   - Caching: Django's cache framework (Redis) is used to cache frequent queries, such as the friends list, to optimize performance.
   - Database Optimization: Queries are optimized with select_related and prefetch_related to minimize database hits.
   - Rate Limiting: To prevent spam, friend requests are rate-limited and have a configurable cooldown period after rejection.
   - Security: User data (like passwords) is encrypted using Django's built-in cryptography tools to ensure security.
   - Dockerization: The project is containerized using Docker for easy deployment and scalability.


