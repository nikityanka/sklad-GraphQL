import strawberry
from typing import List, Optional
from models import (
    get_products,
    get_product,
    add_product as add_product_db,
    update_product_stock,
    remove_product,
    get_stock_changes,
    Product as ProductModel,
    StockChange as StockChangeModel,
    get_user
)
from datetime import datetime
import asyncio
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

def role_required(info, required_role: str):
    user = info.context["user"]
    print(f"User role: {user.get('role')}, Required: {required_role}")
    if user.get("role") != required_role:
        raise Exception(f"Unauthorized access. Requires {required_role} role")

def create_access_token(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

@strawberry.type
class Product:
    id: strawberry.ID
    name: str
    quantity: int

    @classmethod
    def from_model(cls, model: ProductModel):
        return cls(
            id=strawberry.ID(model.id),
            name=model.name,
            quantity=model.quantity
        )

@strawberry.type
class StockChange:
    id: strawberry.ID
    productId: strawberry.ID
    delta: int
    timestamp: datetime

    @classmethod
    def from_model(cls, model: StockChangeModel):
        return cls(
            id=strawberry.ID(model.id),
            productId=strawberry.ID(model.productId),
            delta=model.delta,
            timestamp=datetime.fromisoformat(model.timestamp)
        )

@strawberry.type
class StockAlert:
    productId: strawberry.ID
    productName: str
    currentQuantity: int
    message: str
    timestamp: datetime

@strawberry.input
class AddProductInput:
    name: str
    quantity: int

@strawberry.type
class LoginResult:
    token: str
    userRole: str = strawberry.field(name="userRole")

@strawberry.type
class Query:
    @strawberry.field
    def get_product(self, info: strawberry.Info, id: strawberry.ID) -> Optional[Product]:
        product = get_product(str(id))
        return Product.from_model(product) if product else None

    @strawberry.field
    def list_products(self, info: strawberry.Info, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Product]:
        products = get_products(limit, offset)
        return [Product.from_model(p) for p in products]

    @strawberry.field
    def get_stock_changes(self, info: strawberry.Info) -> List[StockChange]:
        role_required(info, "admin")
        return [StockChange.from_model(sc) for sc in get_stock_changes()]

    @strawberry.field
    def protected_resource(self, info: strawberry.Info) -> str:
        role_required(info, "admin")
        return "Secret data for admins"

@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_product(self, info: strawberry.Info, input: AddProductInput) -> Product:
        role_required(info, "admin")
        product = add_product_db(input.name, input.quantity)
        return Product.from_model(product)

    @strawberry.mutation
    def update_stock(self, info: strawberry.Info, productId: strawberry.ID, delta: int) -> Product:
        role_required(info, "manager")
        product = update_product_stock(str(productId), delta)
        return Product.from_model(product)

    @strawberry.mutation
    def remove_product(self, info: strawberry.Info, id: strawberry.ID) -> bool:
        role_required(info, "admin")
        return remove_product(str(id))

    @strawberry.mutation
    def login(self, username: str, password: str) -> LoginResult:
        user = get_user(username)
        if user and user.password == password:
            token = create_access_token({"sub": username, "role": user.role})
            print(f"Generated token for {username}: {token}")
            return LoginResult(token=token, userRole=user.role)
        raise Exception("Invalid credentials")

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def stream_stock_alerts(self, info: strawberry.Info, threshold: int) -> StockAlert:
        while True:
            products = get_products()
            for product in products:
                if product.quantity <= threshold:
                    yield StockAlert(
                        productId=strawberry.ID(product.id),
                        productName=product.name,
                        currentQuantity=product.quantity,
                        message=f"Товар {product.name} заканчивается! Текущее количество: {product.quantity}",
                        timestamp=datetime.now()
                    )
            await asyncio.sleep(10)