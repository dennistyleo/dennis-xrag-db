"""
XR 系統與 XRAG 整合測試
測試 xr-series-architecture 與 xrag-axiom-engine 的通訊
"""

import requests
import json
import sys
import os
from datetime import datetime

# XRAG API 端點
XRAG_API = "http://localhost:5001/api"

# XR 主系統端點（根據 xrad_demo.py 實際設定）
XR_API = "http://localhost:5000/api"  # 可能需要調整

def print_header(title):
    print("\n" + "="*70)
    print(f"🔧 {title}")
    print("="*70)

def test_xrag_health():
    """測試 XRAG 健康狀態"""
    try:
        response = requests.get(f"{XRAG_API}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ XRAG: 正常 (公理數: {data.get('total', 'N/A')})")
            return True
        else:
            print(f"❌ XRAG: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ XRAG: 連接失敗 - {e}")
        return False

def test_xr_health():
    """測試 XR 主系統健康狀態"""
    try:
        response = requests.get(f"{XR_API}/health")
        if response.status_code == 200:
            print(f"✅ XR 主系統: 正常")
            return True
        else:
            print(f"❌ XR 主系統: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ XR 主系統: 連接失敗 - {e}")
        return False

def test_xrag_match():
    """測試 XRAG 匹配功能"""
    print_header("測試 XRAG 匹配功能")
    
    # 測試候選公理
    candidate = {
        "name": "Thermal Conduction Test",
        "domain": "thermal",
        "computational_core": {
            "type": "heat_conduction",
            "form": "Q = k·A·ΔT/d"
        },
        "input_signature": {
            "required_vars": ["k", "A", "ΔT", "d"]
        }
    }
    
    try:
        response = requests.post(
            f"{XRAG_API}/match",
            json={"candidate": candidate}
        )
        
        if response.status_code == 200:
            result = response.json()
            matches = result.get('matches', [])
            print(f"✅ 匹配成功，找到 {len(matches)} 個相似公理")
            
            for m in matches[:3]:
                print(f"   • {m.get('name')}: 相似度 {m.get('score', 0):.2f}")
            return True
        else:
            print(f"❌ 匹配失敗: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 匹配錯誤: {e}")
        return False

def test_xrag_axioms():
    """取得 XRAG 公理列表"""
    print_header("XRAG 公理列表")
    
    try:
        response = requests.get(f"{XRAG_API}/axioms")
        if response.status_code == 200:
            data = response.json()
            axioms = data.get('axioms', [])
            print(f"✅ 取得 {len(axioms)} 條公理")
            
            # 按領域統計
            domains = {}
            for a in axioms:
                domain = a.get('domain', 'unknown')
                domains[domain] = domains.get(domain, 0) + 1
            
            print("\n📊 領域分佈:")
            for domain, count in sorted(domains.items()):
                print(f"   • {domain}: {count} 條")
            
            return axioms
        else:
            print(f"❌ 取得失敗: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return []

def test_xr_to_xrag_flow():
    """測試 XR → XRAG 完整流程"""
    print_header("測試 XR → XRAG 完整流程")
    
    # 模擬 XR 系統產生的公理
    xr_axiom = {
        "name": "XR_Generated_Axiom",
        "domain": "mechanics",
        "computational_core": {
            "type": "hookes_law",
            "form": "σ = E·ε"
        },
        "input_signature": {
            "required_vars": ["E", "ε"]
        },
        "confidence": 0.92,
        "source": "xr_series"
    }
    
    # 1. XR 系統提交到 XRAG 匹配
    print("\n步驟 1: XR 系統提交公理到 XRAG 匹配")
    try:
        response = requests.post(
            f"{XRAG_API}/match",
            json={"candidate": xr_axiom}
        )
        
        if response.status_code == 200:
            result = response.json()
            matches = result.get('matches', [])
            print(f"✅ 匹配完成，找到 {len(matches)} 個相似公理")
            
            if matches:
                best = matches[0]
                print(f"\n🏆 最佳匹配:")
                print(f"   名稱: {best.get('name')}")
                print(f"   相似度: {best.get('score', 0):.2f}")
            else:
                print("\n⚠️ 沒有找到匹配的公理")
                
                # 2. 無匹配時存入未知通道
                print("\n步驟 2: 存入未知通道")
                unknown_resp = requests.post(
                    f"{XRAG_API}/unknown",
                    json={
                        "candidate": xr_axiom,
                        "reason": "no_match_from_xr"
                    }
                )
                
                if unknown_resp.status_code == 201:
                    unknown_id = unknown_resp.json().get('unknown_id')
                    print(f"✅ 已存入未知通道，ID: {unknown_id}")
                else:
                    print(f"❌ 存入失敗")
        else:
            print(f"❌ 匹配失敗: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 流程錯誤: {e}")

def test_xrag_to_xr_flow():
    """測試 XRAG → XR 完整流程"""
    print_header("測試 XRAG → XR 完整流程")
    
    # 從 XRAG 取得一條公理
    try:
        response = requests.get(f"{XRAG_API}/axioms")
        if response.status_code != 200:
            print("❌ 無法取得公理")
            return
        
        data = response.json()
        axioms = data.get('axioms', [])
        
        if not axioms:
            print("❌ 公理列表為空")
            return
        
        # 取第一條公理作為範例
        sample = axioms[0]
        print(f"\n📦 從 XRAG 取得的公理:")
        print(f"   名稱: {sample.get('name')}")
        print(f"   領域: {sample.get('domain')}")
        
        # 模擬發送到 XR 系統
        print(f"\n📤 發送到 XR 系統...")
        print(f"   (這裡需要根據 XR 系統的 API 實作)")
        
        # TODO: 根據 XR 系統的實際 API 加入發送程式碼
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")

def main():
    print("="*80)
    print("🚀 XR 系統與 XRAG 整合測試")
    print("="*80)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 檢查基本連線
    print_header("檢查基本連線")
    xrag_ok = test_xrag_health()
    xr_ok = test_xr_health()
    
    if not xrag_ok:
        print("\n❌ XRAG 未啟動，請先啟動: python src/api_server.py")
        return
    
    # 2. 取得 XRAG 公理列表
    axioms = test_xrag_axioms()
    
    # 3. 測試匹配功能
    test_xrag_match()
    
    # 4. 測試 XR → XRAG 流程
    test_xr_to_xrag_flow()
    
    # 5. 測試 XRAG → XR 流程
    test_xrag_to_xr_flow()
    
    print("\n" + "="*80)
    print("✅ 整合測試完成")
    print("="*80)

if __name__ == "__main__":
    main()
