from app import app, db

with app.app_context():
    try:
        db.create_all()
        print("Таблицы успешно созданы или уже существуют")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
