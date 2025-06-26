import json
import os
from typing import List, Optional
import uuid
from datetime import datetime
from dataclasses import dataclass

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
STOCK_CHANGES_FILE = os.path.join(DATA_DIR, "stock_changes.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

def init_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(STOCK_CHANGES_FILE):
        with open(STOCK_CHANGES_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump([
                {"username": "admin", "password": "adminpass", "role": "admin"},
                {"username": "manager", "password": "managerpass", "role": "manager"}
            ], f)

@dataclass
class Product:
    id: str
    name: str
    quantity: int

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity
        }

@dataclass
class StockChange:
    id: str
    productId: str
    delta: int
    timestamp: str

    def to_dict(self):
        return {
            "id": self.id,
            "productId": self.productId,
            "delta": self.delta,
            "timestamp": self.timestamp
        }

@dataclass
class User:
    username: str
    password: str
    role: str

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "role": self.role
        }

def _load_data(file_path: str):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return json.load(f)

def _save_data(file_path: str, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def get_products(limit: Optional[int] = None, offset: Optional[int] = None) -> List[Product]:
    data = _load_data(PRODUCTS_FILE)
    products = [Product(**item) for item in data]
    if offset is not None and limit is not None:
        return products[offset:offset + limit]
    return products

def get_product(id: str) -> Optional[Product]:
    products = get_products()
    for product in products:
        if product.id == id:
            return product
    return None

def add_product(name: str, quantity: int) -> Product:
    if quantity < 0:
        raise ValueError("Количество не может быть отрицательным")

    data = _load_data(PRODUCTS_FILE)
    new_product = Product(id=str(uuid.uuid4()), name=name, quantity=quantity)
    data.append(new_product.to_dict())
    _save_data(PRODUCTS_FILE, data)
    return new_product

def update_product_stock(productId: str, delta: int) -> Product:
    data = _load_data(PRODUCTS_FILE)
    products = [Product(**item) for item in data]

    for product in products:
        if product.id == productId:
            new_quantity = product.quantity + delta
            if new_quantity < 0:
                raise ValueError("Сток не может быть отрицательным")

            product.quantity = new_quantity

            updated_data = [p.to_dict() for p in products]
            _save_data(PRODUCTS_FILE, updated_data)

            stock_changes = _load_data(STOCK_CHANGES_FILE)
            stock_changes.append(StockChange(
                id=str(uuid.uuid4()),
                productId=productId,
                delta=delta,
                timestamp=datetime.now().isoformat()
            ).to_dict())
            _save_data(STOCK_CHANGES_FILE, stock_changes)

            return product

    raise ValueError("Товар не найден")

def remove_product(id: str) -> bool:
    data = _load_data(PRODUCTS_FILE)
    updated_data = [item for item in data if item["id"] != id]

    if len(updated_data) < len(data):
        _save_data(PRODUCTS_FILE, updated_data)
        return True
    return False

def get_stock_changes() -> List[StockChange]:
    data = _load_data(STOCK_CHANGES_FILE)
    return [StockChange(**item) for item in data]

def get_user(username: str) -> Optional[User]:
    data = _load_data(USERS_FILE)
    for user in data:
        if user["username"] == username:
            return User(**user)
    return None

init_data_files()