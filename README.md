# Flask Ads API

REST API для управления объявлениями на Flask + PostgreSQL.

## Возможности

- Создание, просмотр, обновление и удаление объявлений
- Пагинация списка объявлений
- Валидация данных

## Запуск

```bash
pip install -r requirements.txt
cp .env_example .env  # настройте переменные окружения
python app.py
```

Сервер запустится на `http://localhost:5000`.

## API endpoints

| Метод | URL              | Описание                |
|-------|------------------|-------------------------|
| GET   | `/ads`           | Список объявлений       |
| POST  | `/ads`           | Создать объявление      |
| GET   | `/ads/<id>`      | Получить объявление     |
| PATCH | `/ads/<id>`      | Обновить объявление     |
| DELETE| `/ads/<id>`      | Удалить объявление      |

## Пример запроса

```bash
# Создать объявление
curl -X POST http://localhost:5000/ads \
  -H "Content-Type: application/json" \
  -d '{"title": "Продам телефон", "description": "iPhone 15", "owner": "Иван"}'

# Получить список (с пагинацией)
curl "http://localhost:5000/ads?page=1&per_page=10"
```
