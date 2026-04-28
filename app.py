import os

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

# Настройка подключения к PostgreSQL
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # Формируем URL из отдельных переменных
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "ads_db")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{user}:{password}@{host}:{port}/{db}"
    )

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Модель объявления
class Ad(db.Model):
    __tablename__ = "ads"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    owner = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "owner": self.owner,
        }


# Создание таблиц при первом запуске
with app.app_context():
    db.create_all()


# Получить список объявлений
@app.route("/ads", methods=["GET"])
def list_ads():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Ограничение максимума выдачи
    per_page = min(per_page, 100)

    ads = Ad.query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "ads": [ad.to_dict() for ad in ads.items],
        "total": ads.total,
        "pages": ads.pages,
        "current_page": page
    }), 200


# Создать объявление
@app.route("/ads", methods=["POST"])
def create_ad():
    data = request.get_json()
    if not data or "title" not in data or "description" not in data or "owner" not in data:
        return jsonify({"error": "Отсутствуют обязательные поля"}), 400
    if not data["title"].strip() or not data["description"].strip() or not data["owner"].strip():
        return jsonify({"error": "Пустые значения недопустимы"}), 400
    if len(data["title"]) > 200:
        return jsonify({"error": "Заголовок превышает допустимую длину"}), 400
    if len(data["description"]) > 300:
        return jsonify({"error": "Описание превышает допустимую длину"}), 400
    if len(data["owner"]) > 100:
        return jsonify({"error": "Имя владельца слишком большое"}), 400

    ad = Ad(
        title=data['title'].strip(),
        description=data['description'].strip(),
        owner=data['owner'].strip()
    )
    db.session.add(ad)
    db.session.commit()

    # 201 Created - новый ресурс создан
    return jsonify(ad.to_dict()), 201


@app.route("/ads/<int:ad_id>", methods=["GET"])
def get_ad(ad_id):
    ad = db.session.get(Ad, ad_id)
    if ad is None:
        return jsonify({"error": "Объявление не найдено"}), 404
    return jsonify(ad.to_dict()), 200


@app.route("/ads/<int:ad_id>", methods=["PATCH"])
def update_ad(ad_id):
    ad = db.session.get(Ad, ad_id)
    if ad is None:
        return jsonify({"error": "Объявление не найдено"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error":"Нет данных для обновления"}), 400
    if "title" in data and data["title"].strip():
        ad.title = data["title"].strip()
    if "description" in data and data["description"].strip():
        ad.description = data["description"].strip()
    if "owner" in data and data["owner"].strip():
        ad.owner = data["owner"].strip()

    db.session.commit()
    return jsonify(ad.to_dict()), 200


@app.route("/ads/<int:ad_id>", methods=["DELETE"])
def delete_ad(ad_id):
    ad = db.session.get(Ad, ad_id)
    if ad is None:
        return jsonify({"error": "Объявление не найдено"}), 404

    db.session.delete(ad)
    db.session.commit()
    return jsonify({"message": "Объявление удалено"}), 200


if __name__ == "__main__":
    app.run(debug=True)
