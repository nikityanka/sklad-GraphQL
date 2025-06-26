import requests
import json
import websockets
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

PORT = os.getenv("PORT", 8000)
SERVER_URL = f"http://localhost:{PORT}/graphql"
WS_URL = f"ws://localhost:{PORT}/graphql"

def print_response(response):
    print(json.dumps(response, indent=2, ensure_ascii=False))

def run_query(query, variables=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.post(
        SERVER_URL,
        json={"query": query, "variables": variables} if variables else {"query": query},
        headers=headers
    )
    try:
        return response.json()
    except json.JSONDecodeError:
        print(f"Ошибка формата JSON в ответе: {response.text}")
        return {"data": None, "errors": [{"message": "Некорректный JSON-ответ от сервера"}]}


def login(username, password):
    mutation = """
    mutation Login($username: String!, $password: String!) {
        login(username: $username, password: $password) {
            token
            userRole
        }
    }
    """
    variables = {"username": username, "password": password}
    response = run_query(mutation, variables)
    if response.get("errors"):
        print("Ошибка входа:", response["errors"])
        return None

    token = response["data"]["login"]["token"]
    print(f"Received token: {token}")
    return token

def list_products(token=None):
    query = """
    query {
        listProducts {
            id
            name
            quantity
        }
    }
    """
    response = run_query(query, token=token)
    print("Список товаров:")
    print_response(response)

def add_product(name, quantity, token=None):
    mutation = """
    mutation AddProduct($input: AddProductInput!) {
        addProduct(input: $input) {
            id
            name
            quantity
        }
    }
    """
    variables = {
        "input": {
            "name": name,
            "quantity": quantity
        }
    }
    response = run_query(mutation, variables, token)
    print("Добавлен товар:")
    print_response(response)

def update_stock(product_id, delta, token=None):
    mutation = """
    mutation UpdateStock($productId: ID!, $delta: Int!) {
        updateStock(productId: $productId, delta: $delta) {
            id
            name
            quantity
        }
    }
    """
    variables = {
        "productId": product_id,
        "delta": delta
    }
    response = run_query(mutation, variables, token)
    print("Обновлен запас:")
    print_response(response)

async def stock_alert_subscription(threshold=5, token=None):
    subscription = """
    subscription StockAlerts($threshold: Int!) {
        streamStockAlerts(threshold: $threshold) {
            productId
            productName
            currentQuantity
            message
            timestamp
        }
    }
    """

    ws_url = WS_URL
    if token:
        ws_url += f"?token={token}"

    async with websockets.connect(
            ws_url,
            subprotocols=["graphql-ws"]
    ) as ws:
        await ws.send(json.dumps({
            "type": "connection_init",
            "payload": {}
        }))

        response = await ws.recv()
        print("Ответ подключения:", response)

        await ws.send(json.dumps({
            "id": "1",
            "type": "start",
            "payload": {
                "query": subscription,
                "variables": {"threshold": threshold}
            }
        }))

        while True:
            message = await ws.recv()
            data = json.loads(message)
            if data.get("type") == "data":
                print("\nОповещение о запасе:")
                print_response(data["payload"]["data"]["streamStockAlerts"])

async def main():
    print("=== Логин администратора ===")
    admin_token = login("admin", "adminpass")
    if not admin_token:
        print("Не удалось войти как администратор")
        return

    print("\n=== Добавление нового товара (требуются права admin) ===")
    add_product("Ноутбук", 10, token=admin_token)

    print("\n=== Логин менеджера ===")
    manager_token = login("manager", "managerpass")
    if not manager_token:
        print("Не удалось войти как менеджер")
        return

    print("\n=== Получение списка товаров ===")
    list_products(token=manager_token)

    print("\n=== Обновление запасов (требуются права manager) ===")
    response = run_query("{ listProducts { id name } }", token=manager_token)

    if response.get("data") and response["data"].get("listProducts"):
        products = response["data"]["listProducts"]
        if products:
            update_stock(products[0]["id"], -6, token=manager_token)
        else:
            print("Нет товаров для обновления")
    else:
        print("Ошибка получения списка товаров")

    print("\n=== Защищенные ресурсы (требуются права admin) ===")
    protected_query = """
    query {
        protectedResource
    }
    """
    protected_res = run_query(protected_query, token=admin_token)
    print("Результат защищенного запроса (admin):")
    print_response(protected_res)

    print("\n=== Попытка защищенного запроса без прав ===")
    protected_res = run_query(protected_query, token=manager_token)
    print("Результат (manager):")
    print_response(protected_res)

    print("\n=== Запуск подписки на оповещения (порог=5) ===")
    print("Ожидание оповещений... Нажмите Ctrl+C для остановки")
    try:
        await stock_alert_subscription(5, token=manager_token)
    except KeyboardInterrupt:
        print("\nПодписка остановлена")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nКлиент остановлен")