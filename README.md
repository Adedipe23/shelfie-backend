# Integrated Supermarket Management System (ISMS)

A production-ready backend for the Integrated Supermarket Management System using FastAPI and modern Python principles.

## Features

- Clean architecture with separation of concerns
- SQLModel ORM with SQLite for development and PostgreSQL for production
- OAuth2 authentication with JWT tokens
- Dynamic role-based access control with customizable permissions
- Query manager system for permission filtering (similar to Django Rest Framework)
- Background tasks for asynchronous operations
- Comprehensive logging with structured output
- API documentation with OpenAPI
- CLI tools for common operations
- Docker support for development and production
- Comprehensive test suite with pytest

## Project Structure

```
app/
  api/           # Route definitions, grouped by module
    v1/          # API version 1 endpoints
  core/          # Settings, database, security, logging, permissions
  models/        # ORM models (SQLModel)
  schemas/       # Pydantic schemas (DTOs)
  services/      # Business logic and query managers
  tasks/         # Background task handlers
  utils/         # Utility functions
  main.py        # FastAPI app entry
tests/
  api/           # API endpoint tests
  core/          # Core module tests
  services/      # Service layer tests
  conftest.py    # Test fixtures and configuration
Dockerfile       # Docker setup
docker-compose.yml # Docker Compose configuration
manage.py        # CLI tool for common operations
```

## Getting Started

### Prerequisites

- Python 3.12+
- Poetry (optional, for dependency management)
- Docker and Docker Compose (optional, for containerization)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/isms.git
cd isms
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file:

```bash
cp .env.example .env
```

5. Initialize the database:

```bash
python manage.py init_db
```

6. Create a superuser:

```bash
python manage.py create_superuser
```

### Running the Application

The project includes a convenient run script for common operations:

```bash
# On Linux/macOS
python run.py dev

# On Windows (using the provided batch file)
run dev
```

Common commands:

```bash
# Run in development mode
run dev

# Initialize the database
run init_db

# Create a superuser
run create_superuser

# Run tests
run test
run test --cov  # With coverage
run test tests/api/  # Specific tests

# Run in Docker
run docker-dev
run docker-test
```

#### Traditional Methods

```bash
# Using manage.py
python manage.py runserver

# Using uvicorn directly
uvicorn app.main:app --reload

# Using Docker Compose
docker-compose up -d
```

### API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Dynamic Permission System

The ISMS backend implements a flexible, dynamic permission system that allows for:

1. **Role-Based Access Control**: Standard roles (Admin, Manager, Cashier) with predefined permissions
2. **Custom Roles**: Create custom roles with specific permission sets
3. **Query Filtering**: Automatically filter database queries based on user permissions
4. **Permission Dependencies**: Protect API endpoints with permission-based dependencies

### Permission Registry

The system uses a central permission registry that manages all permissions and roles:

```python
# Register a permission and assign to roles
PermissionRegistry.register_permission(
    "inventory:create",
    [UserRole.ADMIN, UserRole.MANAGER]
)

# Create a custom role with specific permissions
PermissionRegistry.register_custom_role(
    "inventory_specialist",
    {"inventory:read", "inventory:create", "inventory:update"}
)
```

### Query Managers

Query managers automatically filter database queries based on user permissions:

```python
# Get all products visible to the current user
products = await product_manager.get_all(db, user=current_user)

# Create a product with permission check
product = await product_manager.create(db, product_data, user=current_user)
```

## Testing

Run the comprehensive test suite with pytest:

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/core/test_permissions.py
pytest tests/services/

# Run with coverage report
pytest --cov=app
```

### Running Tests with Docker

You can also run the tests in a Docker container to ensure a consistent environment:

```bash
# Build and run tests
docker-compose -f docker-compose.test.yml up --build

# Run and remove containers after completion
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit --remove-orphans
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
