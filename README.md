# 気象レポート 降水量ハイライター

PDFをアップロードするだけで、降水量が0より大きいセルを水色の枠でハイライトするWebアプリです。

---

## デプロイ手順（Render.com 無料プラン）

### ステップ1：GitHubにコードをアップロード

1. https://github.com にアクセスしてアカウントを作成（無料）
2. 右上の「+」→「New repository」をクリック
3. Repository name に `weather-highlight-app` と入力
4. 「Create repository」をクリック
5. 「uploading an existing file」をクリック
6. このフォルダ内のファイルをすべてドラッグ＆ドロップ
   - app.py
   - requirements.txt
   - render.yaml
   - static/index.html  ← staticフォルダごとアップロード
7. 「Commit changes」をクリック

### ステップ2：Render.comにデプロイ

1. https://render.com にアクセスしてGitHubアカウントでサインアップ
2. 「New +」→「Web Service」をクリック
3. 「Connect a repository」でGitHubと連携
4. 先ほど作った `weather-highlight-app` リポジトリを選択
5. 以下を確認して「Create Web Service」をクリック：
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - Instance Type: Free
6. デプロイ完了まで3〜5分待つ
7. 画面上部に表示される `https://weather-highlight-app-xxxx.onrender.com` がアプリのURL

### ステップ3：スタッフに共有

- 上記のURLをメールやSlackでスタッフに共有するだけです
- スタッフはブラウザでURLを開き、PDFをドロップするだけで使えます
- インストール不要、アカウント不要

---

## 注意事項

- 無料プランでは15分間アクセスがないとサーバーがスリープします
  - 最初のアクセス時に30秒〜1分ほど起動時間がかかる場合があります
  - 有料プラン（$7/月）にアップグレードするとスリープなしになります
- アップロードできるPDFは20MBまでです
- PDFはサーバー上で処理後すぐに削除され、保存されません

---

## ファイル構成

```
weather-highlight-app/
├── app.py              # サーバー処理（Python/Flask）
├── requirements.txt    # 依存ライブラリ
├── render.yaml         # Renderデプロイ設定
├── static/
│   └── index.html      # フロントエンド画面
└── README.md           # この手順書
```
