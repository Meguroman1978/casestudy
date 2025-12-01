#!/usr/bin/env python3
"""
デプロイ診断スクリプト
環境変数や外部サービスへの接続をテストします
"""
import os
import sys
import requests

# python-dotenvが利用可能な場合のみ使用
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ .envファイルから環境変数を読み込みました")
except ImportError:
    print("⚠️  python-dotenvがインストールされていません（環境変数は直接読み込みます）")

print("="*60)
print("デプロイ診断スクリプト / Deployment Diagnostics")
print("="*60)
print()

# 1. 環境変数チェック
print("【1. 環境変数チェック】")
print("-"*60)

openai_key = os.getenv('OPENAI_API_KEY')
sheet_id = os.getenv('GOOGLE_SHEET_ID')
slides_id = os.getenv('GOOGLE_SLIDES_ID')

if openai_key:
    print(f"✅ OPENAI_API_KEY: 設定済み ({openai_key[:15]}...{openai_key[-10:]})")
else:
    print("❌ OPENAI_API_KEY: 未設定")
    
if sheet_id:
    print(f"✅ GOOGLE_SHEET_ID: {sheet_id}")
else:
    print("❌ GOOGLE_SHEET_ID: 未設定")
    
if slides_id:
    print(f"✅ GOOGLE_SLIDES_ID: {slides_id}")
else:
    print("❌ GOOGLE_SLIDES_ID: 未設定")

print()

# 2. Google Sheets接続テスト
print("【2. Google Sheets接続テスト】")
print("-"*60)

if sheet_id:
    csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0'
    try:
        print(f"アクセス中: {csv_url}")
        response = requests.get(csv_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Google Sheets接続成功")
            print(f"   データサイズ: {len(response.content)} bytes")
            # 最初の100文字を表示
            content = response.text[:100]
            print(f"   内容プレビュー: {content}...")
        else:
            print(f"❌ Google Sheets接続失敗")
            print(f"   HTTPステータス: {response.status_code}")
            print(f"   エラー内容: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Google Sheets接続エラー: {e}")
else:
    print("⚠️  GOOGLE_SHEET_IDが設定されていないためスキップ")

print()

# 3. Google Slides接続テスト
print("【3. Google Slides接続テスト】")
print("-"*60)

if slides_id:
    pptx_url = f'https://docs.google.com/presentation/d/{slides_id}/export/pptx'
    try:
        print(f"アクセス中: {pptx_url}")
        response = requests.get(pptx_url, timeout=30)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            file_size = len(response.content)
            print(f"✅ Google Slides接続成功")
            print(f"   Content-Type: {content_type}")
            print(f"   ファイルサイズ: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            
            if file_size < 1_000_000:
                print(f"   ⚠️  ファイルサイズが小さすぎます（期待: 1MB以上）")
                print(f"   → Google Slidesが公開設定になっているか確認してください")
        else:
            print(f"❌ Google Slides接続失敗")
            print(f"   HTTPステータス: {response.status_code}")
            print(f"   → Google Slidesを「リンクを知っている全員」に公開してください")
    except Exception as e:
        print(f"❌ Google Slides接続エラー: {e}")
else:
    print("⚠️  GOOGLE_SLIDES_IDが設定されていないためスキップ")

print()

# 4. OpenAI API接続テスト
print("【4. OpenAI API接続テスト】")
print("-"*60)

if openai_key:
    try:
        print("OpenAI APIにアクセス中...")
        response = requests.get(
            'https://api.openai.com/v1/models',
            headers={'Authorization': f'Bearer {openai_key}'},
            timeout=10
        )
        if response.status_code == 200:
            print("✅ OpenAI API接続成功")
            models = response.json()
            print(f"   利用可能なモデル数: {len(models.get('data', []))}")
        elif response.status_code == 401:
            print("❌ OpenAI API認証失敗")
            print("   → APIキーが無効です。新しいキーを生成してください")
        elif response.status_code == 429:
            print("⚠️  OpenAI APIレート制限")
            print("   → 使用制限に達しています。しばらく待ってから再試行してください")
        else:
            print(f"❌ OpenAI API接続失敗")
            print(f"   HTTPステータス: {response.status_code}")
    except Exception as e:
        print(f"❌ OpenAI API接続エラー: {e}")
else:
    print("⚠️  OPENAI_API_KEYが設定されていないためスキップ")

print()

# 5. 診断結果サマリー
print("【5. 診断結果サマリー】")
print("="*60)

issues = []

if not openai_key:
    issues.append("OPENAI_API_KEYが未設定")
if not sheet_id:
    issues.append("GOOGLE_SHEET_IDが未設定")
if not slides_id:
    issues.append("GOOGLE_SLIDES_IDが未設定")

if issues:
    print("❌ 問題が見つかりました:")
    for issue in issues:
        print(f"   - {issue}")
    print()
    print("📝 解決方法:")
    print("   1. .envファイルを作成または編集")
    print("   2. 必要な環境変数を設定")
    print("   3. このスクリプトを再実行")
    print()
    print("   または、Render.comの場合:")
    print("   1. Environment タブを開く")
    print("   2. 不足している環境変数を追加")
    print("   3. Save Changes をクリック")
else:
    print("✅ 主要な環境変数は設定されています")
    print()
    print("📝 次のステップ:")
    print("   1. Google Sheets/Slidesの公開設定を確認")
    print("   2. アプリケーションを起動してテスト")
    print("   3. エラーが発生する場合はログを確認")

print()
print("="*60)
print("診断完了")
print("="*60)
