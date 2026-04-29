import os

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

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


def validate_ad_data(data, part=False):
    """Функция валидации для POST и PATCH запросов"""
    errors = []

    if not all(isinstance(data.get(k), str) for k in data.keys()):
        return "Все поля должны быть строками"

    fields_to_check = ["title", "description", "owner"] if not part else data.keys()

    if "title" in fields_to_check:
        title = data.get("title", "")
        if not title.strip():
            errors.append("Заголовок не может быть пустым")
        elif len(title.strip()) > 200:
            errors.append("Заголовок превышает допустимую длину (200)")
        else:
            data["title"] = title.strip()  # Перезаписываем обрезанным значением

    if "description" in fields_to_check:
        desc = data.get("description", "")
        if not desc.strip():
            errors.append("Описание не может быть пустым")
        elif len(desc.strip()) > 300:
            errors.append("Описание превышает допустимую длину")
        else:
            data["description"] = desc.strip()

    if "owner" in fields_to_check:
        owner = data.get("owner", "")
        if not owner.strip():
            errors.append("Имя владельца не может быть пустым")
        elif len(owner.strip()) > 100:
            errors.append("Имя владельца превышает допустимую длину")
        else:
            data["owner"] = owner.strip()

    return "; ".join(errors) if errors else None


# *** Роуты ***


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
        "current_page": page,
    }), 200


# Создать объявление
@app.route("/ads", methods=["POST"])
def create_ad():
    data = request.get_json()
    if not data or not all(k in data for k in ("title", "description", "owner")):
        return jsonify({"error": "Отсутствуют обязательные поля"}), 400

    error = validate_ad_data(data, part=False)
    if error:
        return jsonify({"error": error}), 400

    ad = Ad(
        title=data["title"],
        description=data["description"],
        owner=data["owner"],
    )
    db.session.add(ad)
    db.session.commit()

    # 201 Created - новый ресурс создан
    return jsonify(ad.to_dict()), 201


# Получить одно объявление по ID
@app.route("/ads/<int:ad_id>", methods=["GET"])
def get_ad(ad_id):
    ad = db.session.get(Ad, ad_id)
    if ad is None:
        return jsonify({"error": "Объявление не найдено"}), 404
    return jsonify(ad.to_dict()), 200


# Обновить данные одного объявления по ID
@app.route("/ads/<int:ad_id>", methods=["PATCH"])
def update_ad(ad_id):
    ad = db.session.get(Ad, ad_id)
    if ad is None:
        return jsonify({"error": "Объявление не найдено"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "Нет данных для обновления"}), 400

    error = validate_ad_data(data, part=True)
    if error:
        return jsonify({"error": error}), 400

    if "title" in data:
        ad.title = data["title"]
    if "description" in data:
        ad.description = data["description"]
    if "owner" in data:
        ad.owner = data["owner"]

    db.session.commit()
    return jsonify(ad.to_dict()), 200


# Удаление одного объявления по ID
@app.route("/ads/<int:ad_id>", methods=["DELETE"])
def delete_ad(ad_id):
    ad = db.session.get(Ad, ad_id)
    if ad is None:
        return jsonify({"error": "Объявление не найдено"}), 404

    db.session.delete(ad)
    db.session.commit()
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
