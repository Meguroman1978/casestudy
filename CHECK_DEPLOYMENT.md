# デプロイ診断ガイド

## 🔍 **Render.comのログを確認する手順**

エラーメッセージ：
```
サーバーエラーが発生しました。ログを確認してください / 
Server error occurred. Please check logs.
```

このエラーは、サーバー側で500エラーが発生していることを示しています。
Render.comのログで具体的な原因を確認しましょう。

---

## 📊 **ステップ1: Render.comのログにアクセス**

### 1-1. Render.comダッシュボードを開く

1. https://render.com/ にアクセス
2. GitHubアカウントでログイン
3. ダッシュボードが表示されます

### 1-2. Web Serviceを選択

1. 左側のメニューから該当のサービスを選択
   - サービス名: `video-case-study-analyzer` または設定した名前
2. サービスの詳細ページが開きます

### 1-3. Logsタブを開く

1. 上部メニューの **「Logs」** タブをクリック
2. リアルタイムログが表示されます
3. 自動でスクロールしている場合、一時停止ボタンをクリック

---

## 🔎 **ステップ2: エラーログを探す**

### 2-1. エラー発生時刻を確認

1. アプリでエラーが発生した時刻をメモ（例: 2025-12-01 14:30）
2. ログで同じ時刻付近を探す

### 2-2. エラーパターンを探す

以下のようなログを探してください：

#### **パターンA: アプリケーションエラー**

```
="="="="="="="="="="="="="="="="="="="="="="="="="="="="="
予期しないエラーが発生: [エラーメッセージ]
エラータイプ: [エラークラス名]
Traceback (most recent call last):
  File "app.py", line XXX, in process_data
    [エラーの詳細]
  ...
="="="="="="="="="="="="="="="="="="="="="="="="="="="="="
```

#### **パターンB: 起動エラー**

```
Error: Unable to start application
ModuleNotFoundError: No module named 'XXX'
```

#### **パターンC: Google Sheets接続エラー**

```
[エラー] Google Sheet取得失敗: HTTPError: 403 Forbidden
または
ValueError: Google Sheet ID is not configured
```

#### **パターンD: Template.pptxダウンロードエラー**

```
❌ Error downloading Template.pptx: ...
```

---

## 🛠️ **ステップ3: よくあるエラーと解決方法**

### エラー1: 環境変数が設定されていない

**ログの例:**
```
ValueError: Google Sheet ID is not configured. 
Please set GOOGLE_SHEET_ID environment variable.
```

または

```
⚠️ GOOGLE_SHEET_ID not set in environment variables
```

**解決策:**

1. Render.comダッシュボードで **「Environment」** タブを開く
2. 以下の環境変数が設定されているか確認：
   ```
   OPENAI_API_KEY = [あなたのAPIキー]
   GOOGLE_SHEET_ID = 1EsNylv4Leg73lb_AXJLMBnQKkozvHhLzfVGlz4HN2Tk
   GOOGLE_SLIDES_ID = 1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess
   ```
3. 不足している場合は **「Add Environment Variable」** で追加
4. **「Save Changes」** をクリック
5. サービスが自動的に再起動します

---

### エラー2: Google Sheetsにアクセスできない

**ログの例:**
```
[エラー] Google Sheet取得失敗: HTTPError: 403 Forbidden
または
urllib.error.HTTPError: HTTP Error 403: Forbidden
```

**原因:** Google Sheetsが公開設定になっていない

**解決策:**

1. **Google Sheetsを開く**
   ```
   https://docs.google.com/spreadsheets/d/1EsNylv4Leg73lb_AXJLMBnQKkozvHhLzfVGlz4HN2Tk/edit
   ```

2. **共有設定を変更**
   - 右上の「共有」ボタンをクリック
   - 「リンクを知っている全員」に変更
   - 権限を「閲覧者」に設定
   - 「完了」をクリック

3. **確認**
   ブラウザのシークレットモードで以下にアクセス：
   ```
   https://docs.google.com/spreadsheets/d/1EsNylv4Leg73lb_AXJLMBnQKkozvHhLzfVGlz4HN2Tk/export?format=csv&gid=0
   ```
   CSVファイルがダウンロードできればOK

4. **Render.comで再デプロイ**
   - Render.comダッシュボード → **「Manual Deploy」** → **「Deploy latest commit」**

---

### エラー3: Template.pptxがダウンロードできない

**ログの例:**
```
❌ Error downloading Template.pptx: HTTPError: 403 Forbidden
または
⚠️ Warning: File size is smaller than expected
```

**原因:** Google Slidesが公開設定になっていない

**解決策:**

1. **Google Slidesを開く**
   ```
   https://docs.google.com/presentation/d/1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess/edit
   ```

2. **共有設定を変更**
   - 右上の「共有」ボタンをクリック
   - 「リンクを知っている全員」に変更
   - 権限を「閲覧者」に設定
   - 「完了」をクリック

3. **確認**
   ブラウザで以下にアクセス：
   ```
   https://docs.google.com/presentation/d/1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess/export/pptx
   ```
   PPTXファイルがダウンロードできればOK

4. **Render.comで再デプロイ**

---

### エラー4: OpenAI APIエラー

**ログの例:**
```
OpenAI API error: 401 Unauthorized
または
OpenAI API error: 429 Too Many Requests
```

**解決策:**

1. **APIキーを確認**
   - https://platform.openai.com/api-keys にアクセス
   - キーが有効か確認
   - 必要に応じて新しいキーを生成

2. **使用制限を確認**
   - https://platform.openai.com/usage にアクセス
   - クレジット残高を確認
   - レート制限に達していないか確認

3. **環境変数を更新**
   - Render.comの Environment タブ
   - `OPENAI_API_KEY` を新しいキーに更新

---

### エラー5: Pythonパッケージのインストールエラー

**ログの例:**
```
ModuleNotFoundError: No module named 'pandas'
または
ERROR: Could not build wheels for pandas
```

**解決策:**

1. **requirements.txtを確認**
   - すべての依存関係が記載されているか確認

2. **Python バージョンを確認**
   - `runtime.txt` の内容: `python-3.11.11`
   - Render.comのログで使用されているPythonバージョンを確認

3. **ビルドキャッシュをクリア**
   - Render.comダッシュボード → **「Settings」** タブ
   - 下にスクロールして **「Clear build cache & deploy」** をクリック

---

### エラー6: メモリ不足

**ログの例:**
```
MemoryError
または
Killed (OOM)
```

**原因:** 無料プランは512MB制限

**解決策:**

1. **アップロードファイルのサイズを小さくする**
   - Excelファイルのデータ量を減らす

2. **プランをアップグレード**
   - Starter プラン（$7/月）は1GB
   - Pro プラン（$25/月）は2GB以上

---

## 📝 **ステップ4: ログをコピーして共有**

問題が解決しない場合、以下の情報を共有してください：

### 1. エラーログ（前後50行）

```
[ここにRender.comのログを貼り付け]
```

### 2. 環境変数の設定状況

- [ ] OPENAI_API_KEY: 設定済み / 未設定
- [ ] GOOGLE_SHEET_ID: 設定済み / 未設定
- [ ] GOOGLE_SLIDES_ID: 設定済み / 未設定

### 3. 公開設定の確認

- [ ] Google Sheets: 公開済み / 非公開
- [ ] Google Slides: 公開済み / 非公開

### 4. デプロイ状態

- [ ] ビルド: 成功 / 失敗
- [ ] サービス: 起動中 / 停止
- [ ] URL: アクセス可能 / アクセス不可

---

## 🔄 **ステップ5: 再デプロイ**

設定を変更した後は必ず再デプロイ：

1. Render.comダッシュボード
2. 該当サービスを開く
3. 右上の **「Manual Deploy」** → **「Deploy latest commit」**
4. ログを確認しながら待つ（5-10分）
5. デプロイ完了後にアプリをテスト

---

## ✅ **デプロイ成功の確認**

以下が表示されればデプロイ成功：

```
✅ Template.pptx downloaded successfully (XXX bytes)
[INFO] Starting gunicorn
[INFO] Listening at: http://0.0.0.0:10000
[INFO] Booting worker with pid: XXX
```

---

## 📞 **まだ解決しない場合**

上記のログと設定状況を共有してください。
具体的な解決策を提案します。
