# =========================
# routes/account.py
# =========================

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.user import Address, Payment

account = Blueprint("account", __name__, url_prefix="/account")


# =========================
# 住所管理
# =========================
@account.route("/address/add", methods=["GET", "POST"])
@login_required
def add_address():
    next_url = request.args.get("next") or url_for("account.addresses")

    if request.method == "POST":
        recipient_name = request.form.get("recipient_name", "").strip()
        postal_code    = request.form.get("postal_code", "").strip()
        prefecture     = request.form.get("prefecture", "").strip()
        city           = request.form.get("city", "").strip()
        street         = request.form.get("street", "").strip()
        phone          = request.form.get("phone", "").strip()
        label          = request.form.get("label", "その他")
        next_url_form  = request.form.get("next_url", next_url)

        if not all([recipient_name, postal_code, prefecture, city, street, phone]):
            flash("すべての項目を入力してください。", "error")
            return render_template("account/add_address.html", next_url=next_url_form)

        addr = Address(
            user_id        = current_user.id,
            recipient_name = recipient_name,
            postal_code    = postal_code,
            prefecture     = prefecture,
            city           = city,
            street         = street,
            phone          = phone,
            label          = label,
            is_default     = len(current_user.addresses) == 0,
        )
        db.session.add(addr)
        db.session.commit()
        flash("住所を追加しました。", "success")
        return redirect(next_url_form)

    return render_template("account/add_address.html", next_url=next_url)


@account.route("/addresses")
@login_required
def addresses():
    addrs = Address.query.filter_by(user_id=current_user.id).all()
    return render_template("account/addresses.html", addresses=addrs)


@account.route("/address/<int:addr_id>/delete", methods=["POST"])
@login_required
def delete_address(addr_id):
    addr = Address.query.get_or_404(addr_id)
    if addr.user_id != current_user.id:
        flash("権限がありません。", "error")
        return redirect(url_for("account.addresses"))
    db.session.delete(addr)
    db.session.commit()
    flash("住所を削除しました。", "success")
    return redirect(url_for("account.addresses"))


# =========================
# 支払い方法管理
# =========================
@account.route("/payment/add", methods=["GET", "POST"])
@login_required
def add_payment():
    next_url = request.args.get("next") or url_for("account.payments")

    if request.method == "POST":
        card_name    = request.form.get("card_name", "").strip()
        card_brand   = request.form.get("card_brand", "").strip()
        last4        = request.form.get("last4", "").strip()
        expiry_month = request.form.get("expiry_month", "")
        expiry_year  = request.form.get("expiry_year", "")
        next_url_form = request.form.get("next_url", next_url)

        if not all([card_name, card_brand, last4, expiry_month, expiry_year]):
            flash("すべての項目を入力してください。", "error")
            return render_template("account/add_payment.html", next_url=next_url_form)

        try:
            expiry_month = int(expiry_month)
            expiry_year  = int(expiry_year)
            if not (1 <= expiry_month <= 12):
                raise ValueError
        except ValueError:
            flash("有効期限の形式が正しくありません。", "error")
            return render_template("account/add_payment.html", next_url=next_url_form)

        if len(last4) != 4 or not last4.isdigit():
            flash("カード番号下4桁は半角数字4文字で入力してください。", "error")
            return render_template("account/add_payment.html", next_url=next_url_form)

        pay = Payment(
            user_id      = current_user.id,
            card_name    = card_name,
            card_brand   = card_brand,
            last4        = last4,
            expiry_month = expiry_month,
            expiry_year  = expiry_year,
            is_default   = len(current_user.payments) == 0,
        )
        db.session.add(pay)
        db.session.commit()
        flash("支払い方法を追加しました。", "success")
        return redirect(next_url_form)

    return render_template("account/add_payment.html", next_url=next_url)


@account.route("/payments")
@login_required
def payments():
    pays = Payment.query.filter_by(user_id=current_user.id).all()
    return render_template("account/payments.html", payments=pays)


@account.route("/payment/<int:pay_id>/delete", methods=["POST"])
@login_required
def delete_payment(pay_id):
    pay = Payment.query.get_or_404(pay_id)
    if pay.user_id != current_user.id:
        flash("権限がありません。", "error")
        return redirect(url_for("account.payments"))
    db.session.delete(pay)
    db.session.commit()
    flash("支払い方法を削除しました。", "success")
    return redirect(url_for("account.payments"))
