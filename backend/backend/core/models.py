from .mongo import db
from bson import ObjectId

def insert_customer(data):
    result = db.customers.insert_one(data)
    print(f"[insert_customer] Inserted ID: {result.inserted_id}, Data: {data}")
    return result

def get_customers(company=None):
    query = {}
    if company and company != "전체":
        query['company'] = company
    return list(db.customers.find(query))

def delete_customer(customer_id):
    result = db.customers.delete_one({'_id': ObjectId(customer_id)})
    return result.deleted_count


