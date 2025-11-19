#!/usr/bin/env python3
"""API設定のテストスクリプト"""
import os
import requests

def test_openai_api():
    """OpenAI APIのテスト"""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    
    if not api_key:
        print("❌ OPENAI_API_KEY が設定されていません")
        return False
    
    print(f"🔑 OpenAI API Key: {api_key[:20]}...")
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [{'role': 'user', 'content': 'Test'}],
                'max_tokens': 5
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ OpenAI API: 正常に動作しています")
            return True
        else:
            print(f"❌ OpenAI API エラー: {response.status_code}")
            print(f"   レスポンス: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ OpenAI API 接続エラー: {e}")
        return False

def test_screenshot_api():
    """ScreenshotAPI.netのテスト"""
    token = os.environ.get('SCREENSHOT_API_TOKEN', '')
    
    if not token:
        print("⚠️  SCREENSHOT_API_TOKEN が設定されていません（オプション）")
        return None
    
    print(f"🔑 Screenshot API Token: {token[:20]}...")
    
    try:
        test_url = "https://example.com"
        screenshot_url = f"https://shot.screenshotapi.net/screenshot?token={token}&url={test_url}&width=800&height=600&output=image&file_type=png"
        
        response = requests.get(screenshot_url, timeout=15)
        
        if response.status_code == 200:
            print("✅ ScreenshotAPI.net: 正常に動作しています")
            return True
        else:
            print(f"❌ ScreenshotAPI.net エラー: {response.status_code}")
            print(f"   レスポンス: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ ScreenshotAPI.net 接続エラー: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("API設定のテスト")
    print("=" * 60)
    
    openai_ok = test_openai_api()
    print()
    screenshot_ok = test_screenshot_api()
    
    print()
    print("=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"OpenAI API: {'✅ OK' if openai_ok else '❌ エラー'}")
    print(f"ScreenshotAPI.net: {'✅ OK' if screenshot_ok else ('⚠️  未設定' if screenshot_ok is None else '❌ エラー')}")
    print()
    
    if openai_ok:
        print("✨ すべての必須APIが正常に動作しています！")
    else:
        print("⚠️  OpenAI APIキーを正しく設定してください")
