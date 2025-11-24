#!/usr/bin/env python3
"""PPTX生成機能のテストスクリプト"""
import requests
import json

def test_pptx_generation():
    """PPTX生成APIをテスト"""
    
    url = "http://localhost:5000/api/create-pptx"
    
    # テストデータ
    test_data = {
        "channel_name": "Test Channel",
        "industry": "Technology",
        "country": "Japan",
        "url": "https://www.example.com",
        "language": "ja"
    }
    
    print("=" * 60)
    print("PPTX生成APIテスト")
    print("=" * 60)
    print(f"Endpoint: {url}")
    print(f"Test Data: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        response = requests.post(url, json=test_data, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print()
        
        if response.status_code == 200:
            print("✅ PPTX生成成功！")
            print(f"   ファイルサイズ: {len(response.content)} bytes")
            
            # PPTXファイルを保存
            with open('/tmp/test_output.pptx', 'wb') as f:
                f.write(response.content)
            print("   保存先: /tmp/test_output.pptx")
        else:
            print("❌ エラーが発生しました")
            try:
                error_data = response.json()
                print(f"   エラーメッセージ: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   レスポンス: {response.text[:500]}")
        
    except requests.exceptions.Timeout:
        print("⚠️  タイムアウト: リクエストがタイムアウトしました")
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー: サーバーに接続できませんでした")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")

if __name__ == '__main__':
    test_pptx_generation()
