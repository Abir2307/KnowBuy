import requests
from models import Customer, Products,Cart
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import joinedload

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def query_mistral(prompt, model="mistral", stream=False):
        response = requests.post(
            OLLAMA_API_URL,
            json={"model": model, "prompt": prompt, "stream": stream},
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    
def customer_agent(customer_id, user_input):
    customer = Customer.query.filter_by(Customer_Id=customer_id).first()
    if not customer:
        return "Customer not found."

    prompt = f"""
    Customer Information:
    Name: {customer.Name}
    Age: {customer.Age}
    Gender: {customer.Gender}
    Location: {customer.Location}
    Segment: {customer.CustomerSegment}
    Purchase History: {customer.Purchase_history}
    Browsing History: {customer.Browsing_history}

    User Input: "{user_input}"

    What does the customer want? Summarize the intent and mention what data is relevant to respond.
    """
    return query_mistral(prompt)

def analytics_agent(customer_id=None):
    if customer_id:
        customer = Customer.query.filter_by(Customer_Id=customer_id).first()
        if not customer:
            return "Customer not found."

        prompt = f"""
You are a customer behavior analysis expert for an E-Commerce platform.

Analyze the following customer's behavioral data and provide detailed insights:
- What patterns do you observe?
- What does their data suggest about their preferences and buying behavior?
- What can be done to improve their engagement and convert them into a loyal customer?

Customer Profile:
Segment: {customer.CustomerSegment}
Age: {customer.Age}
Gender: {customer.Gender}
Location: {customer.Location}
Average Order Value: ₹{customer.Avg_Order_Value}
Browsing History: {customer.Browsing_history}
Purchase History: {customer.Purchase_history}

Also provide:
1. At least 2 tailored engagement strategies
2. A short summary of the customer's persona
"""
        response = query_mistral(prompt)   
        return response
    else:
        return "Customer ID is required for analytics."

def recommendation_agent(customer_id):
    customer = Customer.query.options(joinedload(Customer.cart_items)).filter_by(Customer_Id=customer_id).first()

    if not customer:
        return []

    products = Products.query.limit(10).all()
    product_info = ""
    for p in products:
        product_info += f"ID: {p.Product_Id}, Brand: {p.Brand}, Category: {p.Category}, Rating: {p.Product_Rating}, Holiday: {p.Holiday}, Season: {p.Season}\n"

    prompt = f"""
    You are a recommendation engine.

    Customer Details:
    Age: {customer.Age}
    Gender: {customer.Gender}
    Location: {customer.Location}
    Segment: {customer.CustomerSegment}
    Purchase History: {customer.Purchase_history}
    Browsing History: {customer.Browsing_history}

    Product Catalog:
    {product_info}

    Based on this, return a list of 8 Product_IDs that are most relevant to the customer.
    Format your answer as a Python list of strings. Example: ["P2001", "P2005"]
    """

    return query_mistral(prompt)
