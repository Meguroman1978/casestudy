#!/usr/bin/env python3
"""
国名マッピング機能のテストスクリプト
"""
from app import get_country_codes, COUNTRY_CODE_MAPPING

def test_country_mapping():
    """国名マッピングのテスト"""
    
    print("=" * 80)
    print("国名マッピングテスト")
    print("=" * 80)
    
    # テスト対象の国
    test_countries = [
        'Japan',
        'United States',
        'United Kingdom',
        'China',
        'Germany',
        'Australia',
        'Unknown Country'  # マッピングにない国
    ]
    
    for country in test_countries:
        codes = get_country_codes(country)
        print(f"\n【国名】: {country}")
        print(f"【対応コード】: {codes}")
    
    print("\n" + "=" * 80)
    print(f"登録済み国数: {len(COUNTRY_CODE_MAPPING)}カ国")
    print("=" * 80)
    
    # 全マッピングを表示
    print("\n【全国名マッピング】")
    print("-" * 80)
    for country, codes in sorted(COUNTRY_CODE_MAPPING.items()):
        print(f"{country:30s} → {codes}")
    
    print("\n" + "=" * 80)
    print("テスト完了")
    print("=" * 80)

if __name__ == '__main__':
    test_country_mapping()
