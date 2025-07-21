#!/usr/bin/env python3
"""Final check for improvements in image classification and organization"""
import json
import os

def check_improvements():
    # Find the latest output
    latest_dir = "output/paper_20250721_012442"
    json_path = os.path.join(latest_dir, "extracted_data.json")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("🎯 BTMR Improvement Check Report")
    print("=" * 50)
    
    # 1. Check for duplicate images
    print("\n1️⃣ Checking for duplicate images between sections...")
    method_urls = set()
    result_urls = set()
    
    # Collect method figure URLs
    for subsection in data.get("method", {}).get("subsections", []):
        for fig in subsection.get("figures", []):
            method_urls.add(fig.get("url"))
    
    # Collect result figure URLs  
    for subsection in data.get("results", {}).get("subsections", []):
        for fig in subsection.get("figures", []):
            result_urls.add(fig.get("url"))
    
    # Add table URLs to results
    for table in data.get("results", {}).get("tables", []):
        if table.get("url"):
            result_urls.add(table.get("url"))
    
    duplicates = method_urls & result_urls
    if duplicates:
        print(f"   ❌ Found {len(duplicates)} duplicate images!")
        for dup in duplicates:
            print(f"      - {dup}")
    else:
        print("   ✅ No duplicate images found!")
    
    # 2. Check image classification
    print("\n2️⃣ Checking image classification...")
    print("\n   Method Section:")
    for subsection in data.get("method", {}).get("subsections", []):
        if subsection.get("figures"):
            print(f"   📂 {subsection['title']}:")
            for fig in subsection["figures"]:
                caption = fig.get("caption", "")
                print(f"      - {caption}")
                # Check if this should be in results
                if any(word in caption.lower() for word in ["vs", "comparison", "performance", "speedup", "analysis"]):
                    print(f"        ⚠️  May be better in results section")
    
    print("\n   Results Section:")
    for subsection in data.get("results", {}).get("subsections", []):
        if subsection.get("figures"):
            print(f"   📂 {subsection['title']}:")
            for fig in subsection["figures"]:
                caption = fig.get("caption", "")
                print(f"      - {caption}")
                # Check if properly classified
                if not any(word in caption.lower() for word in ["vs", "comparison", "performance", "speedup", "analysis", "evaluation"]):
                    print(f"        ⚠️  May need review")
    
    # 3. Check organization improvements
    print("\n3️⃣ Checking content organization...")
    
    method_subsections = data.get("method", {}).get("subsections", [])
    results_subsections = data.get("results", {}).get("subsections", [])
    
    print(f"   Method has {len(method_subsections)} subsections")
    print(f"   Results has {len(results_subsections)} subsections")
    
    if method_subsections and results_subsections:
        print("   ✅ Both sections use improved subsection structure!")
    else:
        print("   ⚠️  Missing subsection structure")
    
    # 4. Summary
    print("\n📊 Summary:")
    total_method_figures = sum(len(s.get("figures", [])) for s in method_subsections)
    total_result_figures = sum(len(s.get("figures", [])) for s in results_subsections)
    total_tables = len(data.get("results", {}).get("tables", []))
    
    print(f"   - Method figures: {total_method_figures}")
    print(f"   - Result figures: {total_result_figures}")
    print(f"   - Tables: {total_tables}")
    print(f"   - Total visual elements: {total_method_figures + total_result_figures + total_tables}")

if __name__ == "__main__":
    check_improvements()