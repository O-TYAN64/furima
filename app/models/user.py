# =========================
# models/user.py
# =========================

from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id                 = db.Column(db.Integer, primary_key=True)
    username           = db.Column(db.String(32), unique=True, nullable=False)
    email              = db.Column(db.String(254), unique=True, nullable=False)
    password           = db.Column(db.String(128), nullable=False)
    display_name       = db.Column(db.String(64), nullable=True)
    bio                = db.Column(db.String(300), nullable=True)
    avatar_path        = db.Column(db.String(255), nullable=True)
    stripe_customer_id = db.Column(db.String(64), nullable=True)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    items         = db.relationship("Item", back_populates="seller", foreign_keys="Item.seller_id")
    purchases     = db.relationship("Item", back_populates="buyer",  foreign_keys="Item.buyer_id")
    likes         = db.relationship("Like", back_populates="user")
    addresses     = db.relationship("Address", back_populates="user", cascade="all, delete-orphan")
    payments      = db.relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    comments      = db.relationship("Comment", back_populates="user")
    notifications = db.relationship("Notification", back_populates="user",
                                    cascade="all, delete-orphan",
                                    order_by="Notification.created_at.desc()")

    def get_display_name(self):
        return self.display_name or self.username

    def unread_notification_count(self):
        return sum(1 for n in self.notifications if not n.is_read)


class Address(db.Model):
    __tablename__ = "address"

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    label          = db.Column(db.String(20), default="その他")
    recipient_name = db.Column(db.String(64), nullable=False)
    postal_code    = db.Column(db.String(10), nullable=False)
    prefecture     = db.Column(db.String(10), nullable=False)
    city           = db.Column(db.String(50), nullable=False)
    street         = db.Column(db.String(100), nullable=False)
    phone          = db.Column(db.String(20), nullable=False)
    is_default     = db.Column(db.Boolean, default=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="addresses")

    def full_address(self):
        return f"{self.prefecture}{self.city}{self.street}"


class Payment(db.Model):
    __tablename__ = "payment"

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    card_name      = db.Column(db.String(64), nullable=False)
    card_brand     = db.Column(db.String(20), nullable=False)
    last4          = db.Column(db.String(4), nullable=False)
    expiry_month   = db.Column(db.Integer, nullable=False)
    expiry_year    = db.Column(db.Integer, nullable=False)
    stripe_pm_id   = db.Column(db.String(64), nullable=True)   # pm_xxxx
    is_default     = db.Column(db.Boolean, default=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="payments")

    def expiry(self):
        return f"{self.expiry_month:02d}/{str(self.expiry_year)[-2:]}"

    def is_stripe(self):
        return bool(self.stripe_pm_id)


class Notification(db.Model):
    __tablename__ = "notification"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message    = db.Column(db.String(200), nullable=False)
    url        = db.Column(db.String(200), nullable=True)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")
