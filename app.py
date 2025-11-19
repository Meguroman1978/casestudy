import os
from flask import Flask, render_template, request, jsonify
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from werkzeug.utils import secure_filename

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
        # 公開されているシートの場合、認証なしで読み取り可能
        # CSVエクスポートURLを使用
        sheet_id = '1EsNylv4Leg73lb_AXJLMBnQKkozvHhLzfVGlz4HN2Tk'
        gid = '0'
        csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'
        
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        print(f"Error reading Google Sheet: {e}")
        return None

def merge_data(video_df, live_df, sheet_df, case_type, industry, country):
    """データをマージしてフィルタリングする"""
    try:
        # 事例タイプに応じて使用するデータフレームを選択
        if case_type == 'short_video':
            main_df = video_df.copy()
        else:  # live_stream
            main_df = live_df.copy()
        
        # Business Idをキーとしてマージ
        # Google Sheetのカラム名を確認して適切にマージ
        merged_df = main_df.merge(
            sheet_df[['Business Id', 'Account: Account Name', 'Account: Industry', 'Account: Owner Territory']],
            on='Business Id',
            how='left'
        )
        
        # フィルタリング
        if industry != 'none':
            merged_df = merged_df[merged_df['Account: Industry'] == industry]
        
        if country != 'none':
            merged_df = merged_df[merged_df['Account: Owner Territory'] == country]
        
        # 必要な列だけを抽出
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
        
        return result_df
    except Exception as e:
        print(f"Error merging data: {e}")
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

@app.route('/api/process', methods=['POST'])
def process_data():
    """アップロードされたファイルを処理"""
    try:
        # ファイルのチェック
        if 'video_file' not in request.files or 'live_file' not in request.files:
            return jsonify({'error': '両方のファイルをアップロードしてください'}), 400
        
        video_file = request.files['video_file']
        live_file = request.files['live_file']
        
        if video_file.filename == '' or live_file.filename == '':
            return jsonify({'error': 'ファイルが選択されていません'}), 400
        
        if not (allowed_file(video_file.filename) and allowed_file(live_file.filename)):
            return jsonify({'error': 'Excelファイル (.xlsx, .xls) のみアップロード可能です'}), 400
        
        # パラメータの取得
        case_type = request.form.get('case_type', 'short_video')
        industry = request.form.get('industry', 'none')
        country = request.form.get('country', 'none')
        
        # ファイルを一時保存
        video_filename = secure_filename(video_file.filename)
        live_filename = secure_filename(live_file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        live_path = os.path.join(app.config['UPLOAD_FOLDER'], live_filename)
        
        video_file.save(video_path)
        live_file.save(live_path)
        
        # データの読み込み
        video_df = pd.read_excel(video_path)
        live_df = pd.read_excel(live_path)
        sheet_df = get_google_sheet_data()
        
        if sheet_df is None:
            return jsonify({'error': 'Google Sheetからデータを取得できませんでした'}), 500
        
        # データのマージとフィルタリング
        result_df = merge_data(video_df, live_df, sheet_df, case_type, industry, country)
        
        if result_df is None:
            return jsonify({'error': 'データの処理中にエラーが発生しました'}), 500
        
        # 一時ファイルを削除
        os.remove(video_path)
        os.remove(live_path)
        
        # 結果をJSON形式で返す
        result = {
            'columns': result_df.columns.tolist(),
            'data': result_df.to_dict(orient='records'),
            'total_count': len(result_df)
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'エラーが発生しました: {str(e)}'}), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
