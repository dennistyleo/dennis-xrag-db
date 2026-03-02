#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db_config import XRAGDatabase
from src.db_interface import XRAGInterface

def seed_all_axioms():
    print("🚀 Seeding XRAG database with initial axioms...")
    
    db = XRAGDatabase('data/xrag_complete.db')
    interface = XRAGInterface(db)
    
    # 1. Add XR Variables
    print("\n📊 Adding XR variables...")
    xr_vars = [
        ('R', 'resistance', 'Ω', 'Electrical resistance', 0, 1e9, 'electrical'),
        ('L', 'inductance', 'H', 'Inductance', 0, 100, 'electrical'),
        ('C', 'capacitance', 'F', 'Capacitance', 0, 1, 'electrical'),
        ('f', 'frequency', 'Hz', 'Frequency', 0, 1e12, 'electrical'),
        ('T', 'temperature', 'K', 'Absolute temperature', 0, 10000, 'thermal'),
        ('k', 'thermal_conductivity', 'W/m·K', 'Thermal conductivity', 0.01, 1000, 'thermal'),
        ('Q', 'heat_flow', 'W', 'Heat flow rate', 0, 1e12, 'thermal'),
        ('A', 'area', 'm²', 'Area', 1e-12, 1e6, 'thermal'),
        ('ΔT', 'temp_diff', 'K', 'Temperature difference', 0, 5000, 'thermal'),
        ('d', 'thickness', 'm', 'Thickness', 1e-9, 100, 'thermal'),
    ]
    
    for var in xr_vars:
        interface.add_variable({
            'symbol': var[0],
            'name': var[1],
            'unit': var[2],
            'description': var[3],
            'min_range': var[4],
            'max_range': var[5],
            'domain': var[6]
        })
    print(f"  ✅ Added {len(xr_vars)} XR variables")
    
    # 2. Add Thermal Axioms
    print("\n🔥 Adding thermal axioms...")
    thermal_axioms = [
        {
            'name': "Fourier's Law (1D Steady-State)",
            'domain': 'thermal',
            'subdomain': 'conduction',
            'computational_core': {
                'type': 'heat_conduction',
                'form': 'Q = k·A·ΔT/d'
            },
            'input_signature': {
                'required_vars': ['k', 'A', 'ΔT', 'd']
            },
            'output_signature': {
                'variable': 'Q',
                'units': 'W'
            },
            'xr_variables': 'k,A,ΔT,d,Q',
            'human_verified': 1,
            'verified_date': '2025-01-01',
            'version': 1
        }
    ]
    
    for axiom in thermal_axioms:
        interface.add_axiom(axiom)
    print(f"  ✅ Added {len(thermal_axioms)} thermal axioms")
    
    print("\n" + "="*50)
    print("✅ XRAG DATABASE INITIALIZATION COMPLETE")
    print("="*50)

if __name__ == "__main__":
    seed_all_axioms()
