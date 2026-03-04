import sqlite3
import json

conn = sqlite3.connect('data/xrag_complete.db')
conn.row_factory = sqlite3.Row

cursor = conn.execute("SELECT * FROM known_axioms WHERE domain='thermal' ORDER BY name")
axioms = [dict(row) for row in cursor]

with open('docs/axioms_thermal.json', 'w', encoding='utf-8') as f:
    json.dump({
        'domain': 'thermal',
        'count': len(axioms),
        'axioms': axioms
    }, f, indent=2, ensure_ascii=False)

print(f"✅ 已導出 {len(axioms)} 條熱學公理")
