# =========================
# models/item.py
# =========================

from extensions import db
from datetime import datetime

class Item(db.Model):
    __tablename__ = "item"

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price       = db.Column(db.Integer, nullable=False)
    category    = db.Column(db.String(50), nullable=False, default="その他")
    condition   = db.Column(db.String(30), nullable=False, default="目立った傷や汚れなし")
    image_path  = db.Column(db.String(255), nullable=True)
    status      = db.Column(db.String(20), default="selling")  # selling / sold

    seller_id   = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    buyer_id    = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    sold_at     = db.Column(db.DateTime, nullable=True)

    seller      = db.relationship("User", back_populates="items",     foreign_keys=[seller_id])
    buyer       = db.relationship("User", back_populates="purchases", foreign_keys=[buyer_id])
    likes       = db.relationship("Like", back_populates="item", cascade="all, delete-orphan")
    images      = db.relationship("ItemImage", back_populates="item", cascade="all, delete-orphan",
                                  order_by="ItemImage.order")
    comments    = db.relationship("Comment", back_populates="item", cascade="all, delete-orphan",
                                  order_by="Comment.created_at")

    def like_count(self):
        return len(self.likes)

    def is_liked_by(self, user):
        if user is None or not user.is_authenticated:
            return False
        return any(like.user_id == user.id for like in self.likes)

    def all_images(self):
        paths = []
        if self.image_path:
            paths.append(self.image_path)
        for img in self.images:
            paths.append(img.path)
        return paths


class ItemImage(db.Model):
    __tablename__ = "item_image"

    id      = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    path    = db.Column(db.String(255), nullable=False)
    order   = db.Column(db.Integer, default=0)

    item = db.relationship("Item", back_populates="images")


class Like(db.Model):
    __tablename__ = "like"

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)

    user    = db.relationship("User", back_populates="likes")
    item    = db.relationship("Item", back_populates="likes")

    __table_args__ = (db.UniqueConstraint("user_id", "item_id"),)


class Comment(db.Model):
    __tablename__ = "comment"

    id         = db.Column(db.Integer, primary_key=True)
    item_id    = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body       = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship("Item", back_populates="comments")
    user = db.relationship("User", back_populates="comments")


CATEGORIES = [
    "レディース", "メンズ", "キッズ・ベビー","パソコン・周辺機器",
    "家電・スマホ", "おもちゃ・ホビー", "スポーツ・アウトドア",
    "本・漫画", "ゲーム", "コスメ・美容",
    "インテリア・住まい", "ハンドメイド", "チケット", "その他"
]

CONDITIONS = [
    "新品・未使用", "未使用に近い", "目立った傷や汚れなし",
    "やや傷や汚れあり", "傷や汚れあり", "全体的に状態が悪い"
]
