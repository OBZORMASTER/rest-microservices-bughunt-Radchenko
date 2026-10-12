import os
from fastapi import FastAPI, Header, status
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel

app = FastAPI(title="OrderService")

AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8001")
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://localhost:8002")

ORDERS: list[dict] = []

class OrderCreate(BaseModel):
    productId: int
    qty: int

@app.post("/orders")
async def create_order(payload: OrderCreate, authorization: str | None = Header(default=None)):
    async with httpx.AsyncClient() as client:
        auth_res = await client.get(f"{AUTH_URL}/whoami", headers={"Authorization": authorization or ""})
        if auth_res.status_code != 200:
            return JSONResponse({"error": "Unauthorized"}, status_code=status.HTTP_401_UNAUTHORIZED)

        prod_res = await client.get(f"{PRODUCT_URL}/products/{payload.productId}")
        if prod_res.status_code != 200:
            return JSONResponse({"error": "Product not found"}, status_code=status.HTTP_404_NOT_FOUND)

        product = prod_res.json()
        if product.get("inStock", 0) < payload.qty:
            return JSONResponse({"error": "Not enough stock"}, status_code=status.HTTP_400_BAD_REQUEST)

    order = {
        "order_id": len(ORDERS) + 1,
        "product_id": payload.productId,
        "quantity": payload.qty,
        "status": "created",
    }
    ORDERS.append(order)
    return JSONResponse(order, status_code=status.HTTP_201_CREATED)

@app.get("/orders")
async def list_orders():
    return {"orders": ORDERS}
