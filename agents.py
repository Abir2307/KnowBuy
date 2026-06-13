import requests
import os
from models import Customer, Products, Cart
from sqlalchemy.orm import joinedload

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def query_mistral(prompt, model="mistralai/Mistral-Small-3.2-24B-Instruct-2506", stream=False):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": stream
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload
        )

        print("Status:", response.status_code)
        print("Raw:", response.text)

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except requests.exceptions.HTTPError as e:
        return f"HTTP Error: {e} | {response.text}"

    except Exception as e:
        return f"Error: {str(e)}"
    
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
    You are a personalized recommendation engine.
    
    Customer Profile:
    Age: {customer.Age}
    Gender: {customer.Gender}
    Location: {customer.Location}
    Segment: {customer.CustomerSegment}
    
    Purchase History:
    {customer.Purchase_history}
    
    Browsing History:
    {customer.Browsing_history}
    
    Product Catalog:
    {product_info}
    
    Rules:
    
    1. Prioritize products similar to the customer's browsing history.
    2. Prioritize products similar to previously purchased products.
    3. Use customer age, gender, location and segment when relevant.
    4. Do NOT recommend products solely because they have high ratings.
    5. Avoid generic or globally popular recommendations.
    6. Maximize personalization.
    7. Recommend products from categories and brands the customer has previously interacted with.
    8. Only recommend products that are strongly relevant to the customer profile.
    
    Return exactly 20 Product_IDs as a Python list.
    
    Example:
    ["P1001","P1002"]
    """
    
    return query_mistral(prompt)
