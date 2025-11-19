import os
import traceback
import logging
import requests
import re
import json
import io
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from werkzeug.utils import secure_filename
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv()

# ロギング設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

# Google Sheets設定
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
if not GOOGLE_SHEET_ID:
    logger.warning("⚠️ GOOGLE_SHEET_ID not set in environment variables")
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_google_sheet_data():
    """Google Sheetからデータを取得する"""
    try:
        logger.info("[STEP 1] Google Sheetからデータを取得中...")
        # 公開されているシートの場合、認証なしで読み取り可能
        # CSVエクスポートURLを使用
        sheet_id = GOOGLE_SHEET_ID
        if not sheet_id:
            raise ValueError("Google Sheet ID is not configured. Please set GOOGLE_SHEET_ID environment variable.")
        gid = '0'
        csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'
        
        df = pd.read_csv(csv_url)
        logger.info(f"[STEP 1 完了] Google Sheet取得成功: {len(df)}行")
        logger.debug(f"Google Sheet カラム: {df.columns.tolist()}")
        
        # カラム名の正規化（'Business ID' -> 'Business Id'）
        if 'Business ID' in df.columns:
            df = df.rename(columns={'Business ID': 'Business Id'})
            logger.info("カラム名を正規化: 'Business ID' -> 'Business Id'")
        
        logger.debug(f"Business Id データ型: {df['Business Id'].dtype}")
        logger.debug(f"Business Id サンプル: {df['Business Id'].head(3).tolist()}")
        
        # Business Idを数値型に変換
        df['Business Id'] = pd.to_numeric(df['Business Id'], errors='coerce')
        logger.info(f"Business Idを数値型に変換: {df['Business Id'].dtype}")
        
        # Account: Industryが空欄（NaN）の場合は「不明 / Unknown」として扱う
        if 'Account: Industry' in df.columns:
            df['Account: Industry'] = df['Account: Industry'].fillna('不明 / Unknown')
            logger.info(f"空欄のAccount: Industryを「不明 / Unknown」に変換")
        
        return df
    except Exception as e:
        logger.error(f"[エラー] Google Sheet取得失敗: {e}")
        logger.error(traceback.format_exc())
        return None

def merge_data(video_df, live_df, sheet_df, case_type, industry_filter, country):
    """データをマージしてフィルタリングする"""
    try:
        logger.info("[STEP 2] データマージ処理開始")
        logger.info(f"選択された事例タイプ: {case_type}, 業界フィルター: {industry_filter}, 国: {country}")
        
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
        
        # Business Idをキーとしてマージ（Channel Name, Business Nameも含める）
        logger.info("[STEP 3] データマージ実行中...")
        
        # Google Sheetに必要な列があるか確認
        available_cols = ['Business Id', 'Account: Account Name', 'Account: Industry', 'Account: Owner Territory']
        if 'Channel Name' in sheet_df.columns:
            available_cols.append('Channel Name')
        if 'Business Name' in sheet_df.columns:
            available_cols.append('Business Name')
        
        merged_df = main_df.merge(
            sheet_df[available_cols],
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
        
        # 業界フィルター（複数の業界名を受け取る場合に対応）
        if industry_filter and industry_filter != 'none':
            # カンマ区切りで複数の業界名が来る場合に対応
            if isinstance(industry_filter, str):
                industries = [i.strip() for i in industry_filter.split(',') if i.strip()]
            elif isinstance(industry_filter, list):
                industries = industry_filter
            else:
                industries = [industry_filter]
            
            if industries:
                merged_df = merged_df[merged_df['Account: Industry'].isin(industries)]
                logger.info(f"業界フィルター適用 ({', '.join(industries)}): {before_filter}行 → {len(merged_df)}行")
                before_filter = len(merged_df)
        
        if country != 'none':
            merged_df = merged_df[merged_df['Account: Owner Territory'] == country]
            logger.info(f"国フィルター適用 ({country}): {before_filter}行 → {len(merged_df)}行")
        
        logger.info(f"[STEP 4 完了] フィルタリング完了: {len(merged_df)}行")
        
        # 必要な列だけを抽出
        logger.info("[STEP 5] 結果データ整形中...")
        
        # 必要な列を構築（会社名とビジネス名は削除）
        columns_to_extract = [
            'Account: Industry',
            'Account: Owner Territory',
            'Page Url',
            'Video Views'
        ]
        
        # Channel Nameがある場合は追加（最初に配置）
        if 'Channel Name' in merged_df.columns:
            columns_to_extract.insert(0, 'Channel Name')
        
        result_df = merged_df[columns_to_extract].copy()
        
        # 列名を日本語に変更（会社名とビジネス名は含めない）
        new_column_names = []
        if 'Channel Name' in merged_df.columns:
            new_column_names.append('チャンネル名')
        new_column_names.extend(['業種', '国', 'URL', '_views'])
        
        result_df.columns = new_column_names
        
        # NaNを空文字列に変換
        result_df = result_df.fillna('')
        
        # URLからドメインを抽出
        result_df['ドメイン'] = result_df['URL'].apply(lambda x: urlparse(x).hostname if x else '')
        
        logger.info(f"[STEP 5 完了] 最終結果: {len(result_df)}行")
        logger.debug(f"結果のサンプル:\n{result_df.head(3)}")
        
        return result_df
    except Exception as e:
        logger.error(f"[エラー] データマージ失敗: {e}")
        logger.error(traceback.format_exc())
        return None

def group_by_domain_and_paginate(result_df, page=1, page_size=5):
    """Channel Name単位でグループ化してページング (デフォルト5件/ページ、各チャンネル最大3 URL)"""
    try:
        logger.info(f"[STEP 6] Channel Name単位でグループ化中... (ページ: {page}, サイズ: {page_size})")
        
        # Channel Name列が存在するか確認
        if 'チャンネル名' not in result_df.columns:
            logger.warning("チャンネル名列が存在しません。ドメインでグループ化します。")
            group_column = 'ドメイン'
        else:
            group_column = 'チャンネル名'
        
        # グループ化の列を決定（会社名とビジネス名は削除）
        agg_dict = {
            '業種': 'first',
            '国': 'first',
            '_views': 'sum',
            'URL': 'count'
        }
        
        # チャンネル名がある場合（グループ化対象でない場合のみ）
        if 'チャンネル名' in result_df.columns and group_column != 'チャンネル名':
            agg_dict['チャンネル名'] = 'first'
        
        # グループ化して集計
        channel_summary = result_df.groupby(group_column).agg(agg_dict).reset_index()
        
        # 合計視聴回数で降順ソート (ページングで制限するのでhead(20)は削除)
        channel_summary = channel_summary.sort_values('_views', ascending=False)
        
        logger.info(f"グループ化完了: Top {len(channel_summary)}件")
        
        # ページネーション適用
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_channels = channel_summary.iloc[start_idx:end_idx]
        
        logger.info(f"ページ {page}: {len(paginated_channels)}件を返却")
        
        # ページネーション対象のチャンネルの詳細データを取得
        channel_list = paginated_channels[group_column].tolist()
        detailed_data = result_df[result_df[group_column].isin(channel_list)].copy()
        
        # 視聴回数で降順ソート（チャンネル内）
        detailed_data = detailed_data.sort_values([group_column, '_views'], ascending=[True, False])
        
        # 各チャンネルのURL数を最大3に制限
        detailed_data = detailed_data.groupby(group_column).head(3).reset_index(drop=True)
        
        return {
            'channel_summary': channel_summary,
            'paginated_channels': paginated_channels,
            'detailed_data': detailed_data,
            'total_domains': len(channel_summary),  # Changed from total_channels to total_domains
            'current_page': page,
            'page_size': page_size,
            'has_next': end_idx < len(channel_summary)
        }
    except Exception as e:
        logger.error(f"[エラー] ドメイングループ化失敗: {e}")
        logger.error(traceback.format_exc())
        return None

@app.route('/')
def index():
    """トップページ"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Favicon"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/api/get-options', methods=['GET'])
def get_options():
    """業界名と国のオプションを取得"""
    try:
        sheet_df = get_google_sheet_data()
        
        # Google Sheetからデータを取得できない場合は、デフォルトの国リストを使用
        if sheet_df is None:
            default_countries = ['Japan', 'United States', 'United Kingdom', 'Germany', 'France', 'System']
            return jsonify({
                'industries': [],
                'countries': default_countries
            })
        
        # ユニークな業界名と国を取得（空でないもの）
        industries = sorted(sheet_df['Account: Industry'].dropna().unique().tolist())
        countries = sorted(sheet_df['Account: Owner Territory'].dropna().unique().tolist())
        
        return jsonify({
            'industries': industries,
            'countries': countries
        })
    except Exception as e:
        # エラーが発生した場合もデフォルトの国リストを返す
        default_countries = ['Japan', 'United States', 'United Kingdom', 'Germany', 'France', 'System']
        return jsonify({
            'industries': [],
            'countries': default_countries
        })

@app.route('/api/get-category-hierarchy', methods=['GET'])
def get_category_hierarchy():
    """カテゴリー階層を取得"""
    try:
        hierarchy_path = os.path.join(os.path.dirname(__file__), 'category_hierarchy.json')
        with open(hierarchy_path, 'r', encoding='utf-8') as f:
            hierarchy = json.load(f)
        return jsonify(hierarchy)
    except Exception as e:
        logger.error(f"Category hierarchy load error: {e}")
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
        # 複数のスクリーンショットサービスを試行
        screenshot_url = None
        if has_fw_tag:
            # URLエンコード
            from urllib.parse import quote
            encoded_url = quote(url, safe='')
            
            # Option 1: screenshotapi.net (無料、登録不要)
            screenshot_url = f"https://shot.screenshotapi.net/screenshot?url={encoded_url}&width=400&height=300&output=image&file_type=png&wait_for_event=load"
            
            # Option 2 (fallback): Google's Page Speed Insights screenshot
            # screenshot_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={encoded_url}&screenshot=true"
            
            # Option 3 (fallback): screenshot.guru
            # screenshot_url = f"https://api.screenshot.guru/screenshot?url={encoded_url}&width=400&height=300"
        
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
        industry_filter = request.form.get('industry_filter', 'none')
        country = request.form.get('country', 'none')
        page = int(request.form.get('page', 1))
        page_size = int(request.form.get('page_size', 5))  # デフォルトを5に変更（最大5チャンネル表示）
        
        logger.info(f"検索条件: 事例タイプ={case_type}, 業界フィルター={industry_filter}, 国={country}, ページ={page}")
        
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
        result_df = merge_data(video_df, live_df, sheet_df, case_type, industry_filter, country)
        
        if result_df is None:
            logger.error("データマージ処理に失敗")
            return jsonify({'error': 'データの処理中にエラーが発生しました。詳細はサーバーログを確認してください。'}), 500
        
        # ドメインごとにグループ化してページネーション
        pagination_result = group_by_domain_and_paginate(result_df, page=page, page_size=page_size)
        
        if pagination_result is None:
            logger.error("ドメインのグループ化に失敗")
            return jsonify({'error': 'ドメインのグループ化中にエラーが発生しました。'}), 500
        
        # 要件4: 表示対象のURLのみ<fw-タグをチェック（パフォーマンス改善）
        logger.info("[STEP 7] 表示対象URLの<fw-タグチェック開始...")
        detailed_data = pagination_result['detailed_data']
        original_count = len(detailed_data)
        
        # 並列処理でURLチェックを高速化 (最大10スレッド並列)
        logger.info(f"並列URLチェック開始: {original_count}件のURL")
        
        def check_url_wrapper(url):
            """URLチェックのラッパー関数"""
            try:
                has_fw_tag, _ = check_fw_tag_in_url(url)
                return (url, has_fw_tag)
            except Exception as e:
                logger.error(f"URLチェック失敗 ({url}): {e}")
                return (url, False)
        
        # 並列実行
        url_to_flag = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            # すべてのURLに対してチェックを送信
            future_to_url = {executor.submit(check_url_wrapper, row['URL']): row['URL'] 
                           for idx, row in detailed_data.iterrows()}
            
            # 完了したものから結果を取得
            completed = 0
            for future in as_completed(future_to_url):
                url, has_fw_tag = future.result()
                url_to_flag[url] = has_fw_tag
                completed += 1
                if completed % 10 == 0:
                    logger.info(f"進行状況: {completed}/{original_count} URLチェック完了")
        
        # 結果をDataFrameに反映
        detailed_data['has_fw_tag'] = detailed_data['URL'].map(url_to_flag)
        filtered_data = detailed_data[detailed_data['has_fw_tag'] == True].copy()
        
        # 内部使用列を削除（フロントエンドで使用しないため）
        if 'ドメイン' in filtered_data.columns:
            filtered_data = filtered_data.drop('ドメイン', axis=1)
        if 'has_fw_tag' in filtered_data.columns:
            filtered_data = filtered_data.drop('has_fw_tag', axis=1)
        if '_views' in filtered_data.columns:
            filtered_data = filtered_data.drop('_views', axis=1)
        
        logger.info(f"[STEP 7 完了] <fw-タグフィルター: {original_count}行 → {len(filtered_data)}行")
        
        # 一時ファイルを削除
        os.remove(video_path)
        os.remove(live_path)
        logger.info("一時ファイル削除完了")
        
        # 結果をJSON形式で返す
        result = {
            'columns': filtered_data.columns.tolist(),
            'data': filtered_data.to_dict(orient='records'),
            'total_count': len(filtered_data),
            'total_domains': pagination_result['total_domains'],
            'current_page': pagination_result['current_page'],
            'page_size': pagination_result['page_size'],
            'has_next': pagination_result['has_next']
        }
        
        logger.info("="*60)
        logger.info(f"検索成功: {len(filtered_data)}件の結果を返却 (ページ {page}/{(pagination_result['total_domains'] + page_size - 1) // page_size})")
        logger.info("="*60)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error("="*60)
        logger.error(f"予期しないエラーが発生: {e}")
        logger.error(traceback.format_exc())
        logger.error("="*60)
        return jsonify({'error': f'エラーが発生しました: {str(e)}'}), 500

def extract_website_info(url):
    """ウェブサイトからメタ情報を抽出"""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        html_content = response.text
        
        # メタタグから情報を抽出
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 会社概要（descriptionメタタグから）
        description_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        description = description_tag.get('content', '') if description_tag else ''
        
        # タイトル
        title = soup.find('title').get_text() if soup.find('title') else ''
        
        # ロゴ画像URL
        logo_url = None
        logo_tag = soup.find('meta', attrs={'property': 'og:image'}) or soup.find('link', attrs={'rel': 'icon'}) or soup.find('link', attrs={'rel': 'apple-touch-icon'})
        if logo_tag:
            logo_url = logo_tag.get('content') or logo_tag.get('href')
            if logo_url and not logo_url.startswith('http'):
                from urllib.parse import urljoin
                logo_url = urljoin(url, logo_url)
        
        return {
            'title': title,
            'description': description,
            'logo_url': logo_url
        }
    except Exception as e:
        logger.error(f"ウェブサイト情報抽出エラー: {e}")
        return {'title': '', 'description': '', 'logo_url': None}

def translate_text(text, target_lang='en'):
    """テキストを翻訳（簡易版 - 実際にはGoogle Translate APIなどを使用）"""
    # ここでは簡易的に、日本語が含まれている場合のみ翻訳を試みる
    if not text or target_lang == 'ja':
        return text
    
    # 日本語が含まれているか確認
    import re
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text):
        # 実際の実装ではGoogle Translate APIを使用
        # ここでは元のテキストを返す（翻訳APIを実装する場合は置き換え）
        return text
    
    return text

def search_logo_images(channel_name, count=3):
    """Channel nameでロゴ画像を検索（OpenAI DALL-E検索機能を使用）"""
    try:
        from bs4 import BeautifulSoup
        import urllib.parse
        
        logger.info(f"Searching logos for: {channel_name}")
        
        # Google画像検索のURL（スクレイピング）
        search_query = f"{channel_name} logo"
        encoded_query = urllib.parse.quote(search_query)
        search_url = f"https://www.google.com/search?q={encoded_query}&tbm=isch"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 画像URLを抽出
        logo_urls = []
        img_tags = soup.find_all('img')
        
        for img in img_tags[:count + 5]:  # 余分に取得
            img_url = img.get('src') or img.get('data-src')
            if img_url and img_url.startswith('http') and len(logo_urls) < count:
                # base64やデータURLは除外
                if not img_url.startswith('data:'):
                    logo_urls.append(img_url)
        
        logger.info(f"Found {len(logo_urls)} logo URLs")
        return logo_urls[:count]
        
    except Exception as e:
        logger.error(f"Logo search error: {e}")
        logger.error(traceback.format_exc())
        return []

def crawl_and_analyze_website(url, language='ja'):
    """WebクローラーでWebサイト情報を取得し、OpenAI APIで分析"""
    try:
        from bs4 import BeautifulSoup
        
        fallback = '手動でサイト概要を入力してください' if language == 'ja' else 'Please manually enter website description here'
        
        # ウェブサイトをクロール
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # テキストコンテンツを抽出（スクリプトやスタイルを除外）
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_content = soup.get_text()
        # 空白を整理
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # テキストが長すぎる場合は切り詰め（OpenAI APIのトークン制限のため）
        if len(text) > 3000:
            text = text[:3000]
        
        # OpenAI APIで要約
        openai_api_key = os.environ.get('OPENAI_API_KEY', '')
        
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not set in environment variables")
            return "Website analysis unavailable (API key not configured)" if language == 'en' else "ウェブサイト分析が利用できません（APIキーが未設定）"
        
        prompt = f"""以下のウェブサイトの内容を分析し、以下の情報を含む簡潔な要約（150-200文字）を作成してください：
- 販売している商品・サービスの種類と特徴
- ビジネスのポジショニングや独自性
- 主な特徴や強み

ウェブサイトの内容:
{text}

要約は{'日本語' if language == 'ja' else '英語'}で作成してください。"""

        summary_response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 300,
                'temperature': 0.7
            },
            timeout=30
        )
        
        if summary_response.status_code == 200:
            result = summary_response.json()
            summary = result['choices'][0]['message']['content']
            logger.info(f"Website summary generated: {summary[:100]}...")
            return summary
        else:
            logger.error(f"OpenAI API error: {summary_response.status_code}")
            logger.error(f"Response body: {summary_response.text[:500]}")
            return fallback
            
    except Exception as e:
        logger.error(f"Website crawl and analysis error: {e}")
        logger.error(traceback.format_exc())
        fallback = '手動でサイト概要を入力してください' if language == 'ja' else 'Please manually enter website description here'
        return fallback

@app.route('/api/create-pptx', methods=['POST'])
def create_pptx():
    """PPTXスライドを生成"""
    try:
        data = request.json
        channel_name = data.get('channel_name', '')
        industry = data.get('industry', '')
        country = data.get('country', '')
        url = data.get('url', '')
        language = data.get('language', 'ja')
        
        logger.info(f"PPTX生成開始: Channel={channel_name}, 言語: {language}")
        
        # ウェブサイト情報を抽出
        website_info = extract_website_info(url)
        
        # 言語が英語の場合、日本語テキストを翻訳
        if language == 'en':
            channel_name = translate_text(channel_name, 'en')
            company_details = translate_text(website_info['description'], 'en')
        else:
            company_details = website_info['description']
        
        # テンプレートを読み込む
        template_path = os.path.join(os.path.dirname(__file__), 'Template.pptx')
        prs = Presentation(template_path)
        
        # 言語に応じてスライドを選択（0: 日本語, 1: 英語）
        slide_index = 0 if language == 'ja' else 1
        slide = prs.slides[slide_index]
        
        # フォールバックメッセージ
        fallback_screenshot = '手動で画面キャプチャを貼り付けてください' if language == 'ja' else 'Please manually paste a screenshot here'
        fallback_logo = '手動でロゴを貼り付けてください' if language == 'ja' else 'Please manually paste the logo here'
        fallback_website = '手動でサイト概要を入力してください' if language == 'ja' else 'Please manually enter website description here'
        
        # WebクローラーとOpenAI APIでWebsite descriptionを取得
        website_description_enhanced = crawl_and_analyze_website(url, language) if url else fallback_website
        
        # プレースホルダーのテキストを置換（Business NameとCompany detailsは削除）
        replacements = {
            '{Business Country}': country,
            '{Account: Industry}': industry,
            '{Channel Name}': channel_name,
            '{URL}': url,
            '{Website description}': website_description_enhanced
        }
        
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                original_text = shape.text
                new_text = original_text
                
                # すべてのプレースホルダーを置換
                for placeholder, value in replacements.items():
                    if placeholder in new_text:
                        new_text = new_text.replace(placeholder, value)
                
                # テキストが変更された場合のみ更新
                if new_text != original_text:
                    if hasattr(shape, "text_frame"):
                        shape.text_frame.text = new_text
                    else:
                        shape.text = new_text
        
        # スクリーンショットを取得して挿入
        screenshot_inserted = False
        screenshot_api_token = os.environ.get('SCREENSHOT_API_TOKEN', '')
        
        if not screenshot_api_token:
            logger.warning("SCREENSHOT_API_TOKEN not set - skipping screenshot generation")
        else:
            try:
                screenshot_url = f"https://shot.screenshotapi.net/screenshot?token={screenshot_api_token}&url={requests.utils.quote(url)}&width=1200&height=800&output=image&file_type=png&wait_for_event=load"
                screenshot_response = requests.get(screenshot_url, timeout=30)
                
                if screenshot_response.status_code == 200:
                img_data = io.BytesIO(screenshot_response.content)
                img = Image.open(img_data)
                
                # 画像を挿入する位置を探す
                for shape in slide.shapes:
                    if hasattr(shape, "text") and '{Insert Screenshot here}' in shape.text:
                        left = shape.left
                        top = shape.top
                        width = shape.width
                        height = shape.height
                        
                        # プレースホルダーを削除
                        sp = shape.element
                        sp.getparent().remove(sp)
                        
                        # 画像をリサイズして挿入
                        slide.shapes.add_picture(img_data, left, top, width=width, height=height)
                        screenshot_inserted = True
                        break
                else:
                    logger.warning(f"Screenshot API returned status code: {screenshot_response.status_code}")
            except Exception as e:
                logger.warning(f"スクリーンショット取得失敗: {e}")
        
        # スクリーンショットが挿入できなかった場合、フォールバックテキストを表示
        if not screenshot_inserted:
            for shape in slide.shapes:
                if hasattr(shape, "text") and '{Insert Screenshot here}' in shape.text:
                    if hasattr(shape, "text_frame"):
                        shape.text_frame.text = fallback_screenshot
                    else:
                        shape.text = fallback_screenshot
                    break
        
        # 3つのロゴを検索して挿入
        logo_urls = search_logo_images(channel_name, count=3)
        logger.info(f"Found {len(logo_urls)} logo URLs for {channel_name}")
        
        # 各ロゴプレースホルダーを探して挿入
        for logo_index in range(1, 4):  # 1, 2, 3
            placeholder = f'{{Channel logo {logo_index}}}'
            logo_inserted = False
            
            # 対応するロゴURLがある場合
            if logo_index <= len(logo_urls):
                logo_url = logo_urls[logo_index - 1]
                try:
                    logo_response = requests.get(logo_url, timeout=10)
                    if logo_response.status_code == 200:
                        logo_data = io.BytesIO(logo_response.content)
                        logo_img = Image.open(logo_data)
                        
                        # ロゴを挿入する位置を探す
                        for shape in slide.shapes:
                            if hasattr(shape, "text") and placeholder in shape.text:
                                left = shape.left
                                top = shape.top
                                max_width = shape.width
                                max_height = shape.height
                                
                                # プレースホルダーを削除
                                sp = shape.element
                                sp.getparent().remove(sp)
                                
                                # アスペクト比を保持してリサイズ
                                img_width, img_height = logo_img.size
                                aspect = img_width / img_height
                                
                                if max_width / max_height > aspect:
                                    new_height = max_height
                                    new_width = int(max_height * aspect)
                                else:
                                    new_width = max_width
                                    new_height = int(max_width / aspect)
                                
                                # 画像を挿入
                                slide.shapes.add_picture(logo_data, left, top, width=new_width, height=new_height)
                                logo_inserted = True
                                logger.info(f"Logo {logo_index} inserted successfully")
                                break
                except Exception as e:
                    logger.warning(f"ロゴ{logo_index}取得失敗: {e}")
            
            # ロゴが挿入できなかった場合、フォールバックテキストを表示
            if not logo_inserted:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and placeholder in shape.text:
                        if hasattr(shape, "text_frame"):
                            shape.text_frame.text = fallback_logo
                        else:
                            shape.text = fallback_logo
                        logger.info(f"Logo {logo_index} fallback text inserted")
                        break
        
        # 選択したスライド以外を削除
        slides_to_delete = []
        for i, s in enumerate(prs.slides):
            if i != slide_index:
                slides_to_delete.append(i)
        
        # 逆順で削除（インデックスの変更を避けるため）
        for idx in reversed(slides_to_delete):
            rId = prs.slides._sldIdLst[idx].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[idx]
        
        # メモリ上にPPTXを保存
        pptx_io = io.BytesIO()
        prs.save(pptx_io)
        pptx_io.seek(0)
        
        logger.info(f"PPTX生成完了: {channel_name}")
        
        return send_file(
            pptx_io,
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            as_attachment=True,
            download_name=f'{channel_name}_Casestudy.pptx'
        )
    
    except Exception as e:
        logger.error(f"PPTX生成エラー: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-excel', methods=['POST'])
def export_excel():
    """Excelファイルをエクスポート"""
    try:
        data = request.json
        rows = data.get('data', [])
        columns = data.get('columns', [])
        language = data.get('language', 'ja')
        
        logger.info(f"Excelエクスポート開始: {len(rows)}行, 言語: {language}")
        
        # 列名を言語に応じて変換（会社名とビジネス名は削除済み）
        if language == 'en':
            column_mapping = {
                'チャンネル名': 'Channel Name',
                '業種': 'Industry',
                '国': 'Country',
                'URL': 'URL'
            }
            translated_columns = [column_mapping.get(col, col) for col in columns]
        else:
            translated_columns = columns
        
        # DataFrameを作成
        df = pd.DataFrame(rows, columns=columns)
        df.columns = translated_columns
        
        # Excelファイルを作成
        excel_io = io.BytesIO()
        with pd.ExcelWriter(excel_io, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Results', index=False)
            
            # スタイルを適用
            workbook = writer.book
            worksheet = writer.sheets['Results']
            
            # ヘッダー行のスタイル
            header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            header_font = Font(bold=True, color='FFFFFF')
            
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 列幅を自動調整
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        excel_io.seek(0)
        
        logger.info(f"Excelエクスポート完了: {len(rows)}行")
        
        return send_file(
            excel_io,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='analysis_result.xlsx'
        )
    
    except Exception as e:
        logger.error(f"Excelエクスポートエラー: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
