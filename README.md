# BookNook - Online Bookstore API

An online bookstore API built with Flask, featuring user authentication, book management, shopping cart functionality, and an admin dashboard.

## Features

- **Authentication & Authorization**
  - JWT-based authentication
  - Role-based access control (Admin/User)
  - Password reset functionality
  - Email verification

- **Book Management**
  - Comprehensive book catalog
  - Search and filtering capabilities
  - Category-based organization
  - Stock management

- **Shopping Experience**
  - Shopping cart functionality
  - Secure checkout with Stripe
  - Order history
  - Real-time stock updates

- **Review System**
  - Book ratings and reviews
  - User-specific review management
  - Review moderation

- **Admin Dashboard**
  - Book inventory management
  - Order processing
  - User management
  - Sales analytics and reporting

- **Performance & Security**
  - Redis caching
  - Rate limiting
  - API documentation with Swagger
  - Secure payment processing

## Technology Stack

- **Backend**: Python/Flask
- **Database**: PostgreSQL
- **Caching**: Redis
- **Payment**: Stripe
- **Documentation**: Swagger/OpenAPI
- **Testing**: Pytest
- **CI/CD**: GitHub Actions
- **Containerization**: Docker

## Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

## Quick Start

### Using Docker

1. Clone the repository:
```bash
git clone https://github.com/codefromlani/BookNook.git
cd booknook
```

2. Create a `.env` file:
```bash
DATABASE_URL=postgresql://postgres:postgres@db:5432/booknook
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=your-email
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
REDIS_URL=redis://redis:6379/0
```

3. Run with Docker Compose:
```bash
docker-compose up --build
```

### Manual Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up the database:
```bash
flask db upgrade
```

4. Run the application:
```bash
flask run
```

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

## API Documentation

Access the Swagger documentation at `/api/docs` when running the application.

### Key Endpoints

- **Authentication**
  - POST `/auth/register` - Register new user
  - POST `/auth/login` - User login
  - POST `/auth/refresh` - Refresh JWT token

- **Books**
  - GET `/books/list` - List all books
  - GET `/books/search` - Search books
  - GET `/books/{id}` - Get book details
  - GET `/books/categories` - List categories

- **Cart & Orders**
  - GET `/api/cart` - View cart
  - POST `/api/cart/add` - Add to cart
  - POST `/api/checkout/complete` - Complete checkout

- **Reviews**
  - GET `/api/books/{book_id}/reviews` - Get book reviews
  - POST `/api/books/{book_id}/reviews` - Create review

- **Admin**
  - POST `/admin/books` - Add new book
  - GET `/admin/orders` - View orders
  - GET `/admin/reports/sales` - View sales reports

## Security

- JWT-based authentication
- Rate limiting on sensitive endpoints
- Password hashing
- Input validation
- CORS protection
- Secure payment processing

## CI/CD Pipeline

The project includes a GitHub Actions workflow that:
1. Runs tests
2. Performs code quality checks
3. Runs security scanning
4. Builds and pushes Docker image
5. Reports test coverage
