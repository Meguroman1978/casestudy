#!/usr/bin/env python3
"""
地域マッピング機能のテストスクリプト
"""
from app import get_country_regions, COUNTRY_TO_REGION_MAPPING

def test_region_mapping():
    """地域マッピングのテスト"""
    
    print("=" * 80)
    print("地域マッピングテスト")
    print("=" * 80)
    
    # テスト対象の国
    test_countries = [
        'Japan',
        'United States',
        'United Kingdom',
        'China',
        'Germany',
        'Australia',
        'India',
        'Thailand',
        'Unknown Country'  # マッピングにない国
    ]
    
    for country in test_countries:
        regions = get_country_regions(country)
        print(f"\n【国名】: {country}")
        print(f"【対応地域】: {regions}")
    
    print("\n" + "=" * 80)
    print(f"登録済み国数: {len(COUNTRY_TO_REGION_MAPPING)}カ国")
    print("=" * 80)
    
    # 地域ごとに国をグループ化
    region_to_countries = {}
    for country, regions in COUNTRY_TO_REGION_MAPPING.items():
        region = regions[0]  # 各国は1つの地域にのみ属する
        if region not in region_to_countries:
            region_to_countries[region] = []
        region_to_countries[region].append(country)
    
    print("\n【地域ごとの国一覧】")
    print("-" * 80)
    for region in sorted(region_to_countries.keys()):
        countries = sorted(region_to_countries[region])
        print(f"\n■ {region} ({len(countries)}カ国)")
        for country in countries:
            print(f"  - {country}")
    
    print("\n" + "=" * 80)
    print("テスト完了")
    print("=" * 80)

if __name__ == '__main__':
    test_region_mapping()
