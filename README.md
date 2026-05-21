# ふりま — フリマアプリ

Flask 製のフリーマーケットアプリです。商品の出品・購入・いいね・コメントなど、フリマアプリの主要機能を備えています。

---

## 機能一覧

| カテゴリ | 機能 |
|---|---|
| 認証 | 会員登録 / ログイン / ログアウト |
| 商品 | 出品（最大4枚の画像）/ 編集 / 削除 / 詳細閲覧 |
| 検索・絞込 | キーワード検索 / カテゴリ / 価格レンジ / ソート（新着・人気・価格）/ 売り切れ表示 |
| 購入 | 購入手続き / 住所選択 / 支払い方法選択 / 購入完了 |
| いいね | いいね / いいね取り消し（Ajax） |
| コメント | 商品へのコメント投稿・削除（出品者・投稿者） |
| 通知 | いいね・購入・コメント時に出品者へ通知 |
| アカウント | プロフィール編集 / アバター画像アップロード |
| 住所管理 | 住所の追加・削除 / 郵便番号から住所を自動入力 |
| 支払い管理 | クレジットカード情報の追加・削除 |
| マイページ | 出品中 / 売れた商品 / 購入した商品 / いいね一覧 |
| プロフィール | 他ユーザーの公開プロフィールページ |
| ページネーション | 20件ごとのページ分割 |

---

## 技術スタック

- **バックエンド:** Python 3.12+ / Flask 3.1
- **ORM:** Flask-SQLAlchemy / SQLite
- **認証:** Flask-Login
- **フロントエンド:** Jinja2 / Vanilla JS / CSS カスタム
- **外部 API:** zipcloud（郵便番号 → 住所変換）

---

## ディレクトリ構成

```
furima/
├── requirements.txt
└── app/
    ├── app.py            # アプリエントリーポイント・DB マイグレーション
    ├── config.py         # 設定
    ├── extensions.py     # db / login_manager
    ├── database.db       # SQLite データベース（自動生成）
    ├── models/
    │   ├── user.py       # User / Address / Payment / Notification
    │   └── item.py       # Item / ItemImage / Like / Comment
    ├── routes/
    │   ├── auth.py       # 登録・ログイン・ログアウト
    │   ├── main.py       # 商品・購入・コメント・通知・プロフィール
    │   └── account.py    # 住所・支払い管理
    ├── static/
    │   ├── css/style.css
    │   ├── js/app.js
    │   └── images/items/ # アップロード画像
    └── templates/
        ├── base.html
        ├── index.html            # トップ（商品一覧）
        ├── item_detail.html      # 商品詳細・コメント
        ├── sell.html             # 出品フォーム
        ├── edit_item.html        # 商品編集
        ├── checkout.html         # 購入手続き
        ├── purchase_complete.html
        ├── mypage.html
        ├── setting.html
        ├── user_profile.html     # 公開プロフィール
        ├── notifications.html    # 通知一覧
        ├── login.html
        ├── register.html
        ├── account/
        │   ├── add_address.html
        │   ├── addresses.html
        │   ├── add_payment.html
        │   └── payments.html
        └── partials/
            └── item_card.html
```

---

## セットアップ

### 1. リポジトリをクローン（またはフォルダに移動）

```bash
cd C:\furima
```

### 2. 仮想環境を作成・有効化

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 4. アプリを起動

```bash
cd app
python app.py
```

ブラウザで [http://localhost:5000](http://localhost:5000) を開きます。

> データベース（`database.db`）と画像保存ディレクトリは初回起動時に自動生成されます。

---

## 環境変数

| 変数名 | 説明 | デフォルト |
|---|---|---|
| `SECRET_KEY` | Flask セッション署名キー | `dev-secret-key-change-in-production` |

本番環境では必ず `SECRET_KEY` を強力なランダム文字列に変更してください。

```bash
export SECRET_KEY="your-secure-random-key"
```

---

## 主要 URL

| URL | 説明 |
|---|---|
| `/` | トップ（商品一覧・検索・絞込） |
| `/sell` | 商品出品 |
| `/item/<id>` | 商品詳細・コメント |
| `/item/<id>/checkout` | 購入手続き |
| `/mypage` | マイページ |
| `/user/<username>` | ユーザー公開プロフィール |
| `/notifications` | 通知一覧 |
| `/setting` | アカウント設定 |
| `/register` | 会員登録 |
| `/login` | ログイン |

---

## データベース構成

```
user         ユーザー（アバター・自己紹介含む）
address      配送先住所
payment      クレジットカード情報
item         出品商品
item_image   商品の追加画像（最大3枚）
like         いいね
comment      コメント
notification 通知
```

---

## 注意事項

- 支払い処理は**モック**です。実際の決済は行われません。
- 本番運用時は SQLite を PostgreSQL 等に移行することを推奨します。
- アップロード画像は `app/static/images/items/` に保存されます。本番では S3 等の外部ストレージの利用を検討してください。
