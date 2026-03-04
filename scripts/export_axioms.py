import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('data/xrag_complete.db')
conn.row_factory = sqlite3.Row

# 獲取所有公理
cursor = conn.execute('SELECT * FROM known_axioms ORDER BY domain, name')
axioms = [dict(row) for row in cursor]

# 處理 JSON 欄位
for axiom in axioms:
    for field in ['computational_core', 'input_signature', 'output_signature', 
                  'boundary_conditions', 'precision_requirements']:
        if axiom.get(field):
            try:
                axiom[field] = json.loads(axiom[field])
            except:
                pass

# 按領域分組
domains = {}
for axiom in axioms:
    domain = axiom['domain']
    if domain not in domains:
        domains[domain] = []
    domains[domain].append(axiom)

# 完整導出
with open('docs/axioms_complete.json', 'w', encoding='utf-8') as f:
    json.dump({
        'total': len(axioms),
        'export_date': datetime.now().isoformat(),
        'domains': domains
    }, f, indent=2, ensure_ascii=False)

# 統計導出
with open('docs/axioms_stats.json', 'w', encoding='utf-8') as f:
    json.dump({
        'total': len(axioms),
        'by_domain': {domain: len(axioms) for domain, axioms in domains.items()}
    }, f, indent=2)

print(f"✅ 已導出 {len(axioms)} 條公理")
print(f"📊 涵蓋 {len(domains)} 個領域")
