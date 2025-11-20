#!/usr/bin/env python3
"""Template.pptxを外部URLからダウンロードするスクリプト"""
import os
import requests
from pathlib import Path

# Template.pptxのダウンロードURL（Google Drive、Dropbox等の公開リンク）
TEMPLATE_URL = os.environ.get('TEMPLATE_PPTX_URL', '')

def download_template():
    """Template.pptxをダウンロード"""
    template_path = Path(__file__).parent / 'Template.pptx'
    
    # 既にファイルが存在する場合はスキップ
    if template_path.exists():
        print(f"✅ Template.pptx already exists ({template_path.stat().st_size} bytes)")
        return True
    
    if not TEMPLATE_URL:
        print("⚠️  TEMPLATE_PPTX_URL not set. Skipping download.")
        return False
    
    print(f"📥 Downloading Template.pptx from {TEMPLATE_URL[:50]}...")
    
    try:
        response = requests.get(TEMPLATE_URL, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(template_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = template_path.stat().st_size
        print(f"✅ Download complete: {file_size} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

if __name__ == '__main__':
    download_template()
