#!/usr/bin/env python3
"""
Why Firework生成機能のテストスクリプト
"""
import os
import sys

# 環境変数を設定（テスト用）
if not os.environ.get('OPENAI_API_KEY'):
    print("警告: OPENAI_API_KEYが設定されていません。fallbackメッセージが使用されます。")

# app.pyをインポート
from app import generate_why_firework, check_fw_tag_in_url

def test_why_firework_generation():
    """Why Firework生成のテスト"""
    
    # テストURL（例：既知のECサイト）
    test_urls = [
        "https://www.uniqlo.com/jp/ja/",
        "https://www.apple.com/jp/",
    ]
    
    print("=" * 80)
    print("Why Firework生成テスト")
    print("=" * 80)
    
    for url in test_urls:
        print(f"\n【テストURL】: {url}")
        print("-" * 80)
        
        try:
            # URLからfwタグとHTMLコンテンツを取得
            has_fw, html_content = check_fw_tag_in_url(url)
            print(f"fwタグ検出: {has_fw}")
            print(f"HTMLコンテンツ取得: {'成功' if html_content else '失敗'}")
            
            if html_content:
                # Website descriptionをシミュレート
                website_description = "アパレルブランドのECサイト。商品カタログと着回し提案を提供。"
                
                # Why Firework生成
                print("\nWhy Firework生成中...")
                why_firework_text = generate_why_firework(
                    url=url,
                    html_content=html_content,
                    website_description=website_description,
                    language='ja'
                )
                
                print(f"\n【生成結果】:")
                print(f"{why_firework_text}")
                print(f"\n文字数: {len(why_firework_text)}文字")
            else:
                print("HTMLコンテンツが取得できなかったため、スキップします。")
                
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 80)
    
    print("\n" + "=" * 80)
    print("テスト完了")
    print("=" * 80)

if __name__ == '__main__':
    test_why_firework_generation()
