from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db,Customer, Products, Cart, Orders, Payments
import pytz
ist = pytz.timezone('Asia/Kolkata')
import pandas as pd
from agents import recommendation_agent
import ast 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///KnowBuy.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'

db.init_app(app)

# Data Loaders
def load_customer_data():
    if Customer.query.first():
        return

    df = pd.read_csv("customer_data_collection.csv")
    for _, row in df.iterrows():
        customer = Customer(
            Customer_Id=row['Customer_ID'].strip(),
            Name=row.get('Name'),
            Email=row.get('Email'),
            Age=int(row['Age']) if pd.notna(row['Age']) else None,
            Gender=row.get('Gender'),
            Location=row.get('Location'),
            Browsing_history=row.get('Browsing_history'),
            Purchase_history=row.get('Purchase_History'),
            CustomerSegment=row.get('Customer_Segment'),
            Avg_Order_Value=float(row['Avg_Order_Value']) if pd.notna(row['Avg_Order_Value']) else None,
            Holiday=row.get('Holiday'),
            Season=row.get('Season')
        )
        db.session.add(customer)
    db.session.commit()
    print("Customer data loaded successfully.")

def load_product_data_once():
    if Products.query.first():
        print("Products already loaded.")
        return

    print("Loading products into database...")
    df = pd.read_csv("product_recommendation_data.csv")

    for _, row in df.iterrows():
        product = Products(
            Product_Id=row['Product_ID'],
            Category=row['Category'],
            Subcategory=row['Subcategory'],
            Price=row['Price'],
            Brand=row['Brand'],
            Average_Rating_of_Similar_Products=row['Average_Rating_of_Similar_Products'],
            Product_Rating=row['Product_Rating'],
            Customer_Review_Sentiment_Score=row['Customer_Review_Sentiment_Score'],
            Holiday=row['Holiday'],
            Season=row['Season'],
            Geographical_Location=row['Geographical_Location'],
            Similar_products=row.get('Similar_Product_List'),
            recommendation_prob=row['Probability_of_Recommendation']
        )
        db.session.add(product)

    db.session.commit()
    print("Products loaded successfully.")

# Routes
@app.route('/', methods=["GET","HEAD"])
def index():
    if request.method == "HEAD":
        return "", 200
    trending_products = Products.query.order_by(Products.recommendation_prob.desc()).limit(12).all()
    return render_template('index.html', trending_products=trending_products)

@app.route('/main', methods=["POST"])
def main():
    customer_id = request.form.get('cid')
    response = recommendation_agent(customer_id)
    try:
        product_ids = ast.literal_eval(response)  # if it's a stringified list
    except:
        product_ids = response.split()  # fallback if they're space-separated

    recommended_products = Products.query.filter(Products.Product_Id.in_(product_ids)).all()

    return render_template('main.html', recommended_products=recommended_products, cid=customer_id)

@app.route("/signup", methods=["POST"])
def signup():
    name = request.form["name"]
    email = request.form["email"]
    location = request.form["location"]
    age = int(request.form["age"])
    holiday = request.form["holiday"]
    season = request.form["season"]

    customer_df = pd.read_csv("customer_data_collection.csv")

    # Generate new Customer ID
    if customer_df["Customer_ID"].str.startswith("C").any():
        last_cid = customer_df["Customer_ID"].str.extract(r'C(\d+)').astype(int).max()[0]
    else:
        last_cid = 10999
    new_cid = f"C{last_cid + 1}"

    # Append new customer
    new_customer = {
        "Customer_ID": new_cid,
        "Name": name,
        "Email": email,
        "Location": location,
        "Age": age,
        "Holiday": holiday,
        "Season": season
    }

    customer_df = pd.concat([customer_df, pd.DataFrame([new_customer])], ignore_index=True)
    customer_df.to_csv("customer_data_collection.csv", index=False)

    return render_template("index.html", signup_message=f"Sign up successful! Your Customer ID is {new_cid}. Please use it to log in.")

@app.route("/signin", methods=["POST"])
def login():
    customer_id = request.form.get("customer_id")
    customer = Customer.query.filter_by(Customer_Id=customer_id).first()
    if customer:
        trending_products = Products.query.order_by(Products.recommendation_prob.desc()).limit(12).all()
        return render_template('loggedin.html', trending_products=trending_products, cid=customer.Customer_Id)

    else:
        
        trending_products = Products.query.order_by(Products.recommendation_prob.desc()).limit(12).all()
        return render_template('index.html', trending_products=trending_products)

@app.route("/logout")
def logout():
    return redirect("/")

@app.route("/search", methods=["POST"])
def search_products():
    customer_id = request.form.get("cid")
    search_term = request.form.get("prod", "").strip()
    number_of_results = int(request.form.get("nbr")or 12) 

    matching_products = Products.query.filter(
        (Products.Brand.ilike(f"%{search_term}%")) |
        (Products.Category.ilike(f"%{search_term}%")) |
        (Products.Subcategory.ilike(f"%{search_term}%"))
    ).limit(number_of_results).all()
    return render_template("search.html", results=matching_products,cid=customer_id)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    customer_id = request.form.get('customer_id')
    product_id = request.form.get('product_id')
    customer = Customer.query.filter_by(Customer_Id=customer_id).first()
    product = Products.query.filter_by(Product_Id=product_id).first()
    existing_item = Cart.query.filter_by(customer_id= customer_id, product_id=product_id).first()
    if existing_item:
        existing_item.quantity += 1
        flash("Product quantity updated in cart!")
    else:
        new_item = Cart(customer_id=customer_id, product_id=product_id, quantity=1)
        db.session.add(new_item)
        flash("Product added to cart!")
        if product.Category and product.Category not in customer.Browsing_history:
            customer.Browsing_history.append(product.Category)
    db.session.commit()
    return redirect(url_for('view_cart', customer_id=customer_id))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    customer_id = request.form.get('customer_id')
    product_id = request.form.get('product_id')

    existing_item = Cart.query.filter_by(customer_id= customer_id, product_id=product_id).first()
    if existing_item.quantity>1:
        existing_item.quantity -= 1
        flash("One unit removed from cart.")
    else:
        db.session.delete(existing_item)
        flash("Item removed from cart.")
    db.session.commit()
    return redirect(url_for('view_cart', customer_id=customer_id))

@app.route('/cart/<customer_id>')
def view_cart(customer_id):
    cart_items = Cart.query.filter_by(customer_id=customer_id).all()

    total = 0
    for item in cart_items:
        product = Products.query.filter_by(Product_Id=item.product_id).first()
        if product:
            item.product = product 
            total += item.quantity * item.product.Price
    return render_template('cart.html', cid=customer_id, cart_items=cart_items, total=total)

@app.route('/view_orders/<customer_id>')
def view_orders(customer_id):
    orders = Orders.query.filter_by(customer_id=customer_id).all()
    return render_template('view_orders.html', orders=orders, cid=customer_id)

@app.route('/checkout', methods=['POST'])
def checkout():
    customer_id = request.form.get('cid')
    if not customer_id:
        flash("Customer ID is missing for checkout.", "danger")
        return redirect(url_for('index'))

    cart_items = Cart.query.filter_by(customer_id=customer_id).all()

    total = 0
    for item in cart_items:
        if item.product:
            total += item.quantity * item.product.Price

    return render_template('checkout.html', customer_id=customer_id, cart_items=cart_items, total=total)

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    customer_id = request.form.get('customer_id')
    product_ids = request.form.getlist('product_id')
    payment_method = request.form.get('payment_method')

    if not product_ids:
        flash("Missing order details.", "danger")
        return redirect(url_for('cart'))

    cart_items = Cart.query.filter(Cart.customer_id == customer_id, Cart.product_id.in_(product_ids)).all()

    if not cart_items:
        flash("Cart is empty or items missing.", "warning")
        return redirect(url_for('view_cart', customer_id=customer_id))

    total = 0
    new_orders = []

    for item in cart_items:
        if item.product:
            subtotal = item.quantity * item.product.Price
            total += subtotal

            new_order = Orders(
                customer_id=customer_id,
                product_id=item.product.Product_Id,
                quantity=item.quantity,
                total_price=subtotal,
                order_date=datetime.now(ist)
            )
            db.session.add(new_order)
            new_orders.append(new_order)

    db.session.commit()

    # Create payment record
    if payment_method:
        for order in new_orders:
            payment = Payments(
                order_id=order.id,
                amount=order.total_price,
                payment_method=payment_method,
                payment_date=datetime.now(ist),
                status="Success"
            )
            db.session.add(payment)

    db.session.commit()

    # Clear cart
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()

    flash("Your order has been placed successfully!", "success")
    return render_template("order_success.html", orders=new_orders, payment_method=payment_method,cid=customer_id)

def initialize():
    with app.app_context():
        db.create_all()
        load_customer_data()
        load_product_data_once()

initialize()

if __name__ == "__main__":
    app.run(debug=True)
 
