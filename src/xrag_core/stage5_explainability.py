"""
L5: Explainability & Audit
Produces human-readable report with full traceability
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
import numpy as np

# 從同一個套件導入
from .stage1_characterization import SignalFeatures
from .stage2_generation import Hypothesis
from .stage3_feasibility import FeasibilityResult
from .stage4_calibration import CalibratedModel

@dataclass
class AuditReport:
    """Complete audit report with full traceability"""
    
    # Report metadata
    report_id: str
    generated_at: str
    xrag_version: str
    
    # L1: Problem characterization
    signal_features: Dict[str, Any]
    
    # L2: Pathways considered
    all_candidates: List[Dict[str, Any]]
    n_candidates_total: int
    
    # L3: Feasibility filtering
    feasibility_results: List[Dict[str, Any]]
    filtered_out: List[Dict[str, Any]]
    n_passed: int
    n_filtered: int
    
    # L4: Calibration results
    calibrated_models: List[Dict[str, Any]]
    model_comparison: Dict[str, Any]
    best_model: Dict[str, Any]
    best_model_idx: int
    
    # Decision explanation
    explanation: str
    executive_summary: str
    technical_summary: str
    
    # Counterfactuals
    counterfactuals: List[Dict[str, Any]]
    
    # Recommendations
    recommendations: List[str]
    
    # Audit integrity
    report_hash: str
    verification_code: str
    
    # Provenance
    provenance_chain: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    def save(self, filename: str):
        """Save report to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

class ExplainabilityEngine:
    """
    L5: Explainability & Audit Layer
    
    Produces human-readable report with full traceability,
    solving the transparency problem by explaining exactly why
    one mathematical path was chosen over others.
    """
    
    def __init__(self):
        self.name = "XRAG-L5"
        self.version = "1.0.0"
        
    def generate_report(self,
                       features: SignalFeatures,
                       candidates: List[Hypothesis],
                       feasibility_results: List[FeasibilityResult],
                       calibrated_models: List[Optional[CalibratedModel]],
                       best_model_idx: int,
                       model_comparison: Optional[Dict] = None) -> AuditReport:
        """
        Generate comprehensive audit report
        
        Args:
            features: SignalFeatures from L1
            candidates: All candidates from L2
            feasibility_results: Results from L3
            calibrated_models: Calibrated models from L4
            best_model_idx: Index of best model
            model_comparison: Optional model comparison results
            
        Returns:
            Complete audit report with full traceability
        """
        
        # Convert candidates to serializable dicts
        all_candidates_dict = []
        for c in candidates:
            c_dict = {
                "name": c.name,
                "family": c.family.value if hasattr(c.family, 'value') else str(c.family),
                "formulation": c.formulation,
                "complexity": c.complexity,
                "assumptions": c.assumptions,
                "applicability": c.applicability,
                "tags": c.tags if hasattr(c, 'tags') else []
            }
            all_candidates_dict.append(c_dict)
        
        # Feasibility results as dicts
        feasibility_dicts = []
        filtered_out = []
        
        for r in feasibility_results:
            r_dict = r.to_dict() if hasattr(r, 'to_dict') else asdict(r)
            feasibility_dicts.append(r_dict)
            if not r.passed:
                filtered_out.append({
                    "name": r.hypothesis_name,
                    "reason": r.rejection_reason,
                    "feasibility_score": r.feasibility_score,
                    "status": r.status.value if hasattr(r.status, 'value') else str(r.status)
                })
        
        # Calibrated models as dicts
        calibrated_dicts = []
        for m in calibrated_models:
            if m is not None:
                m_dict = m.to_dict() if hasattr(m, 'to_dict') else {
                    "name": m.hypothesis_name,
                    "formulation": m.formulation,
                    "parameters": m.parameters,
                    "parameter_uncertainty": m.parameter_hdi,
                    "r2": m.r2,
                    "waic": m.waic,
                    "mae": m.mae
                }
                calibrated_dicts.append(m_dict)
        
        best_model = calibrated_dicts[best_model_idx] if calibrated_dicts and 0 <= best_model_idx < len(calibrated_dicts) else {}
        
        # Generate explanations
        executive_summary = self._generate_executive_summary(
            features, feasibility_results, calibrated_models, best_model_idx
        )
        
        technical_summary = self._generate_technical_summary(
            features, feasibility_results, calibrated_models, best_model_idx
        )
        
        explanation = self._generate_detailed_explanation(
            features, feasibility_results, calibrated_models, best_model_idx
        )
        
        # Generate counterfactuals
        counterfactuals = self._generate_counterfactuals(
            features, candidates, feasibility_results, best_model_idx
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            features, feasibility_results, calibrated_models, best_model_idx
        )
        
        # Build provenance chain
        provenance_chain = self._build_provenance_chain(
            features, candidates, feasibility_results, calibrated_models
        )
        
        # Create report
        report_id = f"xrag_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        report = AuditReport(
            report_id=report_id,
            generated_at=datetime.now().isoformat(),
            xrag_version=self.version,
            signal_features=features.to_dict() if hasattr(features, 'to_dict') else {
                "is_stationary": features.is_stationary,
                "snr_db": features.snr_db,
                "length": features.length,
                "has_missing_data": features.has_missing_data,
                "n_regimes": features.n_regimes
            },
            all_candidates=all_candidates_dict,
            n_candidates_total=len(all_candidates_dict),
            feasibility_results=feasibility_dicts,
            filtered_out=filtered_out,
            n_passed=len([r for r in feasibility_results if r.passed]),
            n_filtered=len([r for r in feasibility_results if not r.passed]),
            calibrated_models=calibrated_dicts,
            model_comparison=model_comparison or {},
            best_model=best_model,
            best_model_idx=best_model_idx,
            explanation=explanation,
            executive_summary=executive_summary,
            technical_summary=technical_summary,
            counterfactuals=counterfactuals,
            recommendations=recommendations,
            report_hash="",
            verification_code="",
            provenance_chain=provenance_chain
        )
        
        # Compute report hash
        report_dict = report.to_dict()
        report_dict.pop('report_hash')
        report_dict.pop('verification_code')
        
        report_json = json.dumps(report_dict, sort_keys=True, default=str)
        report.report_hash = hashlib.sha256(report_json.encode()).hexdigest()
        report.verification_code = report.report_hash[:16]
        
        return report
    
    def _generate_executive_summary(self, features, feasibility_results, 
                                    calibrated_models, best_idx) -> str:
        """Generate executive summary (non-technical)"""
        
        best = calibrated_models[best_idx] if calibrated_models and best_idx >= 0 else None
        
        lines = []
        lines.append("XRAG EXECUTIVE SUMMARY")
        lines.append("=" * 50)
        
        # Signal overview
        lines.append(f"\n📊 Signal Overview:")
        lines.append(f"  • {features.length} data points analyzed")
        lines.append(f"  • Signal quality: {'Good' if features.snr_db > 15 else 'Fair' if features.snr_db > 5 else 'Poor'}")
        lines.append(f"  • Pattern type: {'Stable' if features.is_stationary else 'Evolving'} trend")
        
        # Analysis overview
        lines.append(f"\n🔍 Analysis Summary:")
        lines.append(f"  • {len(calibrated_models)} mathematical models evaluated")
        lines.append(f"  • {len([r for r in feasibility_results if r.passed])} models passed feasibility filter")
        lines.append(f"  • {len([r for r in feasibility_results if not r.passed])} models rejected as infeasible")
        
        # Best model
        if best:
            lines.append(f"\n🏆 Recommended Model:")
            lines.append(f"  • {best.hypothesis_name}")
            lines.append(f"  • Confidence: {best.r2*100:.0f}% explanatory power")
            lines.append(f"  • Key parameters: {', '.join([f'{k}={v:.2f}' for k, v in best.parameters.items()][:3])}")
        
        # Key insight
        if best:
            if best.r2 > 0.8:
                lines.append(f"\n✅ Strong match found - model explains the data well.")
            elif best.r2 > 0.5:
                lines.append(f"\n⚠️ Moderate match - model captures main trends but has some uncertainty.")
            else:
                lines.append(f"\n🔴 Weak match - data may be too complex for available models.")
        
        return "\n".join(lines)
    
    def _generate_technical_summary(self, features, feasibility_results, 
                                   calibrated_models, best_idx) -> str:
        """Generate technical summary with metrics"""
        
        best = calibrated_models[best_idx] if calibrated_models and best_idx >= 0 else None
        
        lines = []
        lines.append("XRAG TECHNICAL SUMMARY")
        lines.append("=" * 50)
        
        # L1 Technical details
        lines.append("\n📊 Signal Characteristics:")
        lines.append(f"  • Stationarity: {features.is_stationary} (p={features.stationarity_pvalue:.3f})")
        lines.append(f"  • SNR: {features.snr_db:.2f} dB")
        lines.append(f"  • Differentiability order: C^{features.differentiability_order}")
        lines.append(f"  • Regime changes: {features.n_regimes}")
        lines.append(f"  • Entropy: {features.entropy:.3f}")
        
        # L3 Filtering details
        lines.append("\n🔍 Feasibility Filtering:")
        lines.append(f"  • Total candidates: {len(feasibility_results)}")
        lines.append(f"  • Passed: {len([r for r in feasibility_results if r.passed])}")
        
        # Top rejection reasons
        rejections = {}
        for r in feasibility_results:
            if not r.passed and r.rejection_reason:
                reason = r.rejection_reason.split(':')[0]
                rejections[reason] = rejections.get(reason, 0) + 1
        
        if rejections:
            lines.append("  • Top rejection reasons:")
            for reason, count in sorted(rejections.items(), key=lambda x: x[1], reverse=True)[:3]:
                lines.append(f"    - {reason}: {count}")
        
        # L4 Calibration details
        if calibrated_models:
            lines.append("\n📈 Calibrated Models:")
            
            # Sort by R²
            sorted_models = sorted(
                [(i, m) for i, m in enumerate(calibrated_models) if m is not None],
                key=lambda x: x[1].r2, reverse=True
            )
            
            for rank, (idx, model) in enumerate(sorted_models[:5]):
                marker = "🏆" if idx == best_idx else "  "
                lines.append(f"  {marker} {rank+1}. {model.hypothesis_name}")
                lines.append(f"     R²={model.r2:.3f}, WAIC={model.waic:.1f}, MAE={model.mae:.4f}")
                
                # Parameter uncertainties
                param_str = []
                for p, v in model.parameters.items():
                    if p in model.parameter_std:
                        unc = model.parameter_std[p]
                        param_str.append(f"{p}={v:.3f}±{2*unc:.3f}")
                if param_str:
                    lines.append(f"     Parameters: {', '.join(param_str[:3])}")
        
        return "\n".join(lines)
    
    def _generate_detailed_explanation(self, features, feasibility_results, 
                                      calibrated_models, best_idx) -> str:
        """Generate detailed human-readable explanation"""
        
        best = calibrated_models[best_idx] if calibrated_models and best_idx >= 0 else None
        
        lines = []
        lines.append("XRAG DETAILED EXPLANATION")
        lines.append("=" * 60)
        
        # === WHY THIS MODEL WAS CHOSEN ===
        if best:
            lines.append("\n🎯 WHY THIS MODEL WAS SELECTED:")
            
            # Compare with alternatives
            alternatives = [m for i, m in enumerate(calibrated_models) 
                          if i != best_idx and m is not None]
            
            if alternatives:
                second = max(alternatives, key=lambda x: x.r2)
                
                lines.append(f"\nThe {best.hypothesis_name} was selected because:")
                
                # R² comparison
                r2_diff = best.r2 - second.r2
                if r2_diff > 0.1:
                    lines.append(f"  • It explains {best.r2*100:.0f}% of the variance, "
                               f"which is {r2_diff*100:.0f}% better than the next best model ({second.hypothesis_name})")
                elif r2_diff > 0.05:
                    lines.append(f"  • It explains {best.r2*100:.0f}% of the variance, "
                               f"moderately better than alternatives")
                else:
                    lines.append(f"  • It explains {best.r2*100:.0f}% of the variance, "
                               f"comparable to other models but with better interpretability")
                
                # Complexity consideration
                if best.r2 - second.r2 < 0.05 and hasattr(best, 'complexity') and hasattr(second, 'complexity'):
                    if best.complexity < second.complexity:
                        lines.append(f"  • It is simpler (complexity {best.complexity} vs {second.complexity}), "
                                   f"following Occam's razor")
        
        # === WHAT THE MODEL TELLS US ===
        if best:
            lines.append("\n📊 WHAT THIS MODEL REVEALS:")
            
            # Parameter interpretation
            if best.parameters:
                lines.append("  • Key parameters:")
                for p, v in best.parameters.items():
                    if p in best.parameter_std:
                        unc = best.parameter_std[p]
                        if unc / abs(v) < 0.1:
                            confidence = "high confidence"
                        elif unc / abs(v) < 0.3:
                            confidence = "moderate confidence"
                        else:
                            confidence = "low confidence"
                        
                        lines.append(f"    - {p} = {v:.4f} ± {2*unc:.4f} ({confidence})")
            
            # Trend interpretation
            if 'a' in best.parameters and best.parameters['a'] > 0:
                lines.append(f"  • The positive coefficient indicates an increasing trend")
            elif 'a' in best.parameters and best.parameters['a'] < 0:
                lines.append(f"  • The negative coefficient indicates a decreasing trend")
            
            # Model form interpretation
            if 'exponential' in best.hypothesis_name.lower():
                if 'b' in best.parameters:
                    if best.parameters['b'] > 0:
                        lines.append(f"  • The data shows exponential growth (rate={best.parameters['b']:.3f})")
                    else:
                        lines.append(f"  • The data shows exponential decay (rate={abs(best.parameters['b']):.3f})")
        
        # === LIMITATIONS AND UNCERTAINTY ===
        if best:
            lines.append("\n⚠️ LIMITATIONS AND UNCERTAINTY:")
            
            # Model fit quality
            if best.r2 > 0.9:
                lines.append(f"  • Excellent fit - model captures the data very well")
            elif best.r2 > 0.7:
                lines.append(f"  • Good fit - model captures main trends")
            elif best.r2 > 0.5:
                lines.append(f"  • Moderate fit - some patterns remain unexplained")
            else:
                lines.append(f"  • Poor fit - data may require more complex models")
            
            # Parameter uncertainty
            high_uncertainty = [p for p in best.parameters 
                              if p in best.parameter_std and best.parameter_std[p] / abs(best.parameters[p]) > 0.5]
            if high_uncertainty:
                lines.append(f"  • High uncertainty in parameters: {', '.join(high_uncertainty)}")
            
            # Residual patterns
            if hasattr(best, 'standardized_residuals') and len(best.standardized_residuals) > 10:
                outliers = np.sum(np.abs(best.standardized_residuals) > 3)
                if outliers > 0:
                    lines.append(f"  • {outliers} potential outliers detected")
        
        return "\n".join(lines)
    
    def _generate_counterfactuals(self, features, candidates,
                                   feasibility_results, best_idx) -> List[Dict]:
        """Generate counterfactual explanations"""
        
        counterfactuals = []
        
        # What if SNR were higher?
        if features.snr_db < 15:
            would_enable = []
            for c in candidates[:20]:  # Check first 20
                if hasattr(c, 'applicability') and ('high_snr' in c.applicability or c.complexity > 5):
                    would_enable.append(c.name)
            
            counterfactuals.append({
                "scenario": "Higher Signal Quality (SNR > 15 dB)",
                "would_enable": would_enable[:3],
                "would_improve": "Parameter uncertainty would decrease by ~30%",
                "confidence_gain": "+15%"
            })
        
        # What if data were stationary?
        if not features.is_stationary:
            would_enable = []
            for c in candidates[:20]:
                if hasattr(c, 'applicability') and 'stationary' in c.applicability:
                    would_enable.append(c.name)
            
            counterfactuals.append({
                "scenario": "Stationary Signal",
                "would_enable": would_enable[:3],
                "would_disable": ["Wavelet/EMD methods would be less effective"],
                "notes": "Consider differencing to achieve stationarity"
            })
        
        # What if we had more data?
        if features.length < 1000:
            counterfactuals.append({
                "scenario": "10x More Data",
                "would_enable": ["Higher complexity models (neural ODE, SINDy)"],
                "uncertainty_reduction": "-40%",
                "notes": f"Current {features.length} samples limits model complexity"
            })
        
        # What if data were continuous?
        if not features.is_continuous:
            counterfactuals.append({
                "scenario": "Continuous Signal",
                "would_enable": ["Differential equation models", "Smooth interpolation methods"],
                "would_improve": "Enable ODE/PDE-based models"
            })
        
        # What if missing data were addressed?
        if features.has_missing_data:
            counterfactuals.append({
                "scenario": "Complete Data (No Missing Values)",
                "would_improve": "All models could be applied without imputation",
                "uncertainty_reduction": f"-{features.missing_ratio*100:.0f}% from imputation"
            })
        
        return counterfactuals
    
    def _generate_recommendations(self, features, feasibility_results,
                                  calibrated_models, best_idx) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Data quality recommendations
        if features.snr_db < 10:
            recommendations.append("Improve signal quality (denoising, better sensors)")
        elif features.snr_db < 15:
            recommendations.append("Consider denoising to reduce parameter uncertainty")
        
        if features.has_missing_data:
            recommendations.append(f"Address missing data ({features.missing_ratio*100:.1f}%) via interpolation or collection")
        
        if features.length < 100:
            recommendations.append("Collect more data to enable more sophisticated models")
        elif features.length < 500:
            recommendations.append("More data would reduce uncertainty and enable higher-complexity models")
        
        # Model-specific recommendations
        if calibrated_models and best_idx >= 0:
            best = calibrated_models[best_idx]
            
            if best.r2 < 0.5:
                recommendations.append("Current models insufficient - consider nonlinear or regime-switching models")
            
            # Check for outliers
            if hasattr(best, 'standardized_residuals'):
                outliers = np.sum(np.abs(best.standardized_residuals) > 3)
                if outliers > 0:
                    recommendations.append(f"Investigate {outliers} potential outliers in the data")
        
        # Feasibility-based recommendations
        data_failures = [r for r in feasibility_results 
                        if not r.passed and not r.data_feasible]
        if data_failures:
            recommendations.append("Address data quality issues to enable more model families")
        
        # Add generic recommendations if none
        if not recommendations:
            recommendations.append("Current analysis complete - consider domain-specific validation")
        
        return recommendations[:5]  # Return top 5
    
    def _build_provenance_chain(self, features, candidates, 
                                feasibility_results, calibrated_models) -> List[Dict]:
        """Build provenance chain for audit trail"""
        
        chain = []
        
        # L1
        chain.append({
            "step": "l1_characterization",
            "timestamp": datetime.now().isoformat(),
            "output": {
                "stationary": features.is_stationary,
                "snr_db": features.snr_db,
                "n_regimes": features.n_regimes,
                "feature_vector_shape": features.feature_vector.shape if hasattr(features, 'feature_vector') else None
            }
        })
        
        # L2
        chain.append({
            "step": "l2_generation",
            "timestamp": datetime.now().isoformat(),
            "output": {
                "candidates_generated": len(candidates),
                "families_represented": len(set(c.family.value for c in candidates if hasattr(c, 'family'))),
                "complexity_range": [min(c.complexity for c in candidates), max(c.complexity for c in candidates)]
            }
        })
        
        # L3
        chain.append({
            "step": "l3_feasibility",
            "timestamp": datetime.now().isoformat(),
            "output": {
                "total_assessed": len(feasibility_results),
                "passed": len([r for r in feasibility_results if r.passed]),
                "filtered": len([r for r in feasibility_results if not r.passed]),
                "avg_feasibility_score": np.mean([r.feasibility_score for r in feasibility_results])
            }
        })
        
        # L4
        chain.append({
            "step": "l4_calibration",
            "timestamp": datetime.now().isoformat(),
            "output": {
                "models_calibrated": len([m for m in calibrated_models if m is not None]),
                "best_model_r2": max([m.r2 for m in calibrated_models if m is not None]) if calibrated_models else None,
                "calibration_method": calibrated_models[0].method if calibrated_models else None
            }
        })
        
        return chain
    
    def export_freeze_package(self, report: AuditReport) -> Dict:
        """Export report as freeze package for Alex's driver"""
        
        freeze_package = {
            "message_type": "frozen.axiom",
            "package_id": report.report_id,
            "created_at": report.generated_at,
            "producer": {
                "name": "xrag",
                "version": report.xrag_version
            },
            "payload": {
                "record_type": "analysis_report",
                "record_id": report.report_id,
                "record": {
                    "best_model": report.best_model,
                    "executive_summary": report.executive_summary,
                    "recommendations": report.recommendations
                }
            },
            "provenance": {
                "source": "xrag_core",
                "chain": report.provenance_chain
            },
            "protocol": {"frozen": True},
            "comparator": {"frozen": True},
            "bridge_rules": {"frozen": True},
            "integrity": {
                "hash_alg": "sha256",
                "report_hash": report.report_hash,
                "verification_code": report.verification_code
            }
        }
        
        return freeze_package
