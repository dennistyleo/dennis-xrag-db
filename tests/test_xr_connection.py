"""
XR-BUS 通訊確認測試
測試儀表板與 XR 主系統的連接
"""

import requests
import json
import sys
import os
from datetime import datetime

# XR 主系統 API 端點（根據實際配置修改）
XR_API_URL = "http://localhost:5001/api"  # 改為 API 伺服器的位址

# 儀表板 API
DASHBOARD_URL = "http://localhost:5002/api"

# XR-BUS 端點（如果有的話）
XRBUS_URL = "http://localhost:5006"  # XR-BUS 服務

def print_header(title):
    """列印標題"""
    print("\n" + "="*60)
    print(f"🔌 {title}")
    print("="*60)

def print_result(name, success, details=""):
    """列印結果"""
    icon = "✅" if success else "❌"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")

def test_xr_health():
    """測試 XR 主系統健康狀態"""
    print_header("測試 XR 主系統連接")
    
    try:
        response = requests.get(f"{XR_API_URL}/health", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print_result("XR 主系統", True, f"狀態: {data.get('status', 'unknown')}")
            return True
        else:
            print_result("XR 主系統", False, f"HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_result("XR 主系統", False, "連接失敗 - 服務未啟動")
        return False
    except Exception as e:
        print_result("XR 主系統", False, f"錯誤: {e}")
        return False

def test_dashboard_health():
    """測試儀表板健康狀態"""
    print_header("測試儀表板連接")
    
    try:
        response = requests.get(f"{DASHBOARD_URL}/stats", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print_result("儀表板", True, f"公理數: {data.get('total_axioms', 0)}")
            return True
        else:
            print_result("儀表板", False, f"HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_result("儀表板", False, "連接失敗 - 儀表板未啟動")
        return False
    except Exception as e:
        print_result("儀表板", False, f"錯誤: {e}")
        return False

def test_xrbus_connection():
    """測試 XR-BUS 連接（如果有的話）"""
    print_header("測試 XR-BUS 連接")
    
    try:
        response = requests.get(f"{XRBUS_URL}/health", timeout=2)
        if response.status_code == 200:
            print_result("XR-BUS", True, "已連接")
            return True
        else:
            print_result("XR-BUS", False, "未回應")
            return False
    except:
        print_result("XR-BUS", False, "未啟動或不存在")
        return False

def test_data_sync():
    """測試數據同步"""
    print_header("測試儀表板-XR 數據同步")
    
    # 從儀表板獲取統計
    try:
        dash_resp = requests.get(f"{DASHBOARD_URL}/stats", timeout=3)
        if dash_resp.status_code != 200:
            print_result("獲取儀表板數據", False)
            return
        
        dash_data = dash_resp.json()
        print_result("儀表板數據", True, f"總公理: {dash_data.get('total_axioms', 0)}")
        
        # 從 XR 系統獲取公理列表
        xr_resp = requests.get(f"{XR_API_URL}/axioms", timeout=3)
        if xr_resp.status_code == 200:
            xr_data = xr_resp.json()
            axioms = xr_data.get('axioms', [])
            print_result("XR 系統數據", True, f"公理數: {len(axioms)}")
            
            # 比對數量（簡單版）
            dash_count = dash_data.get('total_axioms', 0)
            xr_count = len(axioms)
            
            if abs(dash_count - xr_count) < 10:  # 容忍差異
                print_result("數據一致性", True, f"儀表板:{dash_count} vs XR:{xr_count}")
            else:
                print_result("數據一致性", False, f"差異過大: {dash_count} vs {xr_count}")
        else:
            print_result("XR 系統數據", False, f"HTTP {xr_resp.status_code}")
            
    except Exception as e:
        print_result("同步測試", False, f"錯誤: {e}")

def test_submit_axiom():
    """測試提交公理流程"""
    print_header("測試提交公理流程")
    
    # 測試公理
    test_axiom = {
        'name': 'XR-BUS Test Axiom',
        'domain': 'thermal',
        'mathematical_form': {
            'type': 'linear',
            'form': 'y = 2.5x + 1.0'
        },
        'confidence': 0.95,
        'requires_expert': False,
        'source': 'xrbus_test'
    }
    
    # 1. 提交到儀表板
    try:
        print("\n步驟 1: 提交到儀表板")
        resp = requests.post(
            f"{DASHBOARD_URL}/submit_axiom",
            json=test_axiom,
            timeout=5
        )
        
        if resp.status_code == 200:
            result = resp.json()
            print_result("儀表板提交", True, f"ID: {result.get('candidate_id', 'unknown')}")
        else:
            print_result("儀表板提交", False, f"HTTP {resp.status_code}")
            return
    except Exception as e:
        print_result("儀表板提交", False, f"錯誤: {e}")
        return
    
    # 2. 檢查待審清單
    try:
        print("\n步驟 2: 檢查待審清單")
        resp = requests.get(f"{DASHBOARD_URL}/pending_reviews", timeout=3)
        if resp.status_code == 200:
            pending = resp.json()
            print_result("待審清單", True, f"{len(pending)} 筆待審")
            
            # 找到剛剛提交的公理
            found = any(p.get('name') == test_axiom['name'] for p in pending)
            if found:
                print_result("公理存在", True, "已加入待審清單")
            else:
                print_result("公理存在", False, "未找到")
        else:
            print_result("待審清單", False, f"HTTP {resp.status_code}")
    except Exception as e:
        print_result("待審清單檢查", False, f"錯誤: {e}")
    
    print("\n✅ 提交流程測試完成")

def main():
    """主測試函數"""
    print("\n" + "="*70)
    print("🚀 XR-BUS 通訊確認測試")
    print("="*70)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*70)
    
    # 依序測試
    dashboard_ok = test_dashboard_health()
    xr_ok = test_xr_health()
    
    if dashboard_ok and xr_ok:
        test_data_sync()
        test_submit_axiom()
    else:
        print("\n⚠️ 部分服務未啟動，跳過進階測試")
        print("   請先啟動必要的服務：")
        if not dashboard_ok:
            print("   - 儀表板: python dashboard_server.py")
        if not xr_ok:
            print("   - XR 系統: 依實際指令啟動")
    
    test_xrbus_connection()
    
    print("\n" + "="*70)
    print("✅ 測試完成")
    print("="*70)

if __name__ == "__main__":
    main()
