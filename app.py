import os
import traceback
import logging
import requests
import re
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from werkzeug.utils import secure_filename

# ロギング設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

# Google Sheets設定
GOOGLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1EsNylv4Leg73lb_AXJLMBnQKkozvHhLzfVGlz4HN2Tk/edit'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_google_sheet_data():
    """Google Sheetからデータを取得する"""
    try:
        logger.info("[STEP 1] Google Sheetからデータを取得中...")
        # 公開されているシートの場合、認証なしで読み取り可能
        # CSVエクスポートURLを使用
        sheet_id = '1EsNylv4Leg73lb_AXJLMBnQKkozvHhLzfVGlz4HN2Tk'
        gid = '0'
        csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'
        
        df = pd.read_csv(csv_url)
        logger.info(f"[STEP 1 完了] Google Sheet取得成功: {len(df)}行")
        logger.debug(f"Google Sheet カラム: {df.columns.tolist()}")
        logger.debug(f"Business Id データ型: {df['Business Id'].dtype}")
        logger.debug(f"Business Id サンプル: {df['Business Id'].head(3).tolist()}")
        
        # Business Idを数値型に変換
        df['Business Id'] = pd.to_numeric(df['Business Id'], errors='coerce')
        logger.info(f"Business Idを数値型に変換: {df['Business Id'].dtype}")
        
        return df
    except Exception as e:
        logger.error(f"[エラー] Google Sheet取得失敗: {e}")
        logger.error(traceback.format_exc())
        return None

def merge_data(video_df, live_df, sheet_df, case_type, industry, country):
    """データをマージしてフィルタリングする"""
    try:
        logger.info("[STEP 2] データマージ処理開始")
        logger.info(f"選択された事例タイプ: {case_type}, 業界: {industry}, 国: {country}")
        
        # 事例タイプに応じて使用するデータフレームを選択
        if case_type == 'short_video':
            main_df = video_df.copy()
            logger.info("ショート動画データを使用")
        else:  # live_stream
            main_df = live_df.copy()
            logger.info("ライブ配信データを使用")
        
        logger.debug(f"選択データ: {len(main_df)}行")
        logger.debug(f"選択データ Business Id データ型: {main_df['Business Id'].dtype}")
        logger.debug(f"選択データ Business Id サンプル: {main_df['Business Id'].head(3).tolist()}")
        logger.debug(f"Google Sheet Business Id データ型: {sheet_df['Business Id'].dtype}")
        logger.debug(f"Google Sheet Business Id サンプル: {sheet_df['Business Id'].head(3).tolist()}")
        
        # Business Idのデータ型を統一（両方を数値型に）
        main_df['Business Id'] = pd.to_numeric(main_df['Business Id'], errors='coerce')
        sheet_df['Business Id'] = pd.to_numeric(sheet_df['Business Id'], errors='coerce')
        
        logger.info("Business Idのデータ型を統一完了")
        
        # Business Idをキーとしてマージ
        logger.info("[STEP 3] データマージ実行中...")
        merged_df = main_df.merge(
            sheet_df[['Business Id', 'Account: Account Name', 'Account: Industry', 'Account: Owner Territory']],
            on='Business Id',
            how='left'
        )
        logger.info(f"[STEP 3 完了] マージ完了: {len(merged_df)}行")
        
        # マージ結果の確認
        matched_count = merged_df['Account: Account Name'].notna().sum()
        logger.info(f"マッチング成功: {matched_count}/{len(merged_df)}行")
        
        # フィルタリング
        logger.info("[STEP 4] フィルタリング実行中...")
        before_filter = len(merged_df)
        
        if industry != 'none':
            merged_df = merged_df[merged_df['Account: Industry'] == industry]
            logger.info(f"業界フィルター適用 ({industry}): {before_filter}行 → {len(merged_df)}行")
            before_filter = len(merged_df)
        
        if country != 'none':
            merged_df = merged_df[merged_df['Account: Owner Territory'] == country]
            logger.info(f"国フィルター適用 ({country}): {before_filter}行 → {len(merged_df)}行")
        
        logger.info(f"[STEP 4 完了] フィルタリング完了: {len(merged_df)}行")
        
        # 必要な列だけを抽出
        logger.info("[STEP 5] 結果データ整形中...")
        result_df = merged_df[[
            'Account: Account Name',
            'Account: Industry',
            'Account: Owner Territory',
            'Page Url',
            'Video Views'
        ]].copy()
        
        # 列名を日本語に変更
        result_df.columns = ['会社名', '業界名', '国', 'URL', '視聴回数']
        
        # NaNを空文字列に変換
        result_df = result_df.fillna('')
        
        # 視聴回数で降順ソート
        result_df = result_df.sort_values('視聴回数', ascending=False)
        
        logger.info(f"[STEP 5 完了] 最終結果: {len(result_df)}行")
        logger.debug(f"結果のサンプル:\n{result_df.head(3)}")
        
        return result_df
    except Exception as e:
        logger.error(f"[エラー] データマージ失敗: {e}")
        logger.error(traceback.format_exc())
        return None

@app.route('/')
def index():
    """トップページ"""
    return render_template('index.html')

@app.route('/api/get-options', methods=['GET'])
def get_options():
    """業界名と国のオプションを取得"""
    try:
        sheet_df = get_google_sheet_data()
        if sheet_df is None:
            return jsonify({'error': 'Google Sheetからデータを取得できませんでした'}), 500
        
        # ユニークな業界名と国を取得（空でないもの）
        industries = sorted(sheet_df['Account: Industry'].dropna().unique().tolist())
        countries = sorted(sheet_df['Account: Owner Territory'].dropna().unique().tolist())
        
        return jsonify({
            'industries': industries,
            'countries': countries
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_fw_tag_in_url(url):
    """指定されたURLのソースコードに<fw-タグが含まれているかチェック"""
    try:
        logger.info(f"Checking <fw- tag for URL: {url}")
        # タイムアウトを設定してページを取得
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        html_content = response.text
        
        # <fw- で始まるタグを検索
        has_fw_tag = bool(re.search(r'<fw-[\w-]+', html_content, re.IGNORECASE))
        logger.info(f"<fw- tag found: {has_fw_tag}")
        
        return has_fw_tag, html_content
    except Exception as e:
        logger.error(f"Error checking <fw- tag: {e}")
        return False, None

@app.route('/api/check-fw-tag', methods=['GET'])
def api_check_fw_tag():
    """URLの<fw-タグチェックとスクリーンショット情報を返すAPI"""
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({'error': 'URL parameter is required'}), 400
        
        has_fw_tag, html_content = check_fw_tag_in_url(url)
        
        # スクリーンショットURL（要件5用）
        # 実際のスクリーンショット取得は外部サービスを使用する想定
        # ここではダミーのスクリーンショットURLを返す
        screenshot_url = None
        if has_fw_tag:
            # 例: screenshot APIサービスを使用
            # screenshot_url = f"https://api.screenshotmachine.com/?key=YOUR_KEY&url={url}&dimension=1024x768"
            # または自前でスクリーンショットを生成
            screenshot_url = f"https://via.placeholder.com/400x300?text=Screenshot+of+{urlparse(url).hostname}"
        
        return jsonify({
            'has_fw_tag': has_fw_tag,
            'screenshot_url': screenshot_url
        })
    except Exception as e:
        logger.error(f"Error in check_fw_tag API: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/process', methods=['POST'])
def process_data():
    """アップロードされたファイルを処理"""
    try:
        logger.info("="*60)
        logger.info("新しい検索リクエスト開始")
        logger.info("="*60)
        
        # ファイルのチェック
        if 'video_file' not in request.files or 'live_file' not in request.files:
            logger.warning("ファイルがアップロードされていません")
            return jsonify({'error': '両方のファイルをアップロードしてください'}), 400
        
        video_file = request.files['video_file']
        live_file = request.files['live_file']
        
        if video_file.filename == '' or live_file.filename == '':
            logger.warning("ファイル名が空です")
            return jsonify({'error': 'ファイルが選択されていません'}), 400
        
        if not (allowed_file(video_file.filename) and allowed_file(live_file.filename)):
            logger.warning(f"不正なファイル形式: {video_file.filename}, {live_file.filename}")
            return jsonify({'error': 'Excelファイル (.xlsx, .xls) のみアップロード可能です'}), 400
        
        # パラメータの取得
        case_type = request.form.get('case_type', 'short_video')
        industry = request.form.get('industry', 'none')
        country = request.form.get('country', 'none')
        
        logger.info(f"検索条件: 事例タイプ={case_type}, 業界={industry}, 国={country}")
        
        # ファイルを一時保存
        video_filename = secure_filename(video_file.filename)
        live_filename = secure_filename(live_file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        live_path = os.path.join(app.config['UPLOAD_FOLDER'], live_filename)
        
        video_file.save(video_path)
        live_file.save(live_path)
        logger.info(f"ファイル保存完了: {video_filename}, {live_filename}")
        
        # データの読み込み
        logger.info("[STEP 0] Excelファイル読み込み中...")
        video_df = pd.read_excel(video_path)
        logger.info(f"ショート動画データ: {len(video_df)}行, カラム: {video_df.columns.tolist()}")
        
        live_df = pd.read_excel(live_path)
        logger.info(f"ライブ配信データ: {len(live_df)}行, カラム: {live_df.columns.tolist()}")
        
        sheet_df = get_google_sheet_data()
        
        if sheet_df is None:
            logger.error("Google Sheetデータの取得に失敗")
            return jsonify({'error': 'Google Sheetからデータを取得できませんでした'}), 500
        
        # データのマージとフィルタリング
        result_df = merge_data(video_df, live_df, sheet_df, case_type, industry, country)
        
        if result_df is None:
            logger.error("データマージ処理に失敗")
            return jsonify({'error': 'データの処理中にエラーが発生しました。詳細はサーバーログを確認してください。'}), 500
        
        # 要件4: <fw-タグを含むURLのみをフィルタリング
        logger.info("[STEP 6] <fw-タグフィルタリング開始...")
        original_count = len(result_df)
        
        # URLごとに<fw-タグの存在をチェック
        fw_tag_flags = []
        for idx, row in result_df.iterrows():
            url = row['URL']
            has_fw_tag, _ = check_fw_tag_in_url(url)
            fw_tag_flags.append(has_fw_tag)
        
        result_df['has_fw_tag'] = fw_tag_flags
        result_df = result_df[result_df['has_fw_tag'] == True].copy()
        result_df = result_df.drop('has_fw_tag', axis=1)
        
        logger.info(f"[STEP 6 完了] <fw-タグフィルター: {original_count}行 → {len(result_df)}行")
        
        # 一時ファイルを削除
        os.remove(video_path)
        os.remove(live_path)
        logger.info("一時ファイル削除完了")
        
        # 結果をJSON形式で返す
        result = {
            'columns': result_df.columns.tolist(),
            'data': result_df.to_dict(orient='records'),
            'total_count': len(result_df)
        }
        
        logger.info("="*60)
        logger.info(f"検索成功: {len(result_df)}件の結果を返却")
        logger.info("="*60)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error("="*60)
        logger.error(f"予期しないエラーが発生: {e}")
        logger.error(traceback.format_exc())
        logger.error("="*60)
        return jsonify({'error': f'エラーが発生しました: {str(e)}'}), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
