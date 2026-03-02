<<<<<<< HEAD
# XRAG 公理引擎

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 📋 專案簡介

XRAG 公理引擎是一個跨領域的知識庫與匹配系統，支援 17 大領域、132+ 條公理，提供 RESTful API 進行 AI 自創公理的相似度匹配。

## ✨ 功能特色

- **多領域知識庫**：電學、熱學、EMC、流體力學、固體力學、半導體、量子力學、老化、因果漂移、統計指標、控制理論、資訊理論、財務工程、電源行為、基板材料、製造工藝、醫療保健、品質管理
- **多層次匹配**：語法樹、變數簽章、邊界條件、類比推理
- **未知通道**：無匹配公理自動儲存，支援人工審查
- **RESTful API**：完整的 HTTP 介面，易於整合
- **輕量級**：SQLite 資料庫，無需額外服務

## 🚀 快速開始

### 安裝

```bash
# 克隆倉庫
git clone https://github.com/yourusername/xrag-axiom-engine.git
cd xrag-axiom-engine

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt

# 初始化資料庫
python scripts/init_db.py
python scripts/seed_all_axioms.py
# 啟動 API 伺服器
python src/api_server.py
# 健康檢查
curl http://localhost:5001/api/health

# 查看所有公理
curl http://localhost:5001/api/axioms

# 匹配公理
curl -X POST http://localhost:5001/api/match \\
  -H "Content-Type: application/json" \\
  -d '{
    "candidate": {
      "name": "Test_Axiom",
      "domain": "thermal",
      "computational_core": {
        "type": "heat_conduction",
        "form": "Q = k·A·ΔT/d"
      },
      "input_signature": {
        "required_vars": ["k", "A", "ΔT", "d"]
      }
    }
  }'
cat > README.md << 'EOF'
# XRAG 公理引擎

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 📋 專案簡介

XRAG 公理引擎是一個跨領域的知識庫與匹配系統，支援 17 大領域、132+ 條公理，提供 RESTful API 進行 AI 自創公理的相似度匹配。

## ✨ 功能特色

- **多領域知識庫**：電學、熱學、EMC、流體力學、固體力學、半導體、量子力學、老化、因果漂移、統計指標、控制理論、資訊理論、財務工程、電源行為、基板材料、製造工藝、醫療保健、品質管理
- **多層次匹配**：語法樹、變數簽章、邊界條件、類比推理
- **未知通道**：無匹配公理自動儲存，支援人工審查
- **RESTful API**：完整的 HTTP 介面，易於整合
- **輕量級**：SQLite 資料庫，無需額外服務

## 🚀 快速開始

### 安裝

```bash
# 克隆倉庫
git clone https://github.com/yourusername/xrag-axiom-engine.git
cd xrag-axiom-engine

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt

# 初始化資料庫
python scripts/init_db.py
python scripts/seed_all_axioms.pycat > README.md << 'EOF'
# XRAG 公理引擎

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 📋 專案簡介

XRAG 公理引擎是一個跨領域的知識庫與匹配系統，支援 17 大領域、132+ 條公理，提供 RESTful API 進行 AI 自創公理的相似度匹配。

## ✨ 功能特色

- **多領域知識庫**：電學、熱學、EMC、流體力學、固體力學、半導體、量子力學、老化、因果漂移、統計指標、控制理論、資訊理論、財務工程、電源行為、基板材料、製造工藝、醫療保健、品質管理
- **多層次匹配**：語法樹、變數簽章、邊界條件、類比推理
- **未知通道**：無匹配公理自動儲存，支援人工審查
- **RESTful API**：完整的 HTTP 介面，易於整合
- **輕量級**：SQLite 資料庫，無需額外服務

## 🚀 快速開始

### 安裝

```bash
# 克隆倉庫
git clone https://github.com/yourusername/xrag-axiom-engine.git
cd xrag-axiom-engine

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt

# 初始化資料庫
python scripts/init_db.py
python scripts/seed_all_axioms.py
啟動服務
bash
# 啟動 API 伺服器
python src/api_server.py
測試
bash
# 健康檢查
curl http://localhost:5001/api/health

# 查看所有公理
curl http://localhost:5001/api/axioms

# 匹配公理
curl -X POST http://localhost:5001/api/match \\
  -H "Content-Type: application/json" \\
  -d '{
    "candidate": {
      "name": "Test_Axiom",
      "domain": "thermal",
      "computational_core": {
        "type": "heat_conduction",
        "form": "Q = k·A·ΔT/d"
      },
      "input_signature": {
        "required_vars": ["k", "A", "ΔT", "d"]
      }
    }
  }'
📚 API 文檔
端點	方法	說明
/api/health	GET	健康檢查
/api/axioms	GET	列出所有公理
/api/variables	GET	列出 XR 變數
/api/match	POST	匹配公理
/api/unknown	POST	存入未知通道
📊 資料庫結構
known_axioms - 已知公理

xr_variables - XR 標準變數

match_history - 匹配歷史

unknown_candidates - 未知候選

📦 領域統計
領域	數量
電學	2
熱學	7
EMC	3
流體力學	3
固體力學	3
半導體	4
量子力學	3
老化	9
因果漂移	9
統計指標	9
控制理論	9
資訊理論	9
財務工程	9
電源行為	9
基板材料	12
製造工藝	12
醫療保健	12
品質管理	12
總計	132+
📝 授權
MIT License

🤝 貢獻
歡迎提交 Issue 或 Pull Request！
=======
# dennis-xrag-db
Extreme Reliability Axiom Generator
>>>>>>> f63aebb069ec9e4032a2f42c53083bf3d551f73b
