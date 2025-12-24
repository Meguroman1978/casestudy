# 動画事例データ分析アプリ

ExcelファイルとGoogle Sheetを連携して、動画事例データを分析・フィルタリングするウェブアプリケーションです。

## 機能

1. **データアップロード**
   - Top Video Views per URL (ショート動画) のExcelファイルをアップロード
   - Top Live Stream Views per URL (ライブ配信) のExcelファイルをアップロード

2. **フィルタリング**
   - 事例タイプ: ショート動画事例 / ライブ配信事例
   - 業界名: Google Sheetから取得した業界リスト
   - 国: Google Sheetから取得した国リスト

3. **データ連携**
   - Google Sheetと「Business Id」をキーとしてデータマージ
   - 会社名、業界名、国、URLを統合して表示

4. **結果表示**
   - フィルタリングされたデータをテーブル形式で表示
   - **5種類の指標でソート可能** (NEW!)
     - VIDEO_VIEWS（再生回数）
     - THUMBNAIL_IMPRESSIONS（サムネイル表示回数）
     - VIEWTHROUGH_RATE（ビュースルー率）
     - CLICKTHROUGH_RATE（クリック率）
     - A2C_RATE（カート追加率）
   - 各指標で「高→低」または「低→高」の昇順・降順ソート対応
   - CSVファイル・Excelファイルとしてダウンロード可能

## 技術スタック

- **Backend**: Python 3, Flask
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **データ処理**: pandas, openpyxl
- **外部連携**: Google Sheets (CSVエクスポート形式)

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

PPTX生成機能でOpenAI APIとGoogle Sheetsを使用するため、必要な環境変数を設定してください：

**方法1: .envファイルを使用（推奨）**

```bash
cp .env.example .env
# .envファイルを編集して以下を設定:
# - OPENAI_API_KEY: OpenAI APIキー（必須）
# - GOOGLE_SHEET_ID: Google SheetsのID（URLの/d/と/editの間の文字列）（必須）
# - GOOGLE_SLIDES_ID: Google SlidesのID（テンプレート用）（必須）
```

**方法2: 直接環境変数を設定**

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
export GOOGLE_SHEET_ID="your-google-sheet-id-here"
export GOOGLE_SLIDES_ID="your-google-slides-id-here"
```

**API取得方法**:
- **OpenAI API**: https://platform.openai.com/api-keys でAPIキーを取得（必須：Website description生成用）

**注意**: スクリーンショット機能は**Playwright**を使用しているため、外部APIキーは不要です

**重要**: セキュリティのため、これらの値は絶対にGitにコミットしないでください。`.env`ファイルは`.gitignore`に含まれています。

### 3. Google Slidesテンプレートの設定

PPTXファイル生成機能は**Google Slides**をテンプレートとして使用します。

**Google Slidesの準備:**
1. テンプレート用のGoogle Slidesを作成または準備
2. Google SlidesのURLからIDを取得
   - 例: `https://docs.google.com/presentation/d/1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess/edit`
   - IDは `/d/` と `/edit` の間の部分: `1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess`
3. **重要**: Google Slidesを「リンクを知っている全員が閲覧可」に設定してください
   - 右上の「共有」→「リンクを知っている全員」→「閲覧者」
4. 環境変数 `GOOGLE_SLIDES_ID` にIDを設定

**ローカル開発環境:**
```bash
export GOOGLE_SLIDES_ID="1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess"
python download_template_from_slides.py  # Template.pptxをダウンロード
```

**本番環境（Render.com等）:**
- 環境変数 `GOOGLE_SLIDES_ID` を設定するだけで、デプロイ時に自動的にTemplate.pptxがダウンロードされます

### 4. アプリケーションの起動

**初回起動時（Template.pptxのダウンロード）:**
```bash
python download_template_from_slides.py  # Google SlidesからTemplate.pptxをダウンロード
python app.py
```

**2回目以降:**
```bash
python app.py  # Template.pptxが既に存在する場合はダウンロード不要
```

アプリケーションは `http://localhost:5000` で起動します。

## 使用方法

1. ブラウザで `http://localhost:5000` にアクセス
2. 2つのExcelファイルをアップロード:
   - Top Video Views per URL (ショート動画)
   - Top Live Stream Views per URL (ライブ配信)
3. フィルタリング条件を選択:
   - 事例タイプ (必須)
   - 業界名 (オプション)
   - 国 (オプション)
4. 「データを分析」ボタンをクリック
5. 結果がテーブル形式で表示されます
6. 必要に応じて「CSVでダウンロード」ボタンで結果をダウンロード

## ファイル構造

```
/home/user/webapp/
├── app.py              # Flaskアプリケーション本体
├── requirements.txt    # Python依存パッケージ
├── templates/
│   └── index.html     # フロントエンドUI
├── uploads/           # アップロードファイル一時保存用
└── README.md          # このファイル
```

## データフォーマット

### アップロードするExcelファイル

両ファイルとも以下の列が必要です:
- `Page Url`: 動画のURL
- `Business Id`: ビジネスID (Google Sheetとの連携キー)
- `Business Name`: ビジネス名
- `Business Country`: 国
- `Channel Id`: チャンネルID
- `Channel Name`: チャンネル名
- `Video Views`: 視聴回数

### Google Sheet

以下の列が必要です:
- `Business Id`: ビジネスID (連携キー)
- `Account: Account Name`: 会社名
- `Account: Industry`: 業界名
- `Account: Owner Territory`: 国

Google Sheetは環境変数`GOOGLE_SHEET_ID`で指定されます（セキュリティのため直接URLは記載しません）。

## 注意事項

- アップロードファイルのサイズ上限: 16MB
- 対応ファイル形式: .xlsx, .xls
- Google Sheetは公開設定されている必要があります
- 一時アップロードファイルは処理後に自動削除されます
- **OpenAI API**: PPTX生成時のWebサイト分析に必須（APIキーが無効な場合はフォールバックテキストが使用されます）
- **Playwright**: Webサイトスクリーンショットの自動取得に使用（外部APIキー不要、Chromiumブラウザで動作）
- **フォントサイズ**: Website descriptionは自動的に10.5ptに設定されます

## デプロイ（本番環境への公開）

### Render.comへのデプロイ（推奨）

1. **Render.comアカウント作成**
   - https://render.com/ にアクセス
   - GitHubアカウントでサインアップ

2. **新しいWeb Serviceを作成**
   - Dashboard → "New +" → "Web Service"
   - GitHubリポジトリを接続: `Meguroman1978/casestudy`
   - Branch: `main`

3. **Google Slidesの準備（重要）**
   - テンプレート用のGoogle Slidesを準備
   - Google SlidesのURLからIDを取得（例: `1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess`）
   - **必須**: Google Slidesを「リンクを知っている全員が閲覧可」に設定
     - 右上の「共有」→「リンクを知っている全員」→「閲覧者」

4. **環境変数の設定**
   Render.comのダッシュボードで以下の環境変数を設定：
   ```
   OPENAI_API_KEY=（新しく生成したOpenAI APIキー - 古いキーは無効化済み）
   GOOGLE_SHEET_ID=1EsNylv4Leg73lb_AXJLMBnQKkozvHhLzfVGlz4HN2Tk
   GOOGLE_SLIDES_ID=1KpJaTV4jgaUUDFhZg59KGGzaJCsO-rggv12NWRdkess
   ```
   
   **注意:** 
   - Python 3.11.11は `runtime.txt` で自動設定されます（PYTHON_VERSIONは不要）
   - これらの値は絶対にGitHubにコミットしないでください
   - Render.comのダッシュボードで安全に設定します

5. **デプロイ実行**
   - "Create Web Service"をクリック
   - 自動的にビルド＆デプロイが開始されます
   - デプロイ完了後、公開URLが発行されます（例: https://your-app.onrender.com）

**注意**: Render.comの無料プランでは、15分間アクセスがないとアプリが自動的にスリープ状態になります。再アクセス時は起動に30秒～1分程度かかります。

### その他のデプロイオプション

- **Railway.app**: https://railway.app/ (無料クレジット付き)
- **Heroku**: https://www.heroku.com/ (有料プラン必要)
- **Google Cloud Run**: コンテナベースのデプロイ
- **AWS Elastic Beanstalk**: AWSでのPythonアプリホスティング

## ライセンス

MIT License
