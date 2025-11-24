#!/usr/bin/env python3
"""
データセット内の実際の国名表記を確認するスクリプト
"""
import os
from app import get_google_sheet_data
import pandas as pd

def debug_country_values():
    """Google Sheetから国名の実際の値を確認"""
    
    print("=" * 80)
    print("データセット内の国名表記調査")
    print("=" * 80)
    
    # Google Sheetからデータを取得
    sheet_df = get_google_sheet_data()
    
    if sheet_df is None:
        print("エラー: Google Sheetからデータを取得できませんでした")
        return
    
    print(f"\n総行数: {len(sheet_df)}行")
    print(f"カラム: {sheet_df.columns.tolist()}")
    
    if 'Account: Owner Territory' not in sheet_df.columns:
        print("\nエラー: 'Account: Owner Territory' カラムが見つかりません")
        return
    
    # 国名のユニークな値を取得
    countries = sheet_df['Account: Owner Territory'].dropna().unique()
    countries_sorted = sorted(countries)
    
    print(f"\n\n【データセット内の国名表記】（全{len(countries_sorted)}種類）")
    print("-" * 80)
    
    for i, country in enumerate(countries_sorted, 1):
        # 各国名の出現回数をカウント
        count = (sheet_df['Account: Owner Territory'] == country).sum()
        print(f"{i:3d}. {country:40s} ({count:4d}件)")
    
    # United Statesに関連しそうな国名を探す
    print("\n\n【'US', 'United', 'States', 'America'を含む国名】")
    print("-" * 80)
    us_related = [c for c in countries_sorted if any(keyword in str(c).upper() for keyword in ['US', 'UNITED', 'STATES', 'AMERICA'])]
    
    if us_related:
        for country in us_related:
            count = (sheet_df['Account: Owner Territory'] == country).sum()
            print(f"  → {country:40s} ({count:4d}件)")
    else:
        print("  該当なし")
    
    # Japanに関連する国名を探す
    print("\n\n【'JP', 'Japan', 'JA'を含む国名】")
    print("-" * 80)
    jp_related = [c for c in countries_sorted if any(keyword in str(c).upper() for keyword in ['JP', 'JAPAN', 'JA'])]
    
    if jp_related:
        for country in jp_related:
            count = (sheet_df['Account: Owner Territory'] == country).sum()
            print(f"  → {country:40s} ({count:4d}件)")
    else:
        print("  該当なし")
    
    # サンプルデータを表示
    print("\n\n【サンプルデータ（最初の10行）】")
    print("-" * 80)
    sample_cols = ['Business Id', 'Account: Account Name', 'Account: Owner Territory', 'Account: Industry']
    available_cols = [col for col in sample_cols if col in sheet_df.columns]
    print(sheet_df[available_cols].head(10).to_string())
    
    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

if __name__ == '__main__':
    debug_country_values()
