# XRAG Axiom Engine - Core Component of XR Ecosystem

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![FPGA Ready](https://img.shields.io/badge/FPGA-ready-orange.svg)](docs/fpga/README.md)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 📋 Overview

XRAG (Extreme Reliability Axiom Generator) is the core axiom engine of the XR ecosystem, providing:

- **136+ Cross-domain axioms**: Covering 17 engineering domains
- **Multi-layer matching engine**: Syntax tree, variable signature, boundary condition matching
- **RESTful API**: Easy integration with any system
- **Real-time dashboard**: Visual management interface
- **FPGA ready**: Hardware acceleration up to 46,000x

## 🏗️ System Architecture
┌─────────────────────────────────────────────────────┐
│ XRAG Core │
├─────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │ Matcher │ │ Axiom │ │ Unknown │ │
│ │ Engine │ │ Library │ │ Channel │ │
│ │(CPU/FPGA)│ │ (136) │ │ (Review) │ │
│ └──────────┘ └──────────┘ └──────────┘ │
├─────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │ REST API │ │Dashboard │ │ XR-BUS │ │
│ │ (5001) │ │ (5002) │ │ Interface│ │
│ └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────────────────┘

text

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/dennistyleo/dennis-xrag-db.git
cd dennis-xrag-db

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py
python scripts/seed_all_axioms.py
Start Services
bash
# Terminal 1: API Server
python src/api_server.py

# Terminal 2: Dashboard
python dashboard_server.py
Access Interfaces
Dashboard: http://localhost:5002

API: http://localhost:5001/api

📊 API Reference
Endpoint	Method	Description
/api/health	GET	Health check
/api/axioms	GET	List all axioms
/api/variables	GET	List XR variables
/api/match	POST	Match axiom
/api/unknown	POST	Submit to unknown channel
Match Axiom Example
bash
curl -X POST http://localhost:5001/api/match \
  -H "Content-Type: application/json" \
  -d '{
    "candidate": {
      "name": "Test Axiom",
      "domain": "thermal",
      "computational_core": {
        "type": "heat_conduction",
        "form": "Q = k·A·ΔT/d"
      }
    }
  }'
🔌 XR System Integration
python
import requests

class XRAGClient:
    def __init__(self, url="http://localhost:5001"):
        self.url = url
    
    def match(self, axiom):
        response = requests.post(
            f"{self.url}/api/match",
            json={"candidate": axiom}
        )
        return response.json()
    
    def submit_unknown(self, axiom, reason=""):
        response = requests.post(
            f"{self.url}/api/unknown",
            json={"candidate": axiom, "reason": reason}
        )
        return response.json()

# Usage
client = XRAGClient()
result = client.match({
    "domain": "thermal",
    "computational_core": {"form": "Q = k·A·ΔT/d"}
})
🖥️ FPGA Hardware Acceleration
XRAG supports FPGA acceleration with 46,000x performance improvement.

FPGA Specifications
Metric	Software	FPGA	Speedup
Match Latency	2.3 ms	50 ns	46,000x
Throughput	430 ops/s	20M ops/s	46,500x
Power	65W	5W	13x
Axiom Capacity	136	1024	7.5x
📁 Project Structure
text
xrag-axiom-engine/
├── src/                    # Core source code
│   ├── api_server.py       # REST API
│   ├── matcher_engine.py   # Matching engine
│   ├── db_config.py        # Database config
│   └── ...
├── tests/                  # Test files
│   ├── test_matcher.py
│   └── test_xr_integration.py
├── templates/              # Dashboard templates
│   └── dashboard.html
├── static/                 # Static files
│   └── aichip-logo.png
├── data/                   # Database
│   └── xrag_complete.db
├── docs/                   # Documentation
│   └── fpga/               # FPGA design docs
├── scripts/                # Utility scripts
│   ├── init_db.py
│   └── seed_all_axioms.py
├── requirements.txt        # Python dependencies
└── README.md               # This file
📊 Axiom Statistics
Domain	Count
Electrical	2
Thermal	7
EMC	3
Fluid Dynamics	3
Mechanics	3
Thermodynamics	4
Semiconductor	4
Quantum	3
Aging	9
Causal Drift	9
Statistics	9
Control Theory	9
Information Theory	9
Financial Engineering	9
Power Supply	9
Substrate Materials	12
Manufacturing	12
Healthcare	12
Quality Management	12
Total	136+
🧪 Running Tests
bash
# Run all tests
pytest tests/

# Run integration test
python tests/test_xr_xrag_integration.py
🤝 Contributing
Fork the project

Create feature branch (git checkout -b feature/amazing-feature)

Commit changes (git commit -m 'Add amazing feature')

Push to branch (git push origin feature/amazing-feature)

Open a Pull Request

📝 License
MIT License - see LICENSE file

📧 Contact
Author: Dennis T.Y. Liu

Project Link: https://github.com/dennistyleo/dennis-xrag-db

🙏 Acknowledgements
Alex Struver - UPASL Integration

AICHIP Corporation - Support & Resources

Built with 🔧 for Extreme Reliability
