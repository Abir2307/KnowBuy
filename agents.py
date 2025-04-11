import requests
import os
from models import Customer, Products, Cart
from sqlalchemy.orm import joinedload

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def query_mistral(prompt, model="mistralai/mistral-7b-instruct", stream=False):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": stream
    }
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response_json = response.json()
        
        if "choices" not in response_json:
            return f"Unexpected response format: {response_json}"

        return response_json["choices"][0]["message"]["content"].strip()

    except requests.RequestException as e:
        return f"Request failed: {str(e)}"
    except ValueError as e:
        return f"JSON parsing failed: {str(e)}"
    
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

    products = Products.query.limit(20).all()
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

    Based on this, return a list of 20 Product_IDs that are most relevant to the customer.
    Format your answer as a Python list of strings. Example: ["P2001", "P2005"]
    """

    return query_mistral(prompt)
