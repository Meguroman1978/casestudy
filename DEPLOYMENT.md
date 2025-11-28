# Render.com デプロイメントガイド

## 🔒 セキュアな環境変数の設定

このガイドでは、機密情報を安全に管理しながらRender.comにデプロイする方法を説明します。

---

## ステップ1: Render.comでWeb Serviceを作成

### 1-1. Render.comにアクセス
- https://render.com/ にアクセス
- GitHubアカウントでサインイン

### 1-2. 新しいWeb Serviceを作成
1. ダッシュボードで **「New +」** → **「Web Service」** をクリック
2. GitHubリポジトリ **`Meguroman1978/casestudy`** を選択
3. **「Connect」** をクリック

---

## ステップ2: デプロイ設定

以下の設定を入力してください：

| 設定項目 | 値 |
|---------|-----|
| **Name** | `video-case-study-analyzer` |
| **Region** | `Singapore` または最寄り |
| **Branch** | `genspark_ai_developer` または `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && playwright install --with-deps chromium` |
| **Start Command** | `python download_template_from_slides.py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120` |
| **Instance Type** | `Free` または `Starter` |

---

## ステップ3: 環境変数の設定（重要）

**「Environment」セクションで以下の環境変数を追加してください：**

### 必須の環境変数

#### 1. PYTHON_VERSION
```
Key: PYTHON_VERSION
Value: 3.11.0
```

#### 2. OPENAI_API_KEY
```
Key: OPENAI_API_KEY
Value: [あなたのOpenAI APIキー - .envファイルから確認してください]
```

**注意:** 実際のAPIキーは `/home/user/webapp/.env` ファイルに保存されています。
このファイルはGitにコミットされていないため、ローカル環境でのみ確認できます。

#### 3. GOOGLE_SHEET_ID
```
Key: GOOGLE_SHEET_ID
Value: 1EsNylv4Leg73lb_AXJLMBnQKkozvHhLzfVGlz4HN2Tk
```

#### 4. GOOGLE_SLIDES_ID
```
Key: GOOGLE_SLIDES_ID
Value: 1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess
```

### 環境変数の入力方法

1. 「Environment Variables」セクションまでスクロール
2. 「Add Environment Variable」ボタンをクリック
3. 上記の各Key/Valueペアを入力
4. 4つすべて追加したことを確認

**🔒 セキュリティ保証:**
- これらの値はRender.comのサーバー側で暗号化されて保存されます
- GitHubリポジトリには一切含まれません
- ビルドログやアプリケーションログには表示されません
- Render.comのダッシュボードでのみアクセス可能です

---

## ステップ4: Google Slidesの公開設定を確認

### 4-1. Google Slidesにアクセス
https://docs.google.com/presentation/d/1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess/edit

### 4-2. 共有設定を変更
1. 右上の「共有」ボタンをクリック
2. 「リンクを知っている全員」に変更
3. 権限を「閲覧者」に設定
4. 「完了」をクリック

### 4-3. エクスポートをテスト（オプション）
ブラウザのシークレットモードで以下のURLにアクセス：
```
https://docs.google.com/presentation/d/1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess/export/pptx
```
→ PPTXファイルがダウンロードできればOKです

---

## ステップ5: デプロイを実行

1. すべての設定を確認
2. **「Create Web Service」** ボタンをクリック
3. ビルドが自動的に開始されます

**ビルド時間:**
- 初回: 5-10分（Playwrightインストールに時間がかかります）
- 2回目以降: 3-5分

**ログの確認:**
- デプロイページでリアルタイムログを確認できます
- エラーが発生した場合はログをチェックしてください

---

## ステップ6: デプロイ完了後の確認

### 6-1. 公開URLにアクセス
デプロイが完了すると、以下のような公開URLが表示されます：
```
https://video-case-study-analyzer.onrender.com
```

### 6-2. 動作確認
- [ ] ホームページが表示される
- [ ] Excelファイルのアップロードが動作する
- [ ] データのフィルタリングが動作する
- [ ] PPTX生成機能が動作する

---

## 🔧 トラブルシューティング

### エラー1: ビルドが失敗する
```
Build Command failed with exit code 1
```

**解決策:**
- ログで具体的なエラーメッセージを確認
- requirements.txtの依存関係を確認
- Python バージョンが3.11.0であることを確認

---

### エラー2: Template.pptxがダウンロードできない
```
❌ Error downloading Template.pptx
```

**解決策:**
1. Google Slidesの共有設定を確認
   - 「リンクを知っている全員」が閲覧可能になっているか
2. GOOGLE_SLIDES_ID が正しいか確認
   - 値: `1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess`
3. エクスポートURLをブラウザで直接テスト

---

### エラー3: OpenAI API エラー
```
OpenAI API error: Invalid API key
```

**解決策:**
1. OPENAI_API_KEY が正しく設定されているか確認
2. APIキーが有効か確認
   - https://platform.openai.com/api-keys でキーを確認
3. APIキーの使用制限を確認

---

### エラー4: アプリが起動しない
```
Application failed to start
```

**解決策:**
1. Start Command が正しいか確認
2. 環境変数がすべて設定されているか確認
3. ログで詳細なエラーメッセージを確認

---

## 📊 無料プランの制限

Render.comの無料プランには以下の制限があります：

- **スリープモード**: 15分間アクセスがないとアプリがスリープ
- **再起動時間**: スリープ後の再起動に30秒～1分程度
- **メモリ**: 512MB
- **ビルド時間**: 月間400分まで
- **帯域幅**: 月間100GB

---

## 🔄 更新とメンテナンス

### コードを更新してデプロイ
1. ローカルでコードを変更
2. Gitにコミット: `git commit -m "update: description"`
3. GitHubにプッシュ: `git push origin genspark_ai_developer`
4. Render.comが自動的に再デプロイします

### 環境変数を更新
1. Render.comダッシュボードで該当のWeb Serviceを開く
2. 「Environment」タブをクリック
3. 変数を編集または追加
4. 「Save Changes」をクリック
5. サービスが自動的に再起動します

---

## ✅ セキュリティチェックリスト

デプロイ前に以下を確認してください：

- [ ] `.env` ファイルが `.gitignore` に含まれている
- [ ] 環境変数がGitHubリポジトリにコミットされていない
- [ ] Render.comで環境変数を正しく設定した
- [ ] Google Slidesが適切な共有設定になっている
- [ ] OpenAI APIキーが有効である
- [ ] デプロイログでエラーがないことを確認

---

## 📞 サポート

問題が解決しない場合：
1. Render.comのログを確認
2. GitHubのissuesで質問
3. Render.comのサポートに問い合わせ

---

**デプロイ成功を祈ります！ 🚀**
