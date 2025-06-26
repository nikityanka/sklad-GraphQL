# Управление складом с использованием GraphQL

## Описание
Сервис управления складскими запасами с GraphQL API позволяет:
- Добавлять, обновлять и удалять товары
- Отслеживать изменения запасов в реальном времени
- Получать оповещения о низком уровне запасов
- Управлять доступом через систему ролей (admin, manager)

## Стек технологий
- Язык программирования: Python
- GraphQL-библиотека: Strawberry
- Веб-фреймворк: FastAPI + Uvicorn
- Хранилище данных: JSON-файлы
- Аутентификация: JWT (JSON Web Tokens)
- Клиент: Python (requests, websockets)

## Установка
1. Склонируйте репозиторий:
```bash
git clone https://github.com/your-username/inventory-management
cd inventory-management
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте окружение:
```bash
PORT=8000
JWT_SECRET=gfdnjgfgdkslkge
```

## Запуск сервера
```bash
cd server
python server.py
```
Сервер будет доступен по адресу: `http://localhost:8000/graphql`

## Примеры запросов

### 1. Аутентификация
Получение JWT токена:
```graphql
mutation Login {
  login(username: "admin", password: "adminpass") {
    token
    userRole
  }
}
```

**Ожидаемый ответ:**
```json
{
  "data": {
    "login": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "userRole": "admin"
    }
  }
}
```

### 2. Добавление нового товара
```graphql
mutation AddProduct {
  addProduct(input: {name: "Ноутбук", quantity: 10}) {
    id
    name
    quantity
  }
}
```

**Ожидаемый ответ:**
```json
{
  "data": {
    "addProduct": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Ноутбук",
      "quantity": 10
    }
  }
}
```

### 3. Получение списка товаров
```graphql
query ListProducts {
  listProducts {
    id
    name
    quantity
  }
}
```

**Ожидаемый ответ:**
```json
{
  "data": {
    "listProducts": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Ноутбук",
        "quantity": 10
      },
      {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "name": "Смартфон",
        "quantity": 15
      }
    ]
  }
}
```

### 4. Обновление запасов
```graphql
mutation UpdateStock {
  updateStock(productId: "550e8400-e29b-41d4-a716-446655440000", delta: -3) {
    id
    name
    quantity
  }
}
```

**Ожидаемый ответ:**
```json
{
  "data": {
    "updateStock": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Ноутбук",
      "quantity": 7
    }
  }
}
```

### 5. Подписка на оповещения о запасах
```graphql
subscription StockAlerts {
  streamStockAlerts(threshold: 5) {
    productId
    productName
    currentQuantity
    message
    timestamp
  }
}
```

**Ожидаемые события:**
```json
{
  "data": {
    "streamStockAlerts": {
      "productId": "550e8400-e29b-41d4-a716-446655440000",
      "productName": "Ноутбук",
      "currentQuantity": 4,
      "message": "Товар Ноутбук заканчивается! Текущее количество: 4",
      "timestamp": "2025-06-26T15:30:00.123456"
    }
  }
}
```

## Аутентификация
Для доступа к защищенным ресурсам:
1. Выполните мутацию `login` для получения JWT токена
2. Добавьте токен в заголовки запросов:
```
Authorization: Bearer <ваш_токен>
```

Для WebSocket-подписок добавьте токен в параметры подключения:
```
ws://localhost:8000/graphql?token=<ваш_токен>
```

## Клиентские примеры
В папке `client/` находится скрипт `client.py`, который демонстрирует все операции:

```bash
cd client
python client.py
```

Скрипт выполняет:
1. Аутентификацию под разными ролями
2. Добавление нового товара
3. Обновление запасов
4. Запросы к защищенным ресурсам
5. Подписку на оповещения о запасах

## Структура проекта
```
.
├── schema/
│   └── schema.graphql                # SDL схема
├── server/
│   ├── server.py                     # точка входа сервера
│   ├── resolvers.py                  # резолверы GraphQL
│   ├── models.py                     # модели данных и работа с JSON
│   └── data/                         # хранилище данных
│       ├── products.json
│       ├── stock_changes.json
│       └── users.json
├── client/
│   └── client.py                     # клиент для тестирования API
├── .env                              # конфигурация (порт, секреты)
└── README.md                         # документация
```

## Особенности реализации
1. **Ролевая модель доступа**:
   - Администратор: полный доступ
   - Менеджер: управление запасами, просмотр товаров
   - Гость: только просмотр товаров

2. **Реальные подписки**:
   - Реализованы через WebSockets
   - Периодическая проверка запасов (каждые 10 секунд)
   - Фильтрация по пороговому значению

3. **Хранение данных**:
   - Автоматическая инициализация JSON-файлов
   - Атомарные операции чтения/записи
   - Валидация данных на уровне моделей

4. **Обработка ошибок**:
   - Валидация входных данных
   - Обработка авторизационных ошибок
   - Защита от отрицательных запасов