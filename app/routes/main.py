# =========================
# routes/main.py
# =========================

import os, uuid, logging
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError
import json as _json
from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify, current_app, abort)
from flask_login import login_required, current_user
from extensions import db
from models.item import Item, ItemImage, Like, Comment, CATEGORIES, CONDITIONS
from models.user import User, Address, Payment, Notification
from datetime import datetime

main = Blueprint("main", __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
PER_PAGE = 20


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return f"images/items/{filename}"


def _notify(user_id, message, url=None):
    db.session.add(Notification(user_id=user_id, message=message, url=url))


# ======================== トップ ========================
@main.route("/")
def index():
    q          = request.args.get("q", "").strip()
    category   = request.args.get("category", "")
    sort       = request.args.get("sort", "new")
    show_sold  = request.args.get("show_sold", "0")
    price_min  = request.args.get("price_min", "").strip()
    price_max  = request.args.get("price_max", "").strip()
    page       = request.args.get("page", 1, type=int)

    query = Item.query
    if show_sold != "1":
        query = query.filter_by(status="selling")
    if q:
        query = query.filter(Item.title.contains(q))
    if category:
        query = query.filter_by(category=category)
    if price_min:
        try:
            query = query.filter(Item.price >= int(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            query = query.filter(Item.price <= int(price_max))
        except ValueError:
            pass

    if sort == "price_asc":
        query = query.order_by(Item.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Item.price.desc())
    elif sort == "popular":
        query = query.outerjoin(Like).group_by(Item.id).order_by(db.func.count(Like.id).desc())
    else:
        query = query.order_by(Item.created_at.desc())

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    items      = pagination.items

    return render_template("index.html",
                           items=items, pagination=pagination,
                           categories=CATEGORIES,
                           selected_category=category, selected_sort=sort,
                           show_sold=show_sold, q=q,
                           price_min=price_min, price_max=price_max)


# ======================== 商品詳細 ========================
@main.route("/item/<int:item_id>")
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    related = (Item.query
               .filter_by(category=item.category, status="selling")
               .filter(Item.id != item_id)
               .order_by(Item.created_at.desc())
               .limit(6).all())
    return render_template("item_detail.html", item=item, related=related)


# ======================== 出品 ========================
@main.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        title     = request.form.get("title", "").strip()
        desc      = request.form.get("description", "").strip()
        price_str = request.form.get("price", "0").replace(",", "")
        category  = request.form.get("category", "").strip()
        condition = request.form.get("condition", "目立った傷や汚れなし")
        files     = request.files.getlist("images")

        if not title:
            flash("商品名は必須です。", "error")
            return render_template("sell.html", categories=CATEGORIES, conditions=CONDITIONS)
        if not category or category not in CATEGORIES:
            flash("カテゴリを選択してください。", "error")
            return render_template("sell.html", categories=CATEGORIES, conditions=CONDITIONS)
        try:
            price = int(price_str)
            if price < 300:
                raise ValueError
        except ValueError:
            flash("価格は300円以上の整数で入力してください。", "error")
            return render_template("sell.html", categories=CATEGORIES, conditions=CONDITIONS)

        valid_files = [f for f in files if f and f.filename and allowed_file(f.filename)]

        image_path = None
        if valid_files:
            image_path = save_image(valid_files[0])

        item = Item(title=title, description=desc, price=price, category=category,
                    condition=condition, image_path=image_path, seller_id=current_user.id)
        db.session.add(item)
        db.session.flush()

        for i, f in enumerate(valid_files[1:5], start=1):
            db.session.add(ItemImage(item_id=item.id, path=save_image(f), order=i))

        db.session.commit()
        logger.info("SELL item_id=%s seller_id=%s title=%s", item.id, current_user.id, item.title)
        flash("商品を出品しました！", "success")
        return redirect(url_for("main.item_detail", item_id=item.id))

    return render_template("sell.html", categories=CATEGORIES, conditions=CONDITIONS)


# ======================== 商品編集 ========================
@main.route("/item/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.seller_id != current_user.id:
        flash("権限がありません。", "error")
        return redirect(url_for("main.index"))
    if item.status == "sold":
        flash("売り切れ商品は編集できません。", "error")
        return redirect(url_for("main.mypage"))

    if request.method == "POST":
        title     = request.form.get("title", "").strip()
        desc      = request.form.get("description", "").strip()
        price_str = request.form.get("price", "0").replace(",", "")
        category  = request.form.get("category", "").strip()
        condition = request.form.get("condition", item.condition)
        files     = request.files.getlist("images")

        if not title:
            flash("商品名は必須です。", "error")
            return render_template("edit_item.html", item=item, categories=CATEGORIES, conditions=CONDITIONS)
        if not category or category not in CATEGORIES:
            flash("カテゴリを選択してください。", "error")
            return render_template("edit_item.html", item=item, categories=CATEGORIES, conditions=CONDITIONS)
        try:
            price = int(price_str)
            if price < 300:
                raise ValueError
        except ValueError:
            flash("価格は300円以上の整数で入力してください。", "error")
            return render_template("edit_item.html", item=item, categories=CATEGORIES, conditions=CONDITIONS)

        valid_files = [f for f in files if f and f.filename and allowed_file(f.filename)]

        if valid_files:
            # 既存の追加画像を削除して新しい画像に差し替え
            for img in item.images:
                db.session.delete(img)
            item.image_path = save_image(valid_files[0])
            db.session.flush()
            for i, f in enumerate(valid_files[1:4], start=1):
                db.session.add(ItemImage(item_id=item.id, path=save_image(f), order=i))

        item.title = title; item.description = desc; item.price = price
        item.category = category; item.condition = condition
        db.session.commit()
        logger.info("EDIT item_id=%s seller_id=%s", item.id, current_user.id)
        flash("商品情報を更新しました。", "success")
        return redirect(url_for("main.item_detail", item_id=item.id))

    return render_template("edit_item.html", item=item, categories=CATEGORIES, conditions=CONDITIONS)


# ======================== チェックアウト ========================
@main.route("/item/<int:item_id>/checkout")
@login_required
def checkout(item_id):
    item = Item.query.get_or_404(item_id)
    if item.status != "selling":
        flash("この商品はすでに売り切れです。", "error")
        return redirect(url_for("main.item_detail", item_id=item_id))
    if item.seller_id == current_user.id:
        flash("自分の出品商品は購入できません。", "error")
        return redirect(url_for("main.item_detail", item_id=item_id))

    addresses    = Address.query.filter_by(user_id=current_user.id).all()
    payments     = Payment.query.filter_by(user_id=current_user.id).all()
    default_addr = next((a for a in addresses if a.is_default), None) or (addresses[0] if addresses else None)
    default_pay  = next((p for p in payments  if p.is_default),  None) or (payments[0]  if payments  else None)

    return render_template("checkout.html", item=item, addresses=addresses, payments=payments,
                           default_addr=default_addr, default_pay=default_pay)


# ======================== 購入 ========================
@main.route("/item/<int:item_id>/buy", methods=["POST"])
@login_required
def buy(item_id):
    item = Item.query.get_or_404(item_id)
    if item.status != "selling":
        flash("この商品はすでに売り切れです。", "error")
        return redirect(url_for("main.item_detail", item_id=item_id))
    if item.seller_id == current_user.id:
        flash("自分の出品商品は購入できません。", "error")
        return redirect(url_for("main.item_detail", item_id=item_id))

    address_id = request.form.get("address_id")
    payment_id = request.form.get("payment_id")
    if not address_id or not payment_id:
        flash("住所と支払い方法を選択してください。", "error")
        return redirect(url_for("main.checkout", item_id=item_id))

    addr = Address.query.get(address_id)
    pay  = Payment.query.get(payment_id)
    if not addr or addr.user_id != current_user.id:
        flash("住所が無効です。", "error")
        return redirect(url_for("main.checkout", item_id=item_id))
    if not pay or pay.user_id != current_user.id:
        flash("支払い方法が無効です。", "error")
        return redirect(url_for("main.checkout", item_id=item_id))

    item.status   = "sold"
    item.buyer_id = current_user.id
    item.sold_at  = datetime.utcnow()

    _notify(item.seller_id,
            f"「{item.title}」が売れました！",
            url_for("main.mypage"))

    db.session.commit()
    logger.info("BUY item_id=%s buyer_id=%s price=%s addr_id=%s pay_id=%s",
                item.id, current_user.id, item.price, addr.id, pay.id)
    flash("購入が完了しました！ありがとうございます🎉", "success")
    return redirect(url_for("main.purchase_complete", item_id=item_id))


# ======================== 購入完了 ========================
@main.route("/item/<int:item_id>/complete")
@login_required
def purchase_complete(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template("purchase_complete.html", item=item)


# ======================== いいね ========================
@main.route("/item/<int:item_id>/like", methods=["POST"])
@login_required
def toggle_like(item_id):
    item = Item.query.get_or_404(item_id)
    like = Like.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if like:
        db.session.delete(like)
        liked = False
    else:
        db.session.add(Like(user_id=current_user.id, item_id=item_id))
        liked = True
        if item.seller_id != current_user.id:
            _notify(item.seller_id,
                    f"{current_user.get_display_name()} さんが「{item.title}」をいいねしました",
                    url_for("main.item_detail", item_id=item_id))
    db.session.commit()
    return jsonify({"liked": liked, "count": item.like_count()})


# ======================== コメント投稿 ========================
@main.route("/item/<int:item_id>/comment", methods=["POST"])
@login_required
def add_comment(item_id):
    item = Item.query.get_or_404(item_id)
    body = request.form.get("body", "").strip()
    if not body:
        flash("コメントを入力してください。", "error")
        return redirect(url_for("main.item_detail", item_id=item_id))
    if len(body) > 500:
        flash("コメントは500文字以内で入力してください。", "error")
        return redirect(url_for("main.item_detail", item_id=item_id))

    comment = Comment(item_id=item_id, user_id=current_user.id, body=body)
    db.session.add(comment)

    if item.seller_id != current_user.id:
        _notify(item.seller_id,
                f"{current_user.get_display_name()} さんが「{item.title}」にコメントしました",
                url_for("main.item_detail", item_id=item_id))
    db.session.commit()
    flash("コメントを投稿しました。", "success")
    return redirect(url_for("main.item_detail", item_id=item_id) + "#comments")


# ======================== コメント削除 ========================
@main.route("/item/<int:item_id>/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(item_id, comment_id):
    comment = Comment.query.get_or_404(comment_id)
    item    = Item.query.get_or_404(item_id)
    if comment.user_id != current_user.id and item.seller_id != current_user.id:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash("コメントを削除しました。", "success")
    return redirect(url_for("main.item_detail", item_id=item_id) + "#comments")


# ======================== マイページ ========================
@main.route("/mypage")
@login_required
def mypage():
    selling = Item.query.filter_by(seller_id=current_user.id, status="selling").order_by(Item.created_at.desc()).all()
    sold    = Item.query.filter_by(seller_id=current_user.id, status="sold").order_by(Item.sold_at.desc()).all()
    bought  = Item.query.filter_by(buyer_id=current_user.id,  status="sold").order_by(Item.sold_at.desc()).all()
    liked   = [like.item for like in current_user.likes]
    return render_template("mypage.html", selling=selling, sold=sold, bought=bought, liked=liked)


# ======================== ユーザープロフィール ========================
@main.route("/user/<username>")
def user_profile(username):
    user  = User.query.filter_by(username=username).first_or_404()
    items = (Item.query
             .filter_by(seller_id=user.id, status="selling")
             .order_by(Item.created_at.desc()).all())
    sold_count = Item.query.filter_by(seller_id=user.id, status="sold").count()
    return render_template("user_profile.html", profile_user=user,
                           items=items, sold_count=sold_count)


# ======================== 通知一覧 ========================
@main.route("/notifications")
@login_required
def notifications():
    notifs = (Notification.query
              .filter_by(user_id=current_user.id)
              .order_by(Notification.created_at.desc())
              .limit(50).all())
    unread_ids = [n.id for n in notifs if not n.is_read]
    if unread_ids:
        Notification.query.filter(Notification.id.in_(unread_ids)).update(
            {"is_read": True}, synchronize_session=False)
        db.session.commit()
    return render_template("notifications.html", notifications=notifs)


# ======================== 設定 ========================
@main.route("/setting", methods=["GET", "POST"])
@login_required
def setting():
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        bio          = request.form.get("bio", "").strip()
        avatar_file  = request.files.get("avatar")

        if len(display_name) > 64:
            flash("表示名は64文字以内で入力してください。", "error")
            return render_template("setting.html")
        if len(bio) > 300:
            flash("自己紹介は300文字以内で入力してください。", "error")
            return render_template("setting.html")

        current_user.display_name = display_name or current_user.username
        current_user.bio          = bio or None

        if avatar_file and avatar_file.filename and allowed_file(avatar_file.filename):
            current_user.avatar_path = save_image(avatar_file)

        db.session.commit()
        flash("プロフィールを更新しました。", "success")
        return redirect(url_for("main.setting"))
    return render_template("setting.html")


# ======================== 郵便番号プロキシ ========================
def _fetch_json(url, timeout=5):
    with urlopen(url, timeout=timeout) as resp:
        return _json.loads(resp.read().decode())

@main.route("/api/postal")
def postal_lookup():
    zipcode = request.args.get("zipcode", "").replace("-", "").strip()
    if not zipcode.isdigit() or len(zipcode) != 7:
        return jsonify({"error": "郵便番号は7桁の数字で入力してください"}), 400

    # --- API 1: zipcloud ---
    try:
        data = _fetch_json(
            f"https://zipcloud.ibsreg.com/api/search?zipcode={zipcode}")
        if data.get("results"):
            r = data["results"][0]
            return jsonify({"prefecture": r["address1"],
                            "city": r["address2"] + r["address3"]})
    except Exception:
        logger.warning("zipcloud failed for %s", zipcode)

    # --- API 2: zipaddress.net (フォールバック) ---
    try:
        data = _fetch_json(
            f"https://api.zipaddress.net/?zipcode={zipcode}")
        if data.get("code") == 200 and data.get("data"):
            d = data["data"]
            return jsonify({"prefecture": d["pref"],
                            "city": d["city"] + d.get("town", "")})
    except Exception:
        logger.warning("zipaddress.net failed for %s", zipcode)

    # --- API 3: postcode.teraren.com (第2フォールバック) ---
    try:
        data = _fetch_json(
            f"https://postcode.teraren.com/postcodes/{zipcode}.json")
        if data.get("prefecture"):
            return jsonify({"prefecture": data["prefecture"],
                            "city": data.get("city", "") + data.get("town", "")})
    except Exception:
        logger.warning("postcode.teraren.com failed for %s", zipcode)

    return jsonify({"error": "住所の検索に失敗しました。手動で入力してください"}), 503


# ======================== 商品削除 ========================
@main.route("/item/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.seller_id != current_user.id:
        flash("権限がありません。", "error")
        return redirect(url_for("main.index"))
    if item.status == "sold":
        flash("売り切れ商品は削除できません。", "error")
        return redirect(url_for("main.mypage"))
    logger.info("DELETE item_id=%s seller_id=%s", item.id, current_user.id)
    db.session.delete(item)
    db.session.commit()
    flash("商品を削除しました。", "success")
    return redirect(url_for("main.mypage"))
