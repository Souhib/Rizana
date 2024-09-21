# Vinted Clone API

A web application for users to buy and sell second-hand clothes, jewelry, bags, and more. Inspired by Vinted, this platform allows users to register, create listings, communicate with potential buyers or sellers, and complete transactions securely.

## Table of Contents

- [Project Context](#project-context)
- [Features](#features)
- [Technical Stack](#technical-stack)
- [Database Schema](#database-schema)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## Project Context

The second-hand market is growing rapidly as more people turn towards sustainable and eco-friendly shopping practices. This project aims to replicate the key functionalities of Vinted, providing a user-friendly platform for individuals to list their used items, explore products from others, and make secure transactions.

### Features

- **User Authentication and Management**: Register, login, and manage user profiles.
- **Product Listings**: Users can list their used items for sale, complete with images, descriptions, and prices.
- **Categories and Filters**: Items can be sorted by category, condition, price, and other filters.
- **Wishlist and Favorites**: Users can save items they are interested in purchasing later.
- **Secure Transactions**: Supports multiple payment methods for secure transactions.
- **Chat and Notifications**: In-app chat system for communication between buyers and sellers, along with real-time notifications.
- **User Feedback and Reviews**: Users can provide feedback and rate each other after transactions.
- **Activity Logs**: Tracks user actions for analytics and security purposes.
- **JSON-based Logging**: Efficient storage of activity logs using JSON fields for flexible data representation.

## Technical Stack

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) - A modern, fast (high-performance) web framework for building APIs with Python 3.10+.
- **Database**: [PostgreSQL](https://www.postgresql.org/) - A powerful, open-source object-relational database system.
- **ORM**: [SQLModel](https://sqlmodel.tiangolo.com/) - An ORM for Python based on SQLAlchemy and Pydantic, leveraging type hints for better development experience.
- **Authentication**: JWT (JSON Web Tokens) for secure user authentication and session management.
- **Testing**: [Pytest](https://docs.pytest.org/) for unit testing.
- **Documentation**: Auto-generated API documentation using [Swagger UI](https://swagger.io/tools/swagger-ui/) and [ReDoc](https://github.com/Redocly/redoc).

## Database Schema

The database schema is designed to efficiently store and manage user data, product listings, transactions, and more.

### Key Tables

- **User**: Stores user information and credentials.
- **Category**: Categorizes items into groups like clothes, jewelry, bags, etc.
- **Item**: Holds data on listed items for sale, including title, description, price, images, etc.
- **Order**: Tracks transactions between buyers and sellers.
- **Review**: Manages user reviews and feedback.
- **UserActivityLog**: Tracks user activities with flexible, JSON-based logging.
- **Feedback**: Collects user feedback about the platform or service.
- **Wishlist, Payment Method, Chat, Favorite, Transaction History, Item Condition, Discount, Shipping, Report, Notification**: Additional tables to support various features.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/vinted-clone-api.git
   cd vinted-clone-api
   ```

2. **Create a Virtual Environment**

   For Linux/Mac:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

   For Windows:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**

   Create a `.env` file in the root directory and add the following:

   ```
   DATABASE_URL=postgresql://username:password@localhost/dbname
   ```

5. **Initialize the Database**

   ```bash
   python init_db.py
   ```

## Usage

1. **Start the FastAPI Server**

   ```bash
   uvicorn main:app --reload
   ```

2. **Access the API**

   Open your browser and navigate to `http://localhost:8000` to access the API.

3. **API Documentation**

   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## API Documentation

Detailed API documentation is available through Swagger UI and ReDoc. These provide comprehensive information about each endpoint, including request/response schemas, authentication requirements, and example usage.

## Contributing

We welcome contributions to improve the Vinted Clone API! Please follow these steps to contribute:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

Please ensure your code adheres to the project's coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
