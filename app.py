import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
import click

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '9f3a8c7b6d2e5a1f0b3c9d4e7f8a6b2c')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Database configuration - support both SQLite and MySQL
db_type = os.getenv('DB_TYPE', 'sqlite')
if db_type == 'mysql':
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '1234')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME', 'freshbasket')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///freshbasket.db'

# Upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads', 'products')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in first.'

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define models after db initialization
class User(UserMixin, db.Model):
    """User model for customer accounts"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify the password against the hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Product(db.Model):
    """Product model for fruits and vegetables"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)
    
    # Relationships
    cart_items = db.relationship('CartItem', backref='product', lazy=True, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy=True, cascade='delete')
    
    def __repr__(self):
        return f'<Product {self.name}>'


class CartItem(db.Model):
    """Shopping cart items (session-based)"""
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_subtotal(self):
        """Calculate subtotal for this cart item"""
        return self.product.price * self.quantity
    
    def __repr__(self):
        return f'<CartItem {self.product.name} x{self.quantity}>'


class Order(db.Model):
    """Customer orders"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    shipping_address = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def calculate_total(self):
        """Calculate total from order items"""
        return sum(item.get_subtotal() for item in self.items)
    
    def __repr__(self):
        return f'<Order {self.id} - {self.status}>'


class OrderItem(db.Model):
    """Individual items in an order"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    def get_subtotal(self):
        """Calculate subtotal for this order item"""
        return self.price * self.quantity
    
    def __repr__(self):
        return f'<OrderItem {self.product.name} x{self.quantity}>'


@login_manager.user_loader
def load_user(user_id):
    """Load user from database by ID"""
    return User.query.get(int(user_id))


# ==================== Authentication Routes ====================

@app.route('/')
def home():
    """Home page - display featured products"""
    featured_products = Product.query.filter_by(is_available=True).limit(6).all()
    return render_template('index.html', featured_products=featured_products)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        try:
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember_me'))
            flash(f'Welcome back, {user.first_name or user.username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


# ==================== Product Routes ====================

@app.route('/products')
def products():
    """Browse all products"""
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    
    query = Product.query.filter_by(is_available=True)
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%') | 
                             Product.description.ilike(f'%{search}%'))
    
    all_products = query.all()
    categories = db.session.query(Product.category).distinct().all()
    
    return render_template('products.html', 
                          products=all_products, 
                          categories=[c[0] for c in categories],
                          selected_category=category,
                          search_term=search)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter_by(
        category=product.category,
        is_available=True
    ).filter(Product.id != product_id).limit(4).all()
    
    return render_template('product_detail.html', 
                          product=product, 
                          related_products=related_products)


# ==================== Cart Routes ====================

def get_session_id():
    """Get or create session ID for anonymous carts"""
    if 'cart_session' not in session:
        session['cart_session'] = os.urandom(16).hex()
        session.permanent = True
    return session['cart_session']


@app.route('/cart')
def view_cart():
    """View shopping cart"""
    if current_user.is_authenticated:
        # For logged-in users, fetch from database if needed
        cart_items = CartItem.query.filter_by(session_id=get_session_id()).all()
    else:
        cart_items = CartItem.query.filter_by(session_id=get_session_id()).all()
    
    total = sum(item.get_subtotal() for item in cart_items)
    item_count = sum(item.quantity for item in cart_items)
    
    return render_template('cart.html', 
                          cart_items=cart_items, 
                          total=total, 
                          item_count=item_count)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    product = Product.query.get_or_404(product_id)
    quantity = request.form.get('quantity', 1, type=int)
    
    if quantity < 1:
        quantity = 1
    
    if quantity > product.stock:
        flash('Not enough stock available.', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    
    session_id = get_session_id()
    cart_item = CartItem.query.filter_by(
        session_id=session_id,
        product_id=product_id
    ).first()
    
    try:
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                session_id=session_id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(cart_item)
        
        db.session.commit()
        flash(f'{product.name} added to cart!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to add to cart: {str(e)}', 'error')
    
    return redirect(url_for('view_cart'))


@app.route('/cart/update/<int:cart_item_id>', methods=['POST'])
def update_cart_item(cart_item_id):
    """Update cart item quantity"""
    cart_item = CartItem.query.get_or_404(cart_item_id)
    quantity = request.form.get('quantity', 1, type=int)
    
    if quantity < 1:
        quantity = 1
    
    if quantity > cart_item.product.stock:
        flash('Not enough stock available.', 'error')
        return redirect(url_for('view_cart'))
    
    try:
        cart_item.quantity = quantity
        db.session.commit()
        flash('Cart updated.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to update cart: {str(e)}', 'error')
    
    return redirect(url_for('view_cart'))


@app.route('/cart/remove/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    """Remove item from cart"""
    cart_item = CartItem.query.get_or_404(cart_item_id)
    product_name = cart_item.product.name
    
    try:
        db.session.delete(cart_item)
        db.session.commit()
        flash(f'{product_name} removed from cart.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to remove item: {str(e)}', 'error')
    
    return redirect(url_for('view_cart'))


# ==================== Order Routes ====================

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout and place order"""
    cart_items = CartItem.query.filter_by(session_id=get_session_id()).all()
    
    if not cart_items:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('view_cart'))
    
    if request.method == 'POST':
        shipping_address = request.form.get('shipping_address')
        notes = request.form.get('notes', '')
        
        if not shipping_address:
            flash('Shipping address is required.', 'error')
            return redirect(url_for('checkout'))
        
        try:
            # Create order
            total_amount = sum(item.get_subtotal() for item in cart_items)
            order = Order(
                user_id=current_user.id,
                shipping_address=shipping_address,
                notes=notes,
                total_amount=total_amount
            )
            
            # Add order items
            for cart_item in cart_items:
                order_item = OrderItem(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                order.items.append(order_item)
            
            db.session.add(order)
            db.session.flush()
            
            # Clear cart
            for item in cart_items:
                db.session.delete(item)
            
            db.session.commit()
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_confirmation', order_id=order.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to place order: {str(e)}', 'error')
            return redirect(url_for('checkout'))
    
    total = sum(item.get_subtotal() for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)


@app.route('/order/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Order confirmation page"""
    order = Order.query.get_or_404(order_id)
    
    # Check authorization
    if order.user_id != current_user.id:
        flash('You do not have permission to view this order.', 'error')
        return redirect(url_for('home'))
    
    return render_template('order_confirmation.html', order=order)


@app.route('/orders')
@login_required
def user_orders():
    """View user's orders"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('orders.html', orders=orders)


# ==================== Admin Routes ====================

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(10).all()
    low_stock_products = Product.query.filter(Product.stock < 10).all()
    
    # Calculate revenue
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    
    return render_template('admin/dashboard.html',
                          total_users=total_users,
                          total_products=total_products,
                          total_orders=total_orders,
                          pending_orders=pending_orders,
                          recent_orders=recent_orders,
                          low_stock_products=low_stock_products,
                          total_revenue=total_revenue)


@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    """Admin: view all products"""
    products = Product.query.all()
    return render_template('admin/products.html', products=products)


@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_product():
    """Admin: add new product"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        price = request.form.get('price', type=float)
        stock = request.form.get('stock', type=int)
        image_url = request.form.get('image_url', '').strip()
        
        if not all([name, category, price is not None, stock is not None]):
            flash('All required fields must be filled.', 'error')
            return redirect(url_for('admin_add_product'))
        
        # Handle file upload
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Add timestamp to make filename unique
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    try:
                        file.save(filepath)
                        image_url = f"/static/uploads/products/{filename}"
                    except Exception as e:
                        flash(f'Error uploading file: {str(e)}', 'error')
                else:
                    flash('Invalid file type. Please upload JPG, PNG, GIF, or WEBP.', 'error')
        
        # Use placeholder if no image provided
        if not image_url:
            image_url = '/static/images/placeholder.jpg'
        
        try:
            product = Product(
                name=name,
                description=description,
                category=category,
                price=price,
                stock=stock,
                image_url=image_url,
                is_available=True
            )
            db.session.add(product)
            db.session.commit()
            flash(f'Product "{name}" added successfully!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')
    
    return render_template('admin/add_product.html')


@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_product(product_id):
    """Admin: edit product"""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.category = request.form.get('category')
        product.price = request.form.get('price', type=float)
        product.stock = request.form.get('stock', type=int)
        product.is_available = request.form.get('is_available') == 'on'
        
        # Handle file upload
        file_uploaded = False
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Add timestamp to make filename unique
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    try:
                        file.save(filepath)
                        product.image_url = f"/static/uploads/products/{filename}"
                        file_uploaded = True
                    except Exception as e:
                        flash(f'Error uploading file: {str(e)}', 'error')
                else:
                    flash('Invalid file type. Please upload JPG, PNG, GIF, or WEBP.', 'error')
        
        # Update URL if provided and no file uploaded
        if not file_uploaded:
            url_input = request.form.get('image_url', '').strip()
            if url_input:
                product.image_url = url_input
        
        try:
            db.session.commit()
            flash(f'Product "{product.name}" updated successfully!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'error')
    
    return render_template('admin/edit_product.html', product=product)


@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_product(product_id):
    """Admin: delete product"""
    product = Product.query.get_or_404(product_id)
    product_name = product.name
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{product_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('admin_products'))


@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    """Admin: view all orders"""
    status_filter = request.args.get('status', 'all')
    
    query = Order.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    orders = query.order_by(Order.order_date.desc()).all()
    return render_template('admin/orders.html', orders=orders, status_filter=status_filter)


@app.route('/admin/orders/<int:order_id>')
@login_required
@admin_required
def admin_order_detail(order_id):
    """Admin: view order details"""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)


@app.route('/admin/orders/<int:order_id>/update-status', methods=['POST'])
@login_required
@admin_required
def admin_update_order_status(order_id):
    """Admin: update order status"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
        order.status = new_status
        try:
            db.session.commit()
            flash(f'Order #{order.id} status updated to {new_status}!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating order: {str(e)}', 'error')
    else:
        flash('Invalid status value.', 'error')
    
    return redirect(url_for('admin_order_detail', order_id=order_id))


@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Admin: view all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    """Admin: toggle user admin status"""
    if user_id == current_user.id:
        flash('You cannot change your own admin status.', 'error')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    
    try:
        db.session.commit()
        status = 'admin' if user.is_admin else 'regular user'
        flash(f'{user.username} is now a {status}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('500.html'), 500


# ==================== CLI Commands ====================

@app.cli.command()
def init_db():
    """Initialize the database with tables"""
    db.create_all()
    print('Database initialized.')


@app.cli.command()
def seed_db():
    """Seed database with sample products"""
    # Check if products already exist
    if Product.query.first():
        print('Database already seeded.')
        return
    
    sample_products = [
        Product(
            name='Red Apples',
            category='fruit',
            price=5.99,
            stock=50,
            description='Fresh, crisp red apples from local orchards',
            image_url='/static/images/apple.jpg',
            is_available=True
        ),
        Product(
            name='Bananas',
            category='fruit',
            price=3.99,
            stock=100,
            description='Golden yellow bananas, rich in potassium',
            image_url='/static/images/banana.jpg',
            is_available=True
        ),
        Product(
            name='Carrots',
            category='vegetable',
            price=4.99,
            stock=80,
            description='Organic carrots, sweet and crunchy',
            image_url='/static/images/carrot.jpg',
            is_available=True
        ),
        Product(
            name='Tomatoes',
            category='vegetable',
            price=6.99,
            stock=60,
            description='Vine-ripened tomatoes, perfect for salads',
            image_url='/static/images/tomato.jpg',
            is_available=True
        ),
        Product(
            name='Strawberries',
            category='fruit',
            price=7.99,
            stock=40,
            description='Fresh strawberries, sweet and juicy',
            image_url='/static/images/strawberry.jpg',
            is_available=True
        ),
        Product(
            name='Lettuce',
            category='vegetable',
            price=3.49,
            stock=75,
            description='Crisp leafy lettuce for healthy salads',
            image_url='/static/images/lettuce.jpg',
            is_available=True
        ),
    ]
    
    for product in sample_products:
        db.session.add(product)
    
    db.session.commit()
    print('Database seeded with sample products.')


@app.cli.command()
@click.option('--username', prompt='Admin username', help='Username for the admin account')
@click.option('--email', prompt='Admin email', help='Email for the admin account')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password for the admin account')
def create_admin(username, email, password):
    """Create an admin user"""
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        print(f'User {username} already exists.')
        return
    
    admin = User(username=username, email=email, is_admin=True)
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    print(f'Admin user {username} created successfully!')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
