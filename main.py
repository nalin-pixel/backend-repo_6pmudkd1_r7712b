import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order, User

app = FastAPI(title="E-Commerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "E-Commerce Backend Running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Product endpoints
@app.post("/api/products", response_model=dict)
async def create_product(product: Product):
    try:
        inserted_id = create_document("product", product)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products", response_model=List[dict])
async def list_products(category: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    filter_dict = {}
    if category:
        filter_dict["category"] = category
    if q:
        filter_dict["title"] = {"$regex": q, "$options": "i"}
    try:
        docs = get_documents("product", filter_dict, limit)
        # Convert ObjectId to string
        for d in docs:
            d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Seed demo products for convenience
@app.post("/api/products/seed")
async def seed_products():
    sample = [
        {"title": "Running Shoes", "description": "Lightweight running shoes", "price": 59.99, "category": "Shoes", "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800"},
        {"title": "Wireless Headphones", "description": "Noise-cancelling over-ear", "price": 129.99, "category": "Electronics", "image": "https://images.unsplash.com/photo-1518446021390-81371fecb3a2?w=800"},
        {"title": "Smart Watch", "description": "Fitness tracking and more", "price": 199.00, "category": "Electronics", "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800"},
        {"title": "Backpack", "description": "Everyday carry pack", "price": 39.95, "category": "Bags", "image": "https://images.unsplash.com/photo-1520975916090-3105956dac38?w=800"},
    ]
    try:
        ids = []
        for p in sample:
            ids.append(create_document("product", p))
        return {"inserted": len(ids), "ids": ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Order endpoints
@app.post("/api/orders")
async def create_order(order: Order):
    try:
        order_id = create_document("order", order)
        return {"id": order_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
