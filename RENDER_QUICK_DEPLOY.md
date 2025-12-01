# 🚀 Render.com クイックデプロイガイド

このガイドでは、最短でRender.comにデプロイする手順を説明します。

---

## 📋 必要な情報

デプロイ前に以下の情報を準備してください：

| 項目 | 値 | 場所 |
|-----|-----|------|
| OpenAI API Key | `[.envファイルを確認]` | `/home/user/webapp/.env` |
| Google Sheet ID | `1EsNylv4Leg73lb_AXJLMBnQKkozvHhLzfVGlz4HN2Tk` | 設定済み |
| Google Slides ID | `1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess` | 設定済み |

---

## ⚡ デプロイ手順（5ステップ）

### ステップ1: Render.comにアクセス
1. https://render.com/ にアクセス
2. GitHubアカウントでサインイン

### ステップ2: Web Serviceを作成
1. **「New +」** → **「Web Service」**
2. リポジトリ **`Meguroman1978/casestudy`** を選択
3. ブランチ **`genspark_ai_developer`** を選択

### ステップ3: 基本設定
- **Name**: `video-case-study-analyzer`
- **Region**: `Singapore`
- **Runtime**: `Python 3`
- **Instance Type**: `Free`

### ステップ4: ビルド設定（コピー&ペースト）

**Build Command:**
```bash
pip install -r requirements.txt && playwright install --with-deps chromium
```

**Start Command:**
```bash
python download_template_from_slides.py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120
```

### ステップ5: 環境変数を設定

**「Add Environment Variable」で3つの変数を追加:**

**注意:** Python 3.11.11は `runtime.txt` で自動設定されるため、PYTHON_VERSIONは不要です。

```
Key: OPENAI_API_KEY
Value: [.envファイルから取得 - 以下のコマンドで確認できます]

Key: GOOGLE_SHEET_ID
Value: 1EsNylv4Leg73lb_AXJLMBnQKkozvHhLzfVGlz4HN2Tk

Key: GOOGLE_SLIDES_ID
Value: 1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess
```

### OpenAI API Keyの確認方法

ローカル環境で以下のコマンドを実行：
```bash
cat /home/user/webapp/.env | grep OPENAI_API_KEY
```

出力例：
```
OPENAI_API_KEY=sk-proj-AZAgplTV...（実際のキー）
```

この値をコピーしてRender.comの環境変数に設定してください。

---

## ✅ デプロイ実行

すべての設定を完了したら：
1. **「Create Web Service」** をクリック
2. 5-10分待つ（初回ビルド）
3. 公開URLが表示されたら完了！

---

## 🔍 デプロイ後の確認

### 公開URLにアクセス
```
https://video-case-study-analyzer.onrender.com
```

### 動作確認
- [ ] トップページが表示される
- [ ] Excelファイルがアップロードできる
- [ ] データのフィルタリングが動作する
- [ ] PPTX生成機能が動作する

---

## ❓ よくある質問

### Q1: ビルドに失敗します
**A:** ログを確認して、エラーメッセージを確認してください。多くの場合、環境変数の設定ミスです。

### Q2: Template.pptxがダウンロードできません
**A:** Google Slidesが「リンクを知っている全員が閲覧可」に設定されているか確認してください。

### Q3: OpenAI APIエラーが出ます
**A:** OPENAI_API_KEYが正しく設定されているか確認してください。

### Q4: アプリがスリープします
**A:** 無料プランでは15分間アクセスがないとスリープします。これは正常な動作です。

---

## 📖 詳細ガイド

より詳しい情報は `DEPLOYMENT.md` を参照してください。

---

**デプロイ成功を祈ります！ 🎉**
