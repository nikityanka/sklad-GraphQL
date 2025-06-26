import strawberry
from .data import data_store
from .auth import create_access_token, verify_token
from typing import List, Optional
from datetime import datetime


@strawberry.type
class Product:
    id: strawberry.ID
    name: str
    quantity: int


@strawberry.type
class StockChange:
    id: strawberry.ID
    productId: strawberry.ID
    delta: int
    timestamp: datetime


@strawberry.type
class StockAlert:
    product: Product
    currentQuantity: int
    threshold: int


@strawberry.input
class AddProductInput:
    name: str
    quantity: int


@strawberry.type
class Query:
    @strawberry.field
    def get_product(self, id: strawberry.ID) -> Optional[Product]:
        product = data_store.get_product(id)
        if product:
            return Product(**product)
        return None

    @strawberry.field
    def list_products(self, limit: int = 10, offset: int = 0) -> List[Product]:
        products = data_store.list_products(limit, offset)
        return [Product(**p) for p in products]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_product(self, input: AddProductInput) -> Product:
        product = data_store.add_product(input.name, input.quantity)
        return Product(**product)

    @strawberry.mutation
    def update_stock(self, productId: strawberry.ID, delta: int) -> Product:
        product = data_store.update_stock(productId, delta)
        if product:
            return Product(**product)
        raise Exception("Товар не найден")

    @strawberry.mutation
    def remove_product(self, id: strawberry.ID) -> bool:
        return data_store.remove_product(id)

    @strawberry.mutation
    def login(self, username: str, password: str) -> str:
        user = data_store.find_user(username)
        if user and user['password'] == password:
            return create_access_token({"sub": username, "role": user['role']})
        raise Exception("Неверные данные")


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def stream_stock_alerts(self, threshold: int) -> StockAlert:
        pass


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)