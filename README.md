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

### 2. アプリケーションの起動

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

Google Sheet URL: https://docs.google.com/spreadsheets/d/1EsNylv4Leg73lb_AXJLMBnQKkozvHhLzfVGlz4HN2Tk/edit

## 注意事項

- アップロードファイルのサイズ上限: 16MB
- 対応ファイル形式: .xlsx, .xls
- Google Sheetは公開設定されている必要があります
- 一時アップロードファイルは処理後に自動削除されます

## ライセンス

MIT License
