# FreshBasket 🥬🍎

A modern e-commerce web application for buying and selling fresh fruits and vegetables online.

## Features

- **User Authentication**: Secure user registration and login system
- **Product Catalog**: Browse fruits and vegetables with detailed descriptions
- **Shopping Cart**: Add items to cart and manage quantities
- **Orders**: Place orders and track order history
- **Admin Dashboard**: Manage products, orders, and users
- **Responsive Design**: Mobile-friendly interface
- **Database Support**: SQLite (development) and MySQL (production)

## Tech Stack

- **Backend**: Flask 3.1.2
- **Database**: SQLAlchemy ORM with SQLite/MySQL support
- **Authentication**: Flask-Login
- **Frontend**: HTML, CSS, JavaScript
- **Server**: Gunicorn

## Installation

### Prerequisites

- Python 3.10+
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   cd FreshBasket
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   
   Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   DB_TYPE=sqlite
   # For MySQL (optional):
   # DB_TYPE=mysql
   # DB_USER=root
   # DB_PASS=your-password
   # DB_HOST=localhost
   # DB_NAME=freshbasket
   ```

6. **Initialize the database**
   ```bash
   python -m flask init-db
   ```

7. **Seed sample products (optional)**
   ```bash
   python -m flask seed-db
   ```

## Running the Application

### Development

Start the Flask development server:
```bash
python -m flask run
```

The application will be available at `http://localhost:5000`

### Production

Use Gunicorn:
```bash
gunicorn app:app
```

## Admin Setup

### Create an Admin User

```bash
python -m flask create-admin
```

Follow the prompts to enter:
- Admin username
- Admin email
- Password (with confirmation)

### Access Admin Panel

1. Login at `http://localhost:5000/login`
2. Navigate to the admin dashboard at `http://localhost:5000/admin/dashboard`
3. Manage products, orders, and users

## Project Structure

```
FreshBasket/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Environment variables (create from .env.example)
├── instance/             # SQLite database (development)
├── static/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   ├── js/
│   │   └── main.js       # Client-side JavaScript
│   └── uploads/
│       └── products/     # Product images
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── login.html        # Login page
    ├── register.html     # Registration page
    ├── products.html     # Products listing
    ├── product_detail.html # Product detail page
    ├── cart.html         # Shopping cart
    ├── checkout.html     # Checkout page
    ├── orders.html       # Order history
    ├── order_confirmation.html
    ├── 404.html          # 404 error page
    ├── 500.html          # 500 error page
    └── admin/            # Admin templates
        ├── dashboard.html
        ├── products.html
        ├── add_product.html
        ├── edit_product.html
        ├── orders.html
        ├── order_detail.html
        └── users.html
```

## Database Models

### User
- User authentication and admin status
- One-to-many relationship with Orders

### Product
- Product information (name, price, stock, category)
- Relationships with CartItems and OrderItems

### CartItem
- Session-based shopping cart items
- Linked to products and user sessions

### Order
- Customer orders with status tracking
- One-to-many relationship with OrderItems
- One-to-many relationship with Users

### OrderItem
- Individual items within an order
- Stores product info and price at time of order

## API Routes

### Public Routes
- `GET /` - Home page
- `GET /products` - Product listing
- `GET /product/<id>` - Product detail
- `POST /login` - User login
- `POST /register` - User registration
- `POST /logout` - User logout

### User Routes
- `GET /cart` - View shopping cart
- `POST /cart/add/<product_id>` - Add to cart
- `POST /cart/remove/<product_id>` - Remove from cart
- `GET /checkout` - Checkout page
- `POST /order` - Place order
- `GET /orders` - Order history

### Admin Routes
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/products` - Product management
- `POST /admin/products/add` - Add product
- `POST /admin/products/edit/<id>` - Edit product
- `POST /admin/products/delete/<id>` - Delete product
- `GET /admin/orders` - Order management
- `GET /admin/users` - User management

## Troubleshooting

### Flask command not found
Make sure your virtual environment is activated and the venv is in the parent directory:
```bash
..\venv\Scripts\python.exe -m flask create-admin
```

### Database errors
If you encounter database constraint errors, reset the database:
```bash
# Delete the instance folder
rmdir /s instance
# Reinitialize
python -m flask init-db
python -m flask seed-db
```

### Import errors
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Contributing

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'Add amazing feature'`)
3. Push to the branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues or questions, please create an issue in the repository.

---

**Happy shopping with FreshBasket! 🛒**
