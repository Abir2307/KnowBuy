from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.mutable import MutableList
from datetime import datetime
import pytz
ist = pytz.timezone('Asia/Kolkata')
db = SQLAlchemy()
# Models
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Customer_Id = db.Column(db.String(50), unique=True, nullable=False)
    Name = db.Column(db.String(100), nullable=True)
    Email = db.Column(db.String(100), nullable=True)
    Age = db.Column(db.Integer, nullable=True)
    Gender = db.Column(db.String(10), nullable=True)
    Location = db.Column(db.String(100), nullable=True)
    Browsing_history = db.Column(MutableList.as_mutable(db.PickleType), default=list)
    Purchase_history = db.Column(db.String(500), nullable=True)
    CustomerSegment = db.Column(db.String(50), nullable=True)
    Avg_Order_Value = db.Column(db.Float, nullable=True)
    Holiday = db.Column(db.String(50), nullable=True)
    Season = db.Column(db.String(50), nullable=True)
    orders = db.relationship('Orders', backref='customer')

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Product_Id = db.Column(db.String, unique=True)
    Category = db.Column(db.String)
    Subcategory = db.Column(db.String)
    Price = db.Column(db.Float)
    Brand = db.Column(db.String)
    Average_Rating_of_Similar_Products = db.Column(db.Float)
    Product_Rating = db.Column(db.Float)
    Customer_Review_Sentiment_Score = db.Column(db.Float)
    Holiday = db.Column(db.String(50))
    Season = db.Column(db.String(50))
    Geographical_Location = db.Column(db.String)
    Similar_products = db.Column(db.String)
    recommendation_prob = db.Column(db.Float)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String, db.ForeignKey('customer.Customer_Id'), nullable=False)
    product_id = db.Column(db.String, db.ForeignKey('products.Product_Id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    customer = db.relationship('Customer', backref='cart_items')
    product = db.relationship('Products')

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.now(ist))
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    product = db.relationship('Products', backref='orders')
    payment=db.relationship('Payments', backref='orders')

class Payments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.now(ist))
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
