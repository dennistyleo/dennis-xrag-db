"""
L3: Feasibility Assessment
Uncompromising filter that throws out any candidate violating physical constraints
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .stage2_generation import Hypothesis

class FeasibilityStatus(Enum):
    """Feasibility assessment result"""
    PASS = "pass"
    FAIL_DATA = "fail_data_quality"
    FAIL_COMPUTATIONAL = "fail_computational"
    FAIL_PHYSICAL = "fail_physical_constraint"
    FAIL_STATISTICAL = "fail_statistical_assumption"
    FAIL_DOMAIN = "fail_domain_mismatch"

@dataclass
class FeasibilityResult:
    """Result of feasibility assessment for a hypothesis"""
    
    hypothesis_name: str
    hypothesis_family: str
    status: FeasibilityStatus
    passed: bool
    rejection_reason: Optional[str]
    feasibility_score: float  # 0-1
    
    # Detailed constraint checks
    constraints_checked: List[str]
    constraints_passed: List[str]
    constraints_failed: List[Dict[str, Any]]  # Each failed constraint with details
    
    # Component feasibility
    computational_feasible: bool
    data_feasible: bool
    statistical_feasible: bool
    physical_feasible: bool
    domain_feasible: bool
    
    # Additional metadata
    warnings: List[str] = None
    suggestions: List[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        d = asdict(self)
        d['status'] = self.status.value
        return d

class DomainConstraints:
    """Domain-specific physical constraints"""
    
    # Domain invariants (physical constants and bounds)
    INVARIANTS = {
        "general": {
            "temperature": [0, 5000],  # Kelvin
            "pressure": [0, 1e9],  # Pa
            "time": [0, 1e18],  # seconds
            "frequency": [1e-6, 1e15],  # Hz
            "energy": [0, 1e12],  # J
            "power": [0, 1e15]  # W
        },
        "thermal": {
            "temperature": [0, 5000],  # Kelvin
            "heat_flux": [0, 1e12],  # W/m²
            "thermal_conductivity": [0.01, 1000],  # W/(m·K)
            "specific_heat": [100, 10000],  # J/(kg·K)
            "thermal_diffusivity": [1e-8, 1e-3]  # m²/s
        },
        "aging": {
            "activation_energy": [0.1, 2.0],  # eV
            "life_hours": [0, 1e8],  # hours
            "temperature": [200, 500],  # Kelvin for accelerated testing
            "stress": [0, 1e9],  # Pa
            "cycles_to_failure": [1, 1e9]  # cycles
        },
        "electrical": {
            "voltage": [-1e6, 1e6],  # V
            "current": [-1e5, 1e5],  # A
            "resistance": [0, 1e9],  # Ω
            "capacitance": [1e-15, 1],  # F
            "inductance": [1e-9, 1],  # H
            "frequency": [0, 1e12]  # Hz
        },
        "mechanical": {
            "stress": [0, 1e12],  # Pa
            "strain": [0, 10],  # dimensionless
            "youngs_modulus": [1e6, 1e12],  # Pa
            "density": [1, 20000],  # kg/m³
            "velocity": [0, 1e5]  # m/s
        },
        "fluid": {
            "pressure": [0, 1e9],  # Pa
            "velocity": [0, 1e4],  # m/s
            "viscosity": [1e-6, 1e3],  # Pa·s
            "reynolds_number": [0, 1e8],  # dimensionless
            "mach_number": [0, 10]  # dimensionless
        },
        "chemical": {
            "concentration": [0, 1e5],  # mol/m³
            "reaction_rate": [1e-12, 1e6],  # mol/(m³·s)
            "diffusion_coefficient": [1e-14, 1e-4],  # m²/s
            "activation_energy": [0.1, 5.0]  # eV
        }
    }
    
    # Statistical assumptions that must hold
    STATISTICAL_ASSUMPTIONS = {
        "iid": "Independent and identically distributed",
        "normality": "Normally distributed residuals",
        "homoscedasticity": "Constant variance",
        "no_autocorrelation": "No autocorrelation in residuals",
        "stationarity": "Weak stationarity",
        "ergodicity": "Ergodic process",
        "mixing": "Mixing condition"
    }

class FeasibilityAssessor:
    """
    L3: Feasibility Assessment Layer
    
    Uncompromising filter that throws out any mathematical candidate
    violating the physical constraints identified in L1.
    
    This is the UNCOMPROMISING FILTER - any violation = reject.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize feasibility assessor
        
        Args:
            strict_mode: If True, any violation leads to rejection.
                        If False, warnings are issued but can pass.
        """
        self.name = "XRAG-L3"
        self.version = "1.0.0"
        self.strict_mode = strict_mode
        self.domain_constraints = DomainConstraints()
        
    def assess(self, 
               hypotheses: List,
               features,
               domain: str = "general") -> List[FeasibilityResult]:
        """
        Assess feasibility of each hypothesis
        
        This is the UNCOMPROMISING FILTER - any violation = reject
        
        Args:
            hypotheses: List of Hypothesis objects from L2
            features: SignalFeatures from L1
            domain: Application domain for domain-specific constraints
            
        Returns:
            List of feasibility results for each hypothesis
        """
        
        results = []
        
        for h in hypotheses:
            result = self._assess_single(h, features, domain)
            results.append(result)
            
            # In strict mode, reject if any violation
            if self.strict_mode and not result.passed:
                print(f"  🚫 Filtered: {h.name} - {result.rejection_reason}")
        
        return results
    
    def _assess_single(self, hypothesis, features, domain: str) -> FeasibilityResult:
        """Assess a single hypothesis"""
        
        constraints_checked = []
        constraints_passed = []
        constraints_failed = []
        warnings = []
        suggestions = []
        
        # === 1. DATA FEASIBILITY ===
        data_feasible = True
        data_checks = self._check_data_feasibility(hypothesis, features)
        
        constraints_checked.extend(data_checks['checked'])
        constraints_passed.extend(data_checks['passed'])
        
        for failure in data_checks['failed']:
            constraints_failed.append({
                'type': 'data',
                'constraint': failure['constraint'],
                'details': failure['details'],
                'severity': 'critical' if failure['critical'] else 'warning'
            })
            if failure['critical']:
                data_feasible = False
            else:
                warnings.append(f"Data warning: {failure['details']}")
        
        # === 2. COMPUTATIONAL FEASIBILITY ===
        computational_feasible = True
        comp_checks = self._check_computational_feasibility(hypothesis, features)
        
        constraints_checked.extend(comp_checks['checked'])
        constraints_passed.extend(comp_checks['passed'])
        
        for failure in comp_checks['failed']:
            constraints_failed.append({
                'type': 'computational',
                'constraint': failure['constraint'],
                'details': failure['details'],
                'severity': 'critical' if failure['critical'] else 'warning'
            })
            if failure['critical']:
                computational_feasible = False
            else:
                warnings.append(f"Computational warning: {failure['details']}")
        
        # === 3. STATISTICAL FEASIBILITY ===
        statistical_feasible = True
        stat_checks = self._check_statistical_feasibility(hypothesis, features)
        
        constraints_checked.extend(stat_checks['checked'])
        constraints_passed.extend(stat_checks['passed'])
        
        for failure in stat_checks['failed']:
            constraints_failed.append({
                'type': 'statistical',
                'constraint': failure['constraint'],
                'details': failure['details'],
                'severity': 'critical' if failure['critical'] else 'warning'
            })
            if failure['critical']:
                statistical_feasible = False
            else:
                warnings.append(f"Statistical warning: {failure['details']}")
        
        # === 4. PHYSICAL FEASIBILITY ===
        physical_feasible = True
        phys_checks = self._check_physical_feasibility(hypothesis, features, domain)
        
        constraints_checked.extend(phys_checks['checked'])
        constraints_passed.extend(phys_checks['passed'])
        
        for failure in phys_checks['failed']:
            constraints_failed.append({
                'type': 'physical',
                'constraint': failure['constraint'],
                'details': failure['details'],
                'severity': 'critical' if failure['critical'] else 'warning'
            })
            if failure['critical']:
                physical_feasible = False
            else:
                warnings.append(f"Physical warning: {failure['details']}")
        
        # === 5. DOMAIN FEASIBILITY ===
        domain_feasible = True
        domain_checks = self._check_domain_feasibility(hypothesis, features, domain)
        
        constraints_checked.extend(domain_checks['checked'])
        constraints_passed.extend(domain_checks['passed'])
        
        for failure in domain_checks['failed']:
            constraints_failed.append({
                'type': 'domain',
                'constraint': failure['constraint'],
                'details': failure['details'],
                'severity': 'critical' if failure['critical'] else 'warning'
            })
            if failure['critical']:
                domain_feasible = False
            else:
                warnings.append(f"Domain warning: {failure['details']}")
        
        # === OVERALL DECISION ===
        passed = (data_feasible and computational_feasible and 
                 statistical_feasible and physical_feasible and domain_feasible)
        
        # Determine status and primary rejection reason
        status = FeasibilityStatus.PASS if passed else FeasibilityStatus.FAIL_DATA
        rejection_reason = None
        
        if not passed:
            # Find first critical failure
            for failure in constraints_failed:
                if failure['severity'] == 'critical':
                    if failure['type'] == 'data':
                        status = FeasibilityStatus.FAIL_DATA
                    elif failure['type'] == 'computational':
                        status = FeasibilityStatus.FAIL_COMPUTATIONAL
                    elif failure['type'] == 'statistical':
                        status = FeasibilityStatus.FAIL_STATISTICAL
                    elif failure['type'] == 'physical':
                        status = FeasibilityStatus.FAIL_PHYSICAL
                    elif failure['type'] == 'domain':
                        status = FeasibilityStatus.FAIL_DOMAIN
                    
                    rejection_reason = f"{failure['type'].upper()}: {failure['details']}"
                    break
        
        # Feasibility score (0-1)
        total_checks = len(constraints_checked)
        passed_checks = len(constraints_passed)
        feasibility_score = passed_checks / max(total_checks, 1)
        
        # Generate suggestions if failed
        if not passed:
            suggestions = self._generate_suggestions(
                hypothesis, features, constraints_failed
            )
        
        return FeasibilityResult(
            hypothesis_name=hypothesis.name,
            hypothesis_family=hypothesis.family.value,
            status=status,
            passed=passed,
            rejection_reason=rejection_reason,
            feasibility_score=feasibility_score,
            constraints_checked=constraints_checked,
            constraints_passed=constraints_passed,
            constraints_failed=constraints_failed,
            computational_feasible=computational_feasible,
            data_feasible=data_feasible,
            statistical_feasible=statistical_feasible,
            physical_feasible=physical_feasible,
            domain_feasible=domain_feasible,
            warnings=warnings if warnings else None,
            suggestions=suggestions if suggestions else None
        )
    
    def _check_data_feasibility(self, hypothesis, features) -> Dict:
        """Check data quality constraints"""
        result = {
            'checked': [],
            'passed': [],
            'failed': []
        }
        
        # Minimum samples check
        min_samples = self._get_min_samples(hypothesis)
        result['checked'].append(f"min_samples:{min_samples}")
        
        if features.length < min_samples:
            result['failed'].append({
                'constraint': 'minimum_samples',
                'details': f"Need ≥{min_samples} samples, have {features.length}",
                'critical': True
            })
        else:
            result['passed'].append(f"min_samples:{min_samples}")
        
        # SNR check
        min_snr = self._get_min_snr(hypothesis)
        result['checked'].append(f"min_snr:{min_snr}")
        
        if features.snr_db < min_snr:
            critical = features.snr_db < min_snr - 10  # More critical if very low SNR
            result['failed'].append({
                'constraint': 'snr',
                'details': f"Need ≥{min_snr}dB SNR, have {features.snr_db:.1f}dB",
                'critical': critical
            })
        else:
            result['passed'].append(f"min_snr:{min_snr}")
        
        # Missing data check
        max_missing = 0.1 if hypothesis.complexity > 3 else 0.2
        result['checked'].append(f"max_missing:{max_missing}")
        
        if features.missing_ratio > max_missing:
            critical = features.missing_ratio > 0.3
            result['failed'].append({
                'constraint': 'missing_data',
                'details': f"Missing ratio {features.missing_ratio:.2f} > {max_missing:.2f}",
                'critical': critical
            })
        else:
            result['passed'].append(f"max_missing:{max_missing}")
        
        # Continuity check
        if "continuous" in hypothesis.assumptions:
            result['checked'].append("continuity")
            if not features.is_continuous:
                critical = len(features.discontinuity_points) > 5
                result['failed'].append({
                    'constraint': 'continuity',
                    'details': f"Signal has {len(features.discontinuity_points)} discontinuities",
                    'critical': critical
                })
            else:
                result['passed'].append("continuity")
        
        return result
    
    def _check_computational_feasibility(self, hypothesis, features) -> Dict:
        """Check computational constraints"""
        result = {
            'checked': [],
            'passed': [],
            'failed': []
        }
        
        # Complexity vs data size
        if hypothesis.computational_cost == "O(n²)":
            result['checked'].append("complexity:O(n²)")
            if features.length > 10000:
                result['failed'].append({
                    'constraint': 'computational_cost',
                    'details': f"O(n²) with n={features.length} > 10000",
                    'critical': True
                })
            else:
                result['passed'].append("complexity:O(n²)")
                
        elif hypothesis.computational_cost == "O(n³)":
            result['checked'].append("complexity:O(n³)")
            if features.length > 2000:
                result['failed'].append({
                    'constraint': 'computational_cost',
                    'details': f"O(n³) with n={features.length} > 2000",
                    'critical': True
                })
            else:
                result['passed'].append("complexity:O(n³)")
        
        # Parameter count vs data size
        n_params = len(hypothesis.parameter_names)
        min_samples_per_param = 10
        required_samples = n_params * min_samples_per_param
        
        result['checked'].append(f"params:{n_params}")
        if features.length < required_samples:
            critical = features.length < required_samples / 2
            result['failed'].append({
                'constraint': 'parameters_vs_samples',
                'details': f"{n_params} parameters need ~{required_samples} samples, have {features.length}",
                'critical': critical
            })
        else:
            result['passed'].append(f"params:{n_params}")
        
        return result
    
    def _check_statistical_feasibility(self, hypothesis, features) -> Dict:
        """Check statistical assumptions"""
        result = {
            'checked': [],
            'passed': [],
            'failed': []
        }
        
        # Stationarity check
        if "stationary" in hypothesis.assumptions:
            result['checked'].append("stationarity")
            if not features.is_stationary:
                critical = features.stationarity_pvalue < 0.01
                result['failed'].append({
                    'constraint': 'stationarity',
                    'details': f"Signal is not stationary (p={features.stationarity_pvalue:.3f})",
                    'critical': critical
                })
            else:
                result['passed'].append("stationarity")
        
        # IID assumption check (simplified)
        if "iid" in hypothesis.assumptions:
            result['checked'].append("iid")
            
            # Check autocorrelation at lag 1
            if features.length > 10:
                # Simple autocorrelation approximation using feature vector
                if len(features.feature_vector) > 2:
                    acf_lag1 = np.corrcoef(features.feature_vector[:-1], 
                                           features.feature_vector[1:])[0,1]
                    if abs(acf_lag1) > 0.5:
                        result['failed'].append({
                            'constraint': 'iid',
                            'details': f"Strong autocorrelation (ρ={acf_lag1:.2f})",
                            'critical': False  # Warning, not critical
                        })
                    else:
                        result['passed'].append("iid")
        
        # Normality check (simplified)
        if "normality" in hypothesis.assumptions:
            result['checked'].append("normality")
            
            if abs(features.skewness) > 2 or abs(features.kurtosis) > 7:
                result['failed'].append({
                    'constraint': 'normality',
                    'details': f"Non-normal: skew={features.skewness:.2f}, kurt={features.kurtosis:.2f}",
                    'critical': False
                })
            else:
                result['passed'].append("normality")
        
        return result
    
    def _check_physical_feasibility(self, hypothesis, features, domain) -> Dict:
        """Check physical constraints"""
        result = {
            'checked': [],
            'passed': [],
            'failed': []
        }
        
        # Get domain invariants
        invariants = self.domain_constraints.INVARIANTS.get(
            domain, self.domain_constraints.INVARIANTS["general"]
        )
        
        # Check parameter bounds against physical limits
        for param_name, bounds in hypothesis.parameter_bounds.items():
            if param_name in invariants:
                result['checked'].append(f"physical:{param_name}")
                
                phys_bounds = invariants[param_name]
                
                # Check if hypothesis bounds are within physical bounds
                if bounds[0] < phys_bounds[0] or bounds[1] > phys_bounds[1]:
                    result['failed'].append({
                        'constraint': f'physical_range_{param_name}',
                        'details': f"Parameter {param_name} bounds [{bounds[0]}, {bounds[1]}] "
                                  f"outside physical [{phys_bounds[0]}, {phys_bounds[1]}]",
                        'critical': True
                    })
                else:
                    result['passed'].append(f"physical:{param_name}")
        
        # Check for conservation laws if applicable
        if hypothesis.family.value in ["pde", "sde"]:
            result['checked'].append("conservation")
            # Simplified conservation check
            if np.sum(features.feature_vector) < 0:
                result['failed'].append({
                    'constraint': 'conservation',
                    'details': "Potential violation of conservation law",
                    'critical': False
                })
            else:
                result['passed'].append("conservation")
        
        return result
    
    def _check_domain_feasibility(self, hypothesis, features, domain) -> Dict:
        """Check domain-specific feasibility"""
        result = {
            'checked': [],
            'passed': [],
            'failed': []
        }
        
        # Check if hypothesis is appropriate for domain
        domain_keywords = {
            "thermal": ["heat", "temperature", "thermal", "cooling", "fourier"],
            "aging": ["aging", "degradation", "fatigue", "arrhenius", "paris"],
            "electrical": ["voltage", "current", "resistance", "capacitance", "fourier"],
            "mechanical": ["stress", "strain", "displacement", "vibration"],
            "fluid": ["flow", "pressure", "velocity", "viscosity"],
            "chemical": ["concentration", "reaction", "diffusion", "arrhenius"]
        }
        
        if domain in domain_keywords:
            result['checked'].append(f"domain:{domain}")
            
            # Check if hypothesis tags match domain
            hypothesis_text = f"{hypothesis.name} {hypothesis.formulation} {' '.join(hypothesis.tags)}".lower()
            
            matches = any(kw in hypothesis_text for kw in domain_keywords[domain])
            
            if not matches:
                result['failed'].append({
                    'constraint': f'domain_relevance_{domain}',
                    'details': f"Hypothesis may not be relevant for {domain} domain",
                    'critical': False  # Warning only
                })
            else:
                result['passed'].append(f"domain:{domain}")
        
        return result
    
    def _get_min_samples(self, hypothesis) -> int:
        """Get minimum samples required for hypothesis"""
        base_samples = {
            "O(1)": 10,
            "O(n)": 30,
            "O(n log n)": 50,
            "O(n²)": 100,
            "O(n³)": 200
        }
        
        cost = hypothesis.computational_cost
        min_samples = base_samples.get(cost, 30)
        
        # Adjust for complexity
        min_samples *= (hypothesis.complexity // 2 + 1)
        
        return min_samples
    
    def _get_min_snr(self, hypothesis) -> float:
        """Get minimum SNR required for hypothesis"""
        base_snr = {
            1: 0,    # Very simple models can handle low SNR
            2: 3,
            3: 6,
            4: 10,
            5: 15,
            6: 20,
            7: 25,
            8: 30,
            9: 35,
            10: 40
        }
        
        return base_snr.get(hypothesis.complexity, 10)
    
    def _generate_suggestions(self, hypothesis, features, failed_constraints) -> List[str]:
        """Generate suggestions for improving feasibility"""
        suggestions = []
        
        for failure in failed_constraints:
            if failure['type'] == 'data':
                if 'minimum_samples' in failure['constraint']:
                    suggestions.append(f"Collect more data (need {failure['details'].split('≥')[1].split(' ')[0]})")
                elif 'snr' in failure['constraint']:
                    suggestions.append("Improve signal quality or apply denoising")
                elif 'missing_data' in failure['constraint']:
                    suggestions.append("Address missing data through imputation")
                    
            elif failure['type'] == 'computational':
                if 'computational_cost' in failure['constraint']:
                    suggestions.append("Reduce data size or use simpler model")
                elif 'parameters_vs_samples' in failure['constraint']:
                    suggestions.append("Use model with fewer parameters")
                    
            elif failure['type'] == 'statistical':
                if 'stationarity' in failure['constraint']:
                    suggestions.append("Apply differencing or detrending")
                elif 'iid' in failure['constraint']:
                    suggestions.append("Consider time series model with correlation")
                    
            elif failure['type'] == 'physical':
                if 'physical_range' in failure['constraint']:
                    param = failure['constraint'].replace('physical_range_', '')
                    suggestions.append(f"Adjust {param} bounds to physical range")
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def get_feasible_hypotheses(self, 
                               hypotheses: List,
                               features,
                               domain: str = "general") -> List[Tuple[Hypothesis, FeasibilityResult]]:
        """Get only feasible hypotheses with their results"""
        results = self.assess(hypotheses, features, domain)
        
        feasible = []
        for h, r in zip(hypotheses, results):
            if r.passed:
                feasible.append((h, r))
        
        return feasible
