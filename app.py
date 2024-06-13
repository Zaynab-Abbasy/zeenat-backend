from flask import Flask, jsonify, request
from sqlalchemy import ARRAY,Table, Column, Integer, ForeignKey,MetaData,func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
from sqlalchemy import func,extract
from flask_restful import Resource,Api
from datetime import datetime, date
import requests
from geopy.geocoders import Nominatim

import json

Base = declarative_base()

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import secrets
from sqlalchemy.orm import relationship
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail,Message
from datetime import datetime


app = Flask(__name__)

CORS(app)
metadata = MetaData()
app.secret_key = 'SECRET_KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pakistan@localhost/Zeenat'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'muneebabbasi079@gmail.com'
app.config['MAIL_PASSWORD'] = 'wglr xweq jruz fdmt'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True



db = SQLAlchemy(app)
mail = Mail(app)
jwt = JWTManager(app)
api = Api(app)
# User model
class User(db.Model):
    id = db.Column(db.String(255), primary_key=True)  # Use UUID as primary key
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    bio = db.Column(db.Text())
    reset_token = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(255), nullable=True)
    country = db.Column(db.String(255), nullable=True)

class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phoneNumber = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Admin {self.name}>'

# Define Category model
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    parent = db.Column(db.String(100), nullable=False)
    products = db.Column(ARRAY(db.String), nullable=True)
    img = db.Column(db.String(255), nullable=True,default='default_image1.jpg')
    children = db.Column(db.ARRAY(db.String), nullable=True)
    type = db.Column(db.String(50), nullable=False) 

    def __repr__(self):
        return f"<Category {self.parent}>"
    

    

#product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    img = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    imageURLs = db.Column(db.Text)
    price = db.Column(db.Float)
    discount = db.Column(db.Float)
    status = db.Column(db.String(50))
    tags = db.Column(ARRAY(db.String))
    category = db.relationship('Category', backref='associated_products')
    type = db.Column(db.String(50))
    reviews = db.relationship('Review', backref='review_product', lazy=True)
    quantity = db.Column(db.Integer, default=0)

#review model     
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer)  # Rating out of 5, for example
    comment = db.Column(db.Text)
    userId=db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    def serialize(self):
        """Serialize object data to JSON"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'rating': self.rating,
            'comment': self.comment,
            'user_id': self.userId
        }

# Define Coupon model
class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    discount_percentage = db.Column(db.Integer, nullable=False)
    coupon_code = db.Column(db.String(20), nullable=False, unique=True)
    minimum_amount = db.Column(db.Float, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    logo = db.Column(db.String(100))
    
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'discount_percentage': self.discount_percentage,
            'coupon_code': self.coupon_code,
            'minimum_amount': self.minimum_amount,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'logo': self.logo
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    shipping_option = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    subtotal = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    order_note = db.Column(db.Text)
    payment_method = db.Column(db.String(50), nullable=False)
    cart = db.Column(db.Text, nullable=False)
    invoice = db.Column(db.Text, nullable=True,default='00000')
    user = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
   
    #user = db.Column(db.String(200), nullable=False)
    def __repr__(self):
        return f"Order('{self.name}', '{self.email}')" 

     
    
    
# Signup endpoint
@app.route('/user/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    # Check if email is already taken
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    # Hash the password before saving it
    hashed_password = generate_password_hash(password)

    # Create and save the user with a dynamically generated UUID
    new_user = User(id=str(uuid.uuid4()), email=email, password=hashed_password, name=name)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

# Login endpoint
@app.route('/user/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Find the user by email
    user = User.query.filter_by(email=email).first()

    # Check if user exists and password is correct
    if user and check_password_hash(user.password, password):
        # Create access token
        # Create access token
        accessToken = create_access_token(identity=user.id)
        response_data = {
            'accessToken': accessToken,
            'user': {'id': user.id, 'email': user.email, 'name': user.name,'accessToken':accessToken,'phone': user.phone,'address': user.address,'bio': user.bio,}
        }
        return jsonify({'data': response_data}), 200
        
    else:
        app.logger.error(f'Login failed for email: {email}')
        return jsonify({'error': 'Invalid email or password'}), 401
        
    
    
    
#forget password 
@app.route('/user/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    db.session.commit()

    # Send reset password email
    msg = Message('Reset Password Request', sender='zaynababbasy29@gmail.com', recipients=[email])
    reset_link = f"http://localhost:3000/forget-password/{reset_token}"  
    msg.body = f'Please click the following link to reset your password: {reset_link}'
    mail.send(msg)

    return jsonify({'message': 'Reset password email sent'}), 200


    
    
# Confirm forgot password endpoint
@app.route('/user/confirm-forgot-password', methods=['POST'])
def confirm_forgot_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('password')

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return jsonify({'error': 'Invalid token'}), 400

    # Check if the provided new password is valid
    if not new_password or len(new_password) < 6:
        return jsonify({'error': 'New password is invalid'}), 400

    # Hash the new password
    hashed_password = generate_password_hash(new_password)
    user.password = hashed_password
    user.reset_token = None
    db.session.commit()
    app.logger.info('Password reset successfully')

    return jsonify({'message': 'Password reset successfully'}), 200


#category page
@app.route('/showCategory')
def show_category():
    categories = Category.query.all()
    categories_data = [{'id': category.id, 'parent': category.parent, 'children': category.children, 'products': category.products} for category in categories]
    return jsonify({'result': categories_data})
#get category wise products
@app.route('/categoryshow/<type>')
def get_category_by_type(type):
    categories = Category.query.filter_by(type=type).all()
    categories_data = [{'id': category.id, 'parent': category.parent, 'children': category.children, 'products': category.products, 'img': category.img} for category in categories]
    return jsonify({'result': categories_data})



@app.route('/productall')
def get_all_products():
    print("Query string", request.query_string)
    print("Request URL:", request.url)

    category_name = request.args.get('category', default=None)
    print('Category Filter:', category_name)
    
    subcategory_name = request.args.get('subCategory', default=None)
    print('SubCategory Filter:', subcategory_name)
    
    color_filter = request.args.get('color', default=None)
    print('Color Filter:', color_filter)

    if category_name:
        if subcategory_name:
            # Filter products based on the category and subcategory
            products = Product.query.join(Category).filter(
                Category.parent == category_name,
                Category.children.contains([subcategory_name])
            ).all()
        else:
            # Filter products based on the category only
            products = Product.query.join(Category).filter(
                Category.parent == category_name
            ).all()
    else:
        # If no category is specified, retrieve all products
        products = Product.query.all()

    serialized_products = []

    for product in products:
        print('Product ID:', product.id)
        print('Image URLs:', product.imageURLs)
        # Serialize product data
        serialized_product = {
            'id': product.id,
            'img': product.img,
            'category': product.category.parent if product.category else None,
            'title': product.title,
            'price': product.price,
            'discount': product.discount,
            'status': product.status,
            'imageURLs': product.imageURLs,
            'tags': product.tags,
            'colors': []  # Initialize an empty list for colors
            # Add more attributes as needed
        }
        
        # Apply color filtering if color_filter is provided
        if color_filter:
            # Filter products based on the color provided
            products = [
                product for product in products if any(
                    img_data.get('color', {}).get('name', '').lower() == color_filter.lower()
                    for img_data in json.loads(product.imageURLs)
                )
            ]
            print('Filtered Products:', products)

        # Remove duplicate colors
        unique_colors = []
        for color in serialized_product['colors']:
            if color not in unique_colors:
                unique_colors.append(color)
        serialized_product['colors'] = unique_colors
        print('Serialized Products:', serialized_products)
        # Append the serialized product to the list
        serialized_products.append(serialized_product)
        
    return jsonify({'data': serialized_products})







#get product by type
@app.route('/getproductbytype/<product_type>', methods=['GET'])
def get_products(product_type):
    # Get the query parameters
    query_params = request.args
    print("query",query_params)

    # Extract the 'query' parameter
    query = query_params.get('query')

    # Extract the 'topSellers' parameter
    top_sellers_param = query_params.get('query')

    # Query products based on the product type
    products = Product.query.filter_by(type=product_type).all()
    
    # Filter products based on the query parameter and product status
    if top_sellers_param == 'topSellers=true':
     products = Product.query.filter_by(status='top seller')

    # Convert products to JSON format
    products_json = [{
        'id': product.id,
        'img': product.img,
        'category_id': product.category_id,
        'title': product.title,
        'description': product.description,
        'imageURLs': product.imageURLs,
        'price': product.price,
        'discount': product.discount,
        'status': product.status,
        'tags': product.tags
    } for product in products]

    # Return JSON response
    return jsonify({'data': products_json})













#product details page
@app.route('/productdetails/<int:product_id>', methods=['GET'])
def get_product(product_id):
    print("product details:", product_id)
    product = Product.query.filter_by(id=product_id).first()

    # Check if the product exists
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    category_parent = product.category.parent if product.category and hasattr(product.category, 'parent') else None
   
    # Parse imageURLs string to JSON array
    image_urls = json.loads(product.imageURLs)

    # Serialize reviews individually
    reviews = []
    for review in product.reviews:
        review_data = {
            'id': review.id,
            'product_id': review.product_id,
            'rating': review.rating,
            'comment': review.comment,
            'userId'  :review.userId,
            'user_name': None 
        }
        user = User.query.filter_by(id=review.userId).first()
        if user:
         review_data['user_name'] = user.name

        reviews.append(review_data)

    product_json = {
        'id': product.id,
        'img': product.img,
        'category_id': product.category_id,
        'title': product.title,
        'description': product.description,
        'imageURLs': image_urls,  # Use parsed JSON array
        'price': product.price,
        'discount': product.discount,
        'status': product.status,
        'tags': product.tags,
        'category': category_parent,
        'reviews' : reviews  # Include serialized reviews
    }

    # Return JSON response
    return jsonify(product_json)

#top rated products filter
@app.route('/top-rated-products')
def get_top_rated_products():
    # Query to retrieve the top-rated products
    top_rated_products = db.session.query(
        Product.id,
        Product.img,
        Product.title,
        Product.price,
        func.avg(Review.rating).label('average_rating')
    ).join(Review).group_by(Product.id).order_by(func.avg(Review.rating).desc()).limit(3).all()
    
    # Serialize the data
    products_data = []
    for product in top_rated_products:
        product_data = {
            'id': product.id,
            'img': product.img,
            'title': product.title,
            'price' :product.price,
            'average_rating': round(product.average_rating, 2)
        }
        products_data.append(product_data)
    
    # Return the top-rated products as JSON
    return jsonify(data=products_data)

@app.route('/coupons')
def get_coupons():
    coupons = Coupon.query.all()
    coupon_data = [{
        'id': coupon.id,
        'title': coupon.title,
        'discountPercentage': coupon.discount_percentage,
        'couponCode': coupon.coupon_code,
        'minimumAmount': coupon.minimum_amount,
        'endTime': coupon.end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'logo': coupon.logo
    } for coupon in coupons]
    return jsonify({'data':coupon_data})

#save order



@app.route('/saveOrder', methods=['POST'])
def save_order():
    data = request.json
    cart_json = json.dumps(data['cart'])
    # Store all details directly from the request JSON
    order = Order(
        name=data.get('name'),
        address=data.get('address'),
        contact=data.get('contact'),
        email=data.get('email'),
        city=data.get('city'),
        country=data.get('country'),
        zip_code=data.get('zipCode'),
        shipping_option=data.get('shippingOption'),
        subtotal=data.get('subTotal'),
        shipping_cost=data.get('shippingCost'),
        discount=data.get('discount'),
        total_amount=data.get('totalAmount'),
        order_note=data.get('orderNote'),
        payment_method=data.get('paymentMethod'),
        cart =cart_json,  # Assuming 'cart' contains the cart items data
        invoice = datetime.now().strftime("%Y%m%d%H%M%S") + '-' + str(uuid.uuid4())[:8],
        user=data.get('user') 
    )

    db.session.add(order)
    db.session.commit()
    print("Order ID:", order.id)
    response_data = {
        "data": {
            "order": {
                "id": order.id
            }
        },
        "message": "Order saved successfully"
    }
    print("Order ID final:", response_data)
     # Return response with order ID
    return jsonify(response_data), 200




#get user order by id 

@app.route('/user-order/<int:order_id>', methods=['GET'])
def get_user_order(order_id):
    print("order details:", order_id)
    order = Order.query.filter_by(id=order_id).first()
    
    if order:
        order_data = {
            'id': order.id,
            'name': order.name,
            'address': order.address,
            'contact': order.contact,
            'email': order.email,
            'city': order.city,
            'country': order.country,
            'zip_code': order.zip_code,
            'shipping_option': order.shipping_option,
            'status': order.status,
            'subtotal': order.subtotal,
            'shipping_cost': order.shipping_cost,
            'discount': order.discount,
            'total_amount': order.total_amount,
            'order_note': order.order_note,
            'payment_method': order.payment_method,
            'cart': order.cart 
        }
        return jsonify({ 'data': order_data}), 200
    else:
        return jsonify({'message': 'Order not found'}), 404


#update profile
@app.route('/user/update-profile/<string:id>', methods=['PUT'])
def update_profile(id):
    
        user = User.query.get(id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.json
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        user.phone = data.get('phone', user.phone)
        user.address = data.get('address', user.address)
        user.bio = data.get('bio', user.bio)
        
        db.session.commit()
        return jsonify({'message': 'User profile updated successfully'}), 200
 #change password user    


# Endpoint for changing password
@app.route('/user/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    new_password = data.get('newPassword')

    # Find the user by email
    user = User.query.filter_by(email=email).first()

    # Check if user exists and password is correct
    if user and check_password_hash(user.password, password):
        # Update user's password
        user.password = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({'message': 'Password updated successfully'}), 200
    else:
        return jsonify({'error': 'Invalid email or password'}), 401

#get user orders 
# Route for fetching user orders

@app.route('/user-orders')
def get_user_orders():
    # Retrieve orders from the database
    orders = Order.query.all()
    # Convert orders to a list of dictionaries
    orders_list = []
    for order in orders:
        order_data = {
            'id': order.id,
            'name': order.name,
            'address': order.address,
            'contact': order.contact,
            'email': order.email,
            'city': order.city,
            'country': order.country,
            'total_amount': order.total_amount,
            'payment_method': order.payment_method,
            'user_id': order.user,
            'status' :order.status
        }
        orders_list.append(order_data)
    return jsonify({'data':orders_list})


#product review 
# Endpoint to handle adding a review
@app.route('/add-review', methods=['POST'])
def add_review():
    data = request.json
    
    # Extract data from the request
    userId = data.get('userId')
    productId = data.get('productId')
    rating = data.get('rating')
    comment = data.get('comment')
    
    # Validate required fields
    if not userId or not productId  or not rating or  not comment:
        return jsonify({'error': 'Missing data'}), 400
    
    # Create a new Review instance
    new_review = Review(
        product_id=productId,
        rating=rating,
        comment=comment,
        userId=userId
    )
    
    # Add the new review to the database session
    db.session.add(new_review)
    db.session.commit()
    return jsonify({'message': 'Review added successfully'}), 200
 
 
 ############ ADMIN PANNEL 
 #get products
@app.route('/admingetproducts', methods=['GET'])
def get_adminproducts():
    products = Product.query.all()
    products_list = []
    for product in products:
        # Calculate average rating
        if product.reviews:
            average_rating = sum(review.rating for review in product.reviews) / len(product.reviews)
        else:
            average_rating = None  # or set to 0 or any default value if no reviews

        # Prepare reviews list
        reviews_list = [{'comment': review.comment, 'rating': review.rating} for review in product.reviews]

        products_list.append({
            'id': product.id,
            'title': product.title,
            'description': product.description,
            'price': product.price,
            'rating': average_rating,
            'category': product.category.parent if product.category else None,  # Assuming you have a title field in Category
            'quantity': product.quantity,
            'discount': product.discount,
            'status': product.status,
            'img': product.img,
            'reviews': reviews_list,  # Serialize reviews properly
            'tags': product.tags,
            'type': product.type,
            'imageURLs': product.imageURLs,
        })
    return jsonify({'data': products_list})


#get customers

@app.route('/client/customers', methods=['GET'])
def get_customers():
    # Query orders and include relevant customer information
    orders_with_customer_info = Order.query.all()
    
    customers_list = [{
        'id': order.user,
        'name': order.name,
        'email': order.email,
        'contact': order.contact,
        'country': order.country,
        
        # Add any other fields you need from the Order table
    } for order in orders_with_customer_info]
    print (customers_list)

    return jsonify({'data':customers_list})
 


@app.route('/client/orders', methods=['GET'])
def get_orders():
    # Query all orders
    orders = Order.query.all()

    # Extract order information
    orders_list = [{
        'id': order.id,
        'name': order.name,
        'email': order.email,
        'contact': order.contact,
        'address': order.address,
        'city': order.city,
        'country': order.country,
        'zip_code': order.zip_code,
        'shipping_option': order.shipping_option,
        'status': order.status,
        'subtotal': order.subtotal,
        'shipping_cost': order.shipping_cost,
        'discount': order.discount,
        'total_amount': order.total_amount,
        'order_note': order.order_note,
        'payment_method': order.payment_method,
        'cart': order.cart,
        'invoice': order.invoice,
        'user': order.user
        # Add any other fields you need from the Order table
    } for order in orders]

    # Return orders data as JSON
    return jsonify({'data':orders_list})
 
 
@app.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    # Count total distinct customers who have placed orders
    total_customers = db.session.query(func.count(func.distinct(Order.user))).scalar()

    # Get today's date
    today = date.today()
    
    # Calculate today's sales
    today_sales = db.session.query(func.sum(Order.total_amount)).filter(
        extract('year', Order.created_at) == today.year,
        extract('month', Order.created_at) == today.month,
        extract('day', Order.created_at) == today.day
    ).scalar() or 0

    # Calculate monthly sales
    start_of_month = today.replace(day=1)
    monthly_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= start_of_month
    ).scalar() or 0

    # Calculate yearly sales
    start_of_year = today.replace(month=1, day=1)
    yearly_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= start_of_year
    ).scalar() or 0

    # Get sales by category
    orders = Order.query.all()
    sales_by_category = {}
    for order in orders:
        cart_items = json.loads(order.cart)
        for item in cart_items:
            category = item['category']
            sales_by_category[category] = sales_by_category.get(category, 0) + item['price'] * item['orderQuantity']

    sales_by_category_data = [{"category": k, "totalSales": v} for k, v in sales_by_category.items()]

    # Get all transactions and format the data
    transactions = Order.query.all()
    transactions_data = [
        {
            "_id": order.id,
            "userId": order.user,
            "createdAt": order.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # Format date
            "products": order.cart,  # Assuming this is a JSON field or needs parsing
            "cost": order.total_amount
        } for order in transactions
    ]

    # Prepare the data to be sent in the response
    data = {
        "totalCustomers": total_customers,
        "todayStats": {
            "totalSales": today_sales
        },
        "thisMonthStats": {
            "totalSales": monthly_sales
        },
        "yearlySalesTotal": yearly_sales,
        "salesByCategory": sales_by_category_data,
        "transactions": transactions_data
    }

    # Return the data as a JSON response
    return jsonify(data)



@app.route('/add-product', methods=['POST'])
def add_product():
    data = request.form
    files = request.files.getlist('product_images')

    # Parse imageURLs JSON string into a Python list
    image_urls = json.loads(data.get('imageURLs'))

    # You may need to adjust the way you handle colors and image URLs here
    # For example, you could loop through each image URL object and store them separately in the database
    for image in image_urls:
        url = image['url']
        color_name = image['color']['name']
        clr_code = image['color']['clrCode']
        # Store the image URL, color name, and color code in the database as required

    # Store the default image URL
    default_img_url = data.get('img')

    # Proceed with storing other product data in the database
    product = Product(
        title=data.get('title'),
        description=data.get('description'),
        price=float(data.get('price')),
        discount=float(data.get('discount')),
        status=data.get('status'),
        tags=data.get('tags'),
        type=data.get('type'),
        quantity=int(data.get('quantity')),
        category_id=int(data.get('category_id')),
        imageURLs=json.dumps(image_urls),  # Store imageURLs as JSON string
        img=default_img_url  # Store default image URL
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({'message': 'Product added successfully'}), 201   

#update product 

# Update Product endpoint
import logging

# Configure logging to output to console
logging.basicConfig(level=logging.DEBUG)

@app.route('/updateProduct/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        logging.debug(f"Updating product with ID: {product_id}")
        logging.debug(f"Received data: {data}")

        # Update each attribute individually
        product.img = data.get('img', product.img)
        product.category_id = data.get('category', product.category)
        product.title = data.get('title', product.title)
        product.description = data.get('description', product.description)
        product.imageURLs = data.get('imageURLs', product.imageURLs)
        product.price = float(data.get('price', product.price))  # Example: Convert to float if price is expected as a number
        product.discount = float(data.get('discount', product.discount))  # Example: Convert to float if discount is expected as a number
        product.status = data.get('status', product.status)
        product.tags = data.get('tags', product.tags)
        product.type = data.get('type', product.type)
        product.quantity = int(data.get('quantity', product.quantity))  # Example: Convert to int if quantity is expected as a number
        
        

        db.session.commit()
        logging.debug("Product updated successfully")
        return jsonify({'message': 'Product updated successfully'})
    
    except ValueError as ve:
        logging.error(f"ValueError occurred: {ve}")
        db.session.rollback()  # Rollback database changes
        return jsonify({'error': str(ve)}), 400  # Return 400 Bad Request with error message
    
    except Exception as e:
        logging.error(f"Exception occurred: {e}")
        db.session.rollback()  # Rollback database changes
        return jsonify({'error': str(e)}), 500  # Return 500 Internal Server Error


# Delete Product endpoint
@app.route('/deleteProduct/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})


#update order status
@app.route('/updateOrderStatus/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')
    print("new ",new_status)

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    order.status = new_status
    db.session.commit()
    
    return jsonify({'message': 'Order status updated successfully'})


def get_coordinates(city, country):
    # Use a geocoding service to get coordinates for the city and country
    response = requests.get(f"https://api.opencagedata.com/geocode/v1/json?q={city},{country}&key=5716cfd50622490e904c5ef2cfd9f601")
    data = response.json()
    if data['results']:
        return data['results'][0]['geometry']['lng'], data['results'][0]['geometry']['lat']
    return None, None

geolocator = Nominatim(user_agent="geoapiExercises")

@app.route('/client/geography', methods=['GET'])
def get_usersgeo():
    user_locations = []
    users = User.query.all()  # Fetch all users from the database

    for user in users:
        location = geolocator.geocode(f"{user.city}, {user.country}")
        if location:
            user.latitude = location.latitude
            user.longitude = location.longitude
            user_locations.append({
                'id': user.id,
                'name': user.name,
                'city': user.city,
                'country': user.country,
                'latitude': user.latitude,
                'longitude': user.longitude
            })
    
    return jsonify(user_locations)
#category 
@app.route('/getcategories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([{
        'id': category.id,
        'parent': category.parent,
        'type': category.type,
        'img': category.img,
        'products': category.products,
        'children': category.children
    } for category in categories])

# Endpoint to delete a category by ID
@app.route('/deletecategories/<int:id>', methods=['DELETE'])
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted successfully'})

#add category
@app.route('/addcategory', methods=['POST'])
def add_category():
    data = request.get_json()
    new_category = Category(
        parent=data['parent'],
        type=data['type'],
        img=data.get('img', 'default_image.jpg'),
        products=data.get('products', []),
        children=data.get('children', [])
    )
    db.session.add(new_category)
    db.session.commit()
    return jsonify({'message': 'Category added successfully'}), 201

#update category
@app.route('/updatecategory/<int:id>', methods=['PUT'])
def update_category(id):
    data = request.get_json()
    category = Category.query.get_or_404(id)
    category.parent = data.get('parent', category.parent)
    category.type = data.get('type', category.type)
    category.img = data.get('img', category.img)
    category.products = data.get('products', category.products)
    category.children = data.get('children', category.children)
    db.session.commit()
    return jsonify({'message': 'Category updated successfully'}), 200

#coupon data
@app.route('/getcoupons', methods=['GET'])
def get_coupons_route():
    coupons = Coupon.query.all()
    return jsonify([coupon.serialize() for coupon in coupons])

@app.route('/addcoupon', methods=['POST'])
def add_coupon():
    data = request.json
    new_coupon = Coupon(
        title=data['title'],
        discount_percentage=data['discount_percentage'],
        coupon_code=data['coupon_code'],
        minimum_amount=data['minimum_amount'],
        end_time=datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M'),
        logo=data['logo']
    )
    db.session.add(new_coupon)
    db.session.commit()
    return jsonify({'message': 'Coupon added successfully'})

@app.route('/updatecoupon/<int:id>', methods=['PUT'])
def update_coupon(id):
    coupon = Coupon.query.get(id)
    if not coupon:
        return jsonify({'error': 'Coupon not found'}), 404
    
    data = request.json
    coupon.title = data['title']
    coupon.discount_percentage = data['discount_percentage']
    coupon.coupon_code = data['coupon_code']
    coupon.minimum_amount = data['minimum_amount']

    end_time_str = data['end_time']
    try:
        coupon.end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        try:
            coupon.end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

    coupon.logo = data['logo']

    db.session.commit()
    return jsonify({'message': 'Coupon updated successfully'})

@app.route('/deletecoupon/<int:id>', methods=['DELETE'])
def delete_coupon(id):
    coupon = Coupon.query.get(id)
    if not coupon:
        return jsonify({'error': 'Coupon not found'}), 404

    db.session.delete(coupon)
    db.session.commit()
    return jsonify({'message': 'Coupon deleted successfully'})


#review
# Route to get all reviews
@app.route('/getreviews', methods=['GET'])
def get_reviews():
    reviews = Review.query.all()
    return jsonify([review.serialize() for review in reviews])

# Route to delete a specific review by ID
@app.route('/deletereviews/<int:id>', methods=['DELETE'])
def delete_review(id):
    review = Review.query.get(id)
    if not review:
        return jsonify({'error': 'Review not found'}), 404
    
    db.session.delete(review)
    db.session.commit()
    return jsonify({'message': 'Review deleted successfully'})

#overview data
@app.route('/sales/sales', methods=['GET'])
def get_sales_data():
    try:
        # Fetch monthly sales data
        monthly_data = db.session.query(
            func.extract('month', Order.created_at).label('month'),
            func.sum(Order.total_amount).label('totalSales')
        ).group_by(func.extract('month', Order.created_at)).all()

        formatted_monthly_data = [
            {'month': month, 'totalSales': float(total_sales)}
            for month, total_sales in monthly_data
        ]

        # Fetch daily sales data within a specified date range
        start_date_str = request.args.get('startDate', str(datetime.now().date() - timedelta(days=30)))
        end_date_str = request.args.get('endDate', str(datetime.now().date()))

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        daily_data = db.session.query(
            func.date(Order.created_at).label('date'),
            func.sum(Order.total_amount).label('totalSales')
        ).filter(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ).group_by(func.date(Order.created_at)).all()

        formatted_daily_data = [
            {'date': str(date), 'totalSales': float(total_sales)}
            for date, total_sales in daily_data
        ]

        # Fetch yearly total sales
        current_year = datetime.now().year
        yearly_sales_total = db.session.query(
            func.sum(Order.total_amount)
        ).filter(
            func.extract('year', Order.created_at) == current_year
        ).scalar()

        # Fetch sales by category
        orders = Order.query.all()
        sales_by_category = {}

        for order in orders:
            cart_items = json.loads(order.cart)
            for item in cart_items:
                category = item['category']  # Assuming each item has a 'category' key
                sales_by_category[category] = sales_by_category.get(category, 0) + item['price'] * item['orderQuantity']  # Assuming each item has 'price' and 'quantity' keys

        formatted_sales_by_category = {
            category: float(total_sales)
            for category, total_sales in sales_by_category.items()
        }

        return jsonify({
            'monthlyData': formatted_monthly_data,
            'dailyData': formatted_daily_data,
            'yearlySalesTotal': float(yearly_sales_total),
            'salesByCategory': formatted_sales_by_category
        }), 200


    except Exception as e:
        # Log the error for debugging purposes
        app.logger.error(f"Error fetching monthly sales data: {str(e)}")
        return jsonify({'error': 'An error occurred while fetching data'}), 500
    
    
    
    
#admin list 
@app.route('/admins', methods=['GET'])
def get_admins():
    admins = Admin.query.all()
    admins_list = [{
        "_id": admin.id,
        "name": admin.name,
        "email": admin.email,
        "phoneNumber": admin.phoneNumber,
        "country": admin.country,
        "occupation": admin.occupation,
        "role": admin.role
    } for admin in admins]
    return jsonify(admins_list)

if __name__ == '__main__':
    app.run(debug=True)
@app.route('/')
def index():
    return 'hello world'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

