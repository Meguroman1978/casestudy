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
   - 視聴回数で降順ソート
   - CSVファイルとしてダウンロード可能

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
# - SCREENSHOT_API_TOKEN: ScreenshotAPI.netのトークン（オプション）
```

**方法2: 直接環境変数を設定**

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
export GOOGLE_SHEET_ID="your-google-sheet-id-here"
export SCREENSHOT_API_TOKEN="your-screenshot-api-token-here"  # オプション
```

**API取得方法**:
- **OpenAI API**: https://platform.openai.com/api-keys でAPIキーを取得
- **ScreenshotAPI.net**: https://screenshotapi.net/ でアカウント作成後、トークンを取得（オプション）

**重要**: セキュリティのため、これらの値は絶対にGitにコミットしないでください。`.env`ファイルは`.gitignore`に含まれています。

### 3. Template.pptxの配置

PPTXファイル生成機能を使用する場合、`Template.pptx`ファイルをプロジェクトのルートディレクトリに配置してください。

**注意**: Template.pptxは72MBの大きなファイルのため、Gitリポジトリには含まれていません（.gitignoreに記載）。

### 4. アプリケーションの起動

```bash
python app.py
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
- **ScreenshotAPI.net**: Webサイトスクリーンショットの自動挿入に使用（トークンが未設定の場合はプレースホルダーテキストが表示されます）

## ライセンス

MIT License
