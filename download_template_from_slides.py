#!/usr/bin/env python3
"""
Google SlidesからTemplate.pptxをダウンロードするスクリプト
環境変数GOOGLE_SLIDES_IDを使用
"""
import os
import sys
import requests
from pathlib import Path

def download_template_from_google_slides():
    """Google SlidesからPPTXをダウンロード"""
    slides_id = os.environ.get('GOOGLE_SLIDES_ID')
    
    if not slides_id:
        print("❌ Error: GOOGLE_SLIDES_ID environment variable not set")
        sys.exit(1)
    
    # Google SlidesのエクスポートURL
    export_url = f"https://docs.google.com/presentation/d/{slides_id}/export/pptx"
    
    template_path = Path(__file__).parent / 'Template.pptx'
    
    # 既にファイルが存在する場合はスキップ
    if template_path.exists():
        print(f"✅ Template.pptx already exists ({template_path.stat().st_size} bytes)")
        return
    
    try:
        print(f"⬇️  Downloading Template.pptx from Google Slides...")
        print(f"   Slides ID: {slides_id}")
        
        response = requests.get(export_url, timeout=60)
        response.raise_for_status()
        
        # Content-Typeを確認
        content_type = response.headers.get('content-type', '')
        if 'presentation' not in content_type and 'octet-stream' not in content_type:
            print(f"⚠️  Warning: Unexpected content-type: {content_type}")
            print(f"⚠️  This might not be a PPTX file. Check if the Google Slides is publicly accessible.")
        
        # ファイルに保存
        with open(template_path, 'wb') as f:
            f.write(response.content)
        
        file_size = template_path.stat().st_size
        print(f"✅ Template.pptx downloaded successfully ({file_size:,} bytes)")
        
        # サイズチェック（少なくとも1MB以上あるはず）
        if file_size < 1_000_000:
            print(f"⚠️  Warning: File size is smaller than expected ({file_size:,} bytes)")
            print(f"⚠️  Please verify the Google Slides is publicly accessible:")
            print(f"   https://docs.google.com/presentation/d/{slides_id}/edit")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading Template.pptx: {e}")
        print(f"")
        print(f"🔧 Troubleshooting:")
        print(f"   1. Verify GOOGLE_SLIDES_ID is correct: {slides_id}")
        print(f"   2. Make sure the Google Slides is publicly accessible")
        print(f"   3. Try accessing this URL in browser:")
        print(f"      {export_url}")
        sys.exit(1)

if __name__ == '__main__':
    download_template_from_google_slides()
