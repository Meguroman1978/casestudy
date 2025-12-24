# Fly.ioへの強制デプロイ手順

最新の変更（率系指標の中央値集計）をFly.ioにデプロイする手順です。

## 🚀 ローカルマシンでのデプロイ手順

### ステップ1: 最新コードを取得

```bash
# casestudyディレクトリに移動（または新しくクローン）
cd /path/to/casestudy

# mainブランチの最新を取得
git checkout main
git pull origin main

# 最新のコミットを確認
git log --oneline -3
# 期待される出力:
# 6bd86ee fix: Change rate metrics aggregation from mean to median
# 4fbfeba docs: Update README with new sorting functionality
# fa46850 feat: Add sorting functionality for 5 new metrics
```

### ステップ2: Fly.ioにログイン

```bash
# Fly.ioにログイン（初回のみ）
flyctl auth login
# ブラウザが開き、Fly.ioアカウントでログイン

# ログイン確認
flyctl auth whoami
```

### ステップ3: デプロイ実行

```bash
# casestudyアプリにデプロイ
flyctl deploy --app casestudy

# または、カレントディレクトリのfly.tomlを使用
flyctl deploy
```

**デプロイには5-10分かかります。** 以下のような出力が表示されます：

```
==> Verifying app config
--> Verified app config
==> Building image
...
--> Pushing image done
==> Creating release
--> release v4 created
--> You can detach the terminal anytime without stopping the deployment
==> Deploying
...
--> v4 deployed successfully
```

### ステップ4: デプロイ確認

```bash
# アプリの状態を確認
flyctl status --app casestudy

# ログを確認（リアルタイム）
flyctl logs -f --app casestudy

# アプリをブラウザで開く
flyctl open --app casestudy
```

**期待されるログ出力**:
```
⬇️  Downloading Template.pptx from Google Slides...
✅ Template.pptx downloaded successfully (XXXXX bytes)
✅ uploads directory ready
🌐 Starting Gunicorn web server...
```

### ステップ5: 動作確認

1. https://casestudy.fly.dev/ にアクセス
2. Excelファイルをアップロード（新しい指標カラムを含む）
3. 検索を実行
4. 「並び替え」ドロップダウンから任意の指標を選択
5. ソートが正常に動作することを確認

---

## 🔧 トラブルシューティング

### 問題1: flyctlコマンドが見つからない

```bash
# flyctlをインストール
curl -L https://fly.io/install.sh | sh

# PATHに追加（.bashrcまたは.zshrcに追記）
export FLYCTL_INSTALL="/home/user/.fly"
export PATH="$FLYCTL_INSTALL/bin:$PATH"

# 反映
source ~/.bashrc  # または source ~/.zshrc
```

### 問題2: 認証エラー

```bash
# 再度ログイン
flyctl auth login

# トークンを確認
flyctl auth token
```

### 問題3: デプロイが失敗する

```bash
# 詳細ログでデプロイ
flyctl deploy --verbose --app casestudy

# ビルドキャッシュをクリアして再デプロイ
flyctl deploy --no-cache --app casestudy
```

### 問題4: Template.pptxダウンロードエラー

ログに以下のエラーが表示される場合：
```
❌ Error: GOOGLE_SLIDES_ID environment variable not set
```

**解決策**:
```bash
# 環境変数を確認
flyctl secrets list --app casestudy

# GOOGLE_SLIDES_IDを設定
flyctl secrets set GOOGLE_SLIDES_ID="1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess" --app casestudy

# アプリを再起動
flyctl apps restart casestudy
```

### 問題5: Google Slidesが非公開

**解決策**:
1. https://docs.google.com/presentation/d/1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess/edit にアクセス
2. 右上の「共有」→「リンクを知っている全員が閲覧可能」に設定
3. テストURL:
   ```bash
   curl -L "https://docs.google.com/presentation/d/1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess/export/pptx" -o test.pptx
   ls -lh test.pptx  # 1MB以上あるか確認
   ```

---

## 📋 デプロイ後のチェックリスト

- [ ] `flyctl status --app casestudy` で "Running" が表示される
- [ ] ログに `✅ Template.pptx downloaded successfully` が表示される
- [ ] https://casestudy.fly.dev/ にアクセスできる
- [ ] Excelファイルアップロードが動作する
- [ ] 新しいソート機能が動作する
- [ ] 率系指標（VIEWTHROUGH_RATE, CLICKTHROUGH_RATE, A2C_RATE）のグループ化集計が中央値になっている

---

## 🔗 参考リンク

- **Fly.io Dashboard**: https://fly.io/dashboard/casestudy
- **アプリケーションURL**: https://casestudy.fly.dev/
- **GitHubリポジトリ**: https://github.com/Meguroman1978/casestudy
- **Fly.io Docs**: https://fly.io/docs/

---

## 💡 今回の変更内容

**コミット `6bd86ee`**: 率系指標の集計を平均から中央値に変更

**変更内容**:
- `VIEWTHROUGH_RATE`, `CLICKTHROUGH_RATE`, `A2C_RATE` のグループ化集計
- **変更前**: `'mean'` (平均)
- **変更後**: `'median'` (中央値)
- **理由**: 中央値は外れ値に対してロバストで、率系指標の典型的な値をより正確に表現

**影響範囲**:
- ドメインごとにグループ化している場合のみ
- 回数系（VIDEO_VIEWS, THUMBNAIL_IMPRESSIONS）は引き続き合計値を使用
