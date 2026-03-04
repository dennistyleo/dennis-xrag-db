"""
XRAG Core Engine - 5-Stage Pipeline
Orchestrates L1-L5 to generate axioms from raw data
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import time as timer  # 重命名為 timer 避免與參數衝突
import json

from .stage1_characterization import ProblemCharacterizer, SignalFeatures
from .stage2_generation import PathwayGenerator, Hypothesis
from .stage3_feasibility import FeasibilityAssessor, FeasibilityResult
from .stage4_calibration import ParameterCalibrator, CalibratedModel
from .stage5_explainability import ExplainabilityEngine, AuditReport

@dataclass
class XRAGResult:
    """Complete XRAG pipeline result"""
    
    # L1 result
    features: Optional[SignalFeatures]
    
    # L2 result
    candidates: List[Hypothesis]
    
    # L3 result
    feasibility_results: List[FeasibilityResult]
    feasible_hypotheses: List[Hypothesis]
    
    # L4 result
    calibrated_models: List[Optional[CalibratedModel]]
    best_model_idx: int
    model_comparison: Dict
    
    # L5 result
    report: Optional[AuditReport]
    freeze_package: Dict
    
    # Metadata
    runtime_ms: float
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        d = asdict(self)
        # Handle non-serializable objects
        d['features'] = self.features.to_dict() if self.features else None
        d['candidates'] = [c.to_dict() if hasattr(c, 'to_dict') else {'name': c.name} for c in self.candidates]
        d['feasibility_results'] = [r.to_dict() if hasattr(r, 'to_dict') else {} for r in self.feasibility_results]
        d['feasible_hypotheses'] = [c.to_dict() if hasattr(c, 'to_dict') else {'name': c.name} for c in self.feasible_hypotheses]
        d['calibrated_models'] = [m.to_dict() if m and hasattr(m, 'to_dict') else None for m in self.calibrated_models]
        d['report'] = self.report.to_dict() if self.report else None
        return d
    
    def save(self, filename: str):
        """Save result to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

class XRAGEngine:
    """
    XRAG Core Engine - 5-Stage Pipeline
    
    Orchestrates the complete axiom generation process:
    L1: Problem Characterization
    L2: Pathway Generation
    L3: Feasibility Assessment (Uncompromising Filter)
    L4: Parameter Calibration
    L5: Explainability & Audit
    """
    
    def __init__(self, 
                 calibration_method: str = "auto",
                 strict_filtering: bool = True,
                 max_candidates_to_calibrate: int = 10,
                 verbose: bool = True):
        """
        Initialize XRAG Engine
        
        Args:
            calibration_method: "mcmc", "optimization", "approximate", or "auto"
            strict_filtering: If True, any feasibility violation leads to rejection
            max_candidates_to_calibrate: Maximum number of models to calibrate
            verbose: Print progress
        """
        self.name = "XRAG-CORE"
        self.version = "2.0.0"
        self.verbose = verbose
        self.max_candidates_to_calibrate = max_candidates_to_calibrate
        
        # Initialize the 5 stages
        self.l1 = ProblemCharacterizer()
        self.l2 = PathwayGenerator()
        self.l3 = FeasibilityAssessor(strict_mode=strict_filtering)
        self.l4 = ParameterCalibrator(method=calibration_method)
        self.l5 = ExplainabilityEngine()
        
        if verbose:
            print(f"✅ XRAG Core Engine v{self.version} initialized")
            print(f"   Calibration method: {calibration_method}")
            print(f"   Strict filtering: {strict_filtering}")
            print("   5-Stage Pipeline Ready:")
            print("   L1: Problem Characterization")
            print("   L2: Pathway Generation (136+ families)")
            print("   L3: Feasibility Assessment (Uncompromising Filter)")
            print("   L4: Parameter Calibration")
            print("   L5: Explainability & Audit")
    
    def run(self,
            signal: np.ndarray,
            time: Optional[np.ndarray] = None,
            domain: str = "general",
            sampling_rate: Optional[float] = None,
            return_all: bool = True) -> XRAGResult:
        """
        Run the complete 5-stage XRAG pipeline
        
        Args:
            signal: Raw signal data (1D numpy array)
            time: Optional time vector
            domain: Application domain (thermal, aging, electrical, etc.)
            sampling_rate: Optional sampling rate in Hz
            return_all: Return all results (if False, returns minimal result)
            
        Returns:
            Complete XRAG result with all stages
        """
        
        start_time = timer.time()
        
        try:
            if self.verbose:
                print("\n" + "="*70)
                print("🚀 XRAG Core Engine - Starting 5-Stage Pipeline")
                print("="*70)
            
            # === STAGE 1: Problem Characterization ===
            if self.verbose:
                print("\n📊 L1: Problem Characterization")
                print("-"*50)
            
            features = self.l1.characterize(signal, time, sampling_rate)
            
            if self.verbose:
                print(f"   ✓ Stationary: {features.is_stationary}")
                print(f"   ✓ SNR: {features.snr_db:.2f} dB")
                print(f"   ✓ Length: {features.length} samples")
                print(f"   ✓ Regimes: {features.n_regimes}")
                print(f"   ✓ Differentiability: C^{features.differentiability_order}")
            
            # === STAGE 2: Pathway Generation ===
            if self.verbose:
                print("\n🧪 L2: Pathway Generation")
                print("-"*50)
            
            candidates = self.l2.generate(features)
            
            if self.verbose:
                print(f"   ✓ Generated {len(candidates)} candidate hypotheses")
                print(f"     Families: {len(set(c.family.value for c in candidates))}")
            
            # === STAGE 3: Feasibility Assessment (Uncompromising Filter) ===
            if self.verbose:
                print("\n🔍 L3: Feasibility Assessment")
                print("-"*50)
            
            feasibility_results = self.l3.assess(candidates, features, domain)
            
            # Get indices of feasible hypotheses
            feasible_indices = [i for i, r in enumerate(feasibility_results) if r.passed]
            feasible_hypotheses = [candidates[i] for i in feasible_indices]
            
            if self.verbose:
                print(f"   ✓ {len(feasible_hypotheses)} passed feasibility filter")
                print(f"   ✗ {len(candidates) - len(feasible_hypotheses)} rejected")
                
                # Show top rejection reasons
                if len(candidates) - len(feasible_hypotheses) > 0:
                    rejections = {}
                    for r in feasibility_results:
                        if not r.passed and r.rejection_reason:
                            reason = r.rejection_reason.split(':')[0]
                            rejections[reason] = rejections.get(reason, 0) + 1
                    
                    print("     Top reasons:")
                    for reason, count in sorted(rejections.items(), key=lambda x: x[1], reverse=True)[:3]:
                        print(f"       • {reason}: {count}")
            
            # === STAGE 4: Parameter Calibration ===
            if self.verbose:
                print("\n📈 L4: Parameter Calibration")
                print("-"*50)
            
            calibrated_models = []
            
            # Select top candidates by complexity (simpler first for speed)
            calibration_candidates = feasible_hypotheses[:self.max_candidates_to_calibrate]
            
            if self.verbose:
                print(f"   Calibrating {len(calibration_candidates)} models...")
            
            # Prepare data
            x_data = time if time is not None else np.arange(len(signal))
            y_data = signal
            
            for i, h in enumerate(calibration_candidates):
                if self.verbose:
                    print(f"   [{i+1}/{len(calibration_candidates)}] {h.name}...", end="", flush=True)
                
                model = self.l4.calibrate(h, x_data, y_data)
                calibrated_models.append(model)
                
                if self.verbose:
                    if model:
                        print(f" R²={model.r2:.3f}")
                    else:
                        print(" failed")
            
            # Filter out None models for comparison
            valid_models = [m for m in calibrated_models if m is not None]
            
            # Select best model (by R²)
            best_model_idx = -1
            model_comparison = {}
            
            if valid_models:
                # Find best model in the original list
                best_r2 = -float('inf')
                for i, m in enumerate(calibrated_models):
                    if m is not None and m.r2 > best_r2:
                        best_r2 = m.r2
                        best_model_idx = i
                
                # Compare models
                model_comparison = self.l4.compare_models(valid_models)
                
                if self.verbose and best_model_idx >= 0:
                    best = calibrated_models[best_model_idx]
                    print(f"\n   🏆 Best model: {best.hypothesis_name}")
                    print(f"      R² = {best.r2:.3f}")
                    print(f"      WAIC = {best.waic:.1f}")
                    print(f"      MAE = {best.mae:.4f}")
                    
                    # Show top parameters
                    param_str = []
                    for p, v in list(best.parameters.items())[:3]:
                        if p in best.parameter_std:
                            param_str.append(f"{p}={v:.3f}±{2*best.parameter_std[p]:.3f}")
                    if param_str:
                        print(f"      Parameters: {', '.join(param_str)}")
            
            # === STAGE 5: Explainability & Audit ===
            if self.verbose:
                print("\n📝 L5: Explainability & Audit")
                print("-"*50)
            
            report = self.l5.generate_report(
                features, candidates, feasibility_results,
                calibrated_models, best_model_idx, model_comparison
            )
            
            freeze_package = self.l5.export_freeze_package(report)
            
            if self.verbose:
                print(f"   ✓ Report ID: {report.report_id}")
                print(f"   ✓ Hash: {report.report_hash[:16]}...")
                print(f"   ✓ Executive summary generated")
                print(f"   ✓ {len(report.recommendations)} recommendations")
            
            runtime = (timer.time() - start_time) * 1000  # ms
            
            if self.verbose:
                print("\n" + "="*70)
                print(f"✅ XRAG Pipeline Complete in {runtime:.0f} ms")
                print("="*70)
            
            if return_all:
                return XRAGResult(
                    features=features,
                    candidates=candidates,
                    feasibility_results=feasibility_results,
                    feasible_hypotheses=feasible_hypotheses,
                    calibrated_models=calibrated_models,
                    best_model_idx=best_model_idx,
                    model_comparison=model_comparison,
                    report=report,
                    freeze_package=freeze_package,
                    runtime_ms=runtime,
                    success=True
                )
            else:
                # Return minimal result
                return XRAGResult(
                    features=features,
                    candidates=[],
                    feasibility_results=[],
                    feasible_hypotheses=[],
                    calibrated_models=[],
                    best_model_idx=best_model_idx,
                    model_comparison={},
                    report=report,
                    freeze_package=freeze_package,
                    runtime_ms=runtime,
                    success=True
                )
            
        except Exception as e:
            runtime = (timer.time() - start_time) * 1000
            print(f"\n❌ XRAG Pipeline Failed: {e}")
            import traceback
            traceback.print_exc()
            
            return XRAGResult(
                features=None,
                candidates=[],
                feasibility_results=[],
                feasible_hypotheses=[],
                calibrated_models=[],
                best_model_idx=-1,
                model_comparison={},
                report=None,
                freeze_package={},
                runtime_ms=runtime,
                success=False,
                error=str(e)
            )
    
    def run_batch(self, 
                  signals: List[np.ndarray],
                  times: Optional[List[np.ndarray]] = None,
                  domain: str = "general",
                  parallel: bool = False) -> List[XRAGResult]:
        """
        Run XRAG pipeline on multiple signals
        
        Args:
            signals: List of signals
            times: List of time vectors (optional)
            domain: Application domain
            parallel: Run in parallel (if True)
            
        Returns:
            List of results
        """
        results = []
        
        if parallel:
            try:
                from concurrent.futures import ProcessPoolExecutor
                with ProcessPoolExecutor() as executor:
                    futures = []
                    for i, signal in enumerate(signals):
                        time_vec = times[i] if times else None
                        futures.append(
                            executor.submit(self.run, signal, time_vec, domain, None, False)
                        )
                    
                    for future in futures:
                        results.append(future.result())
            except:
                # Fall back to sequential
                for i, signal in enumerate(signals):
                    time_vec = times[i] if times else None
                    results.append(self.run(signal, time_vec, domain, None, False))
        else:
            for i, signal in enumerate(signals):
                time_vec = times[i] if times else None
                results.append(self.run(signal, time_vec, domain, None, False))
        
        return results
    
    def get_summary(self, result: XRAGResult) -> Dict:
        """Get quick summary of results"""
        if not result.success:
            return {"success": False, "error": result.error}
        
        summary = {
            "success": True,
            "runtime_ms": result.runtime_ms,
            "n_candidates": len(result.candidates),
            "n_feasible": len(result.feasible_hypotheses),
            "n_calibrated": len([m for m in result.calibrated_models if m is not None]),
            "best_model": None
        }
        
        if result.best_model_idx >= 0 and result.calibrated_models[result.best_model_idx]:
            best = result.calibrated_models[result.best_model_idx]
            summary["best_model"] = {
                "name": best.hypothesis_name,
                "r2": best.r2,
                "mae": best.mae,
                "parameters": best.parameters
            }
        
        return summary
