# ========================
# app.py
# ========================

import logging
import os
from flask import Flask

from config import Config
from extensions import db, login_manager
from models.user import User
from routes.auth import auth
from routes.main import main
from routes.account import account

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(account)

with app.app_context():
    db.create_all()
    # SQLite マイグレーション: 既存テーブルへの新規カラム追加
    from sqlalchemy import text, inspect
    inspector = inspect(db.engine)
    def _add_col(table, col, typedef):
        existing = [c["name"] for c in inspector.get_columns(table)]
        if col not in existing:
            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}"))
    try:
        _add_col("user", "avatar_path", "VARCHAR(255)")
        db.session.commit()
    except Exception:
        db.session.rollback()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
