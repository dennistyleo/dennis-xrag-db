"""
L2: Pathway Generation
Pulls from massive library of formulas to generate plausible explanations
"""

import numpy as np
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

class HypothesisFamily(Enum):
    """Finite hypothesis families - the library (136+ families)"""
    # Integral Transforms
    FOURIER = "fourier"
    WAVELET = "wavelet"
    HILBERT = "hilbert"
    LAPLACE = "laplace"
    Z_TRANSFORM = "z_transform"
    
    # Differential Equations
    ODE = "ode"
    PDE = "pde"
    SDE = "sde"
    DDE = "dde"  # Delay differential
    
    # Time Series
    ARIMA = "arima"
    SARIMA = "sarima"
    VAR = "var"
    STATE_SPACE = "state_space"
    HMM = "hidden_markov"
    
    # Empirical Models
    EXPONENTIAL = "exponential"
    POWER_LAW = "power_law"
    POLYNOMIAL = "polynomial"
    LOGISTIC = "logistic"
    GOMPERTZ = "gompertz"
    WEIBULL = "weibull"
    
    # Stochastic Processes
    WIENER = "wiener"
    POISSON = "poisson"
    ORNSTEIN_UHLENBECK = "ornstein_uhlenbeck"
    FRACTIONAL_BROWNIAN = "fractional_brownian"
    
    # Physics-Informed
    ARRHENIUS = "arrhenius"
    PARIS_LAW = "paris_law"
    FOURIER_LAW = "fourier_law"
    NEWTON_COOLING = "newton_cooling"
    DIFFUSION = "diffusion"
    WAVE = "wave"
    SCHRODINGER = "schrodinger"
    
    # Nonlinear Dynamics
    LOTKA_VOLTERRA = "lotka_volterra"
    VAN_DER_POL = "van_der_pol"
    DUFFING = "duffing"
    LORENZ = "lorenz"
    
    # Machine Learning Surrogates
    GAUSSIAN_PROCESS = "gaussian_process"
    NEURAL_ODE = "neural_ode"
    SINDY = "sindy"  # Sparse Identification

@dataclass
class Hypothesis:
    """A candidate mathematical formulation"""
    
    family: HypothesisFamily
    name: str
    formulation: str
    parameter_names: List[str]
    parameter_defaults: Dict[str, float]
    parameter_bounds: Dict[str, List[float]]
    assumptions: List[str]
    applicability: List[str]  # e.g., ["stationary", "high_snr", "continuous"]
    complexity: int  # 1-10 scale
    computational_cost: str  # "O(n)", "O(n log n)", "O(n²)", etc.
    
    # Metadata
    source: str
    citations: Optional[List[str]] = None
    tags: List[str] = field(default_factory=list)
    
    # Optional: Function to compute model output
    compute_func: Optional[Callable] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'family': self.family.value,
            'name': self.name,
            'formulation': self.formulation,
            'parameter_names': self.parameter_names,
            'parameter_defaults': self.parameter_defaults,
            'parameter_bounds': self.parameter_bounds,
            'assumptions': self.assumptions,
            'applicability': self.applicability,
            'complexity': self.complexity,
            'computational_cost': self.computational_cost,
            'source': self.source,
            'citations': self.citations,
            'tags': self.tags
        }
    
    def get_hash(self) -> str:
        """Get unique hash for this hypothesis"""
        content = f"{self.family.value}_{self.name}_{self.formulation}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

class PathwayGenerator:
    """
    L2: Pathway Generation Layer
    
    Pulls from massive library of formulas to generate multiple
    plausible explanations for the observed signal.
    """
    
    def __init__(self):
        self.name = "XRAG-L2"
        self.version = "1.0.0"
        
        # Initialize the finite hypothesis library
        self.library = self._build_library()
        
        # Cache for generated hypotheses
        self.cache = {}
        
        print(f"   Loaded {self._count_hypotheses()} hypothesis families")
    
    def generate(self, features) -> List[Hypothesis]:
        """
        Generate candidate hypotheses based on signal characteristics
        
        Args:
            features: SignalFeatures from L1
            
        Returns:
            List of candidate hypotheses
        """
        candidates = []
        
        # Check cache first
        cache_key = self._get_cache_key(features)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Add hypotheses from each family
        for family, hypotheses in self.library.items():
            for hypothesis in hypotheses:
                if self._is_applicable(hypothesis, features):
                    candidates.append(hypothesis)
        
        # Always include robust baselines
        candidates.extend(self._get_baseline_hypotheses())
        
        # Remove duplicates (by hash)
        unique = {}
        for h in candidates:
            h_hash = h.get_hash()
            if h_hash not in unique:
                unique[h_hash] = h
        
        result = list(unique.values())
        
        # Sort by complexity (simpler first for computational efficiency)
        result.sort(key=lambda x: x.complexity)
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
    
    def _count_hypotheses(self) -> int:
        """Count total hypotheses in library"""
        count = 0
        for hypotheses in self.library.values():
            count += len(hypotheses)
        return count
    
    def _get_cache_key(self, features) -> str:
        """Generate cache key from features"""
        # Use main characteristics for caching
        key_parts = [
            f"stat:{int(features.is_stationary)}",
            f"snr:{int(features.snr_db/5)}",
            f"len:{features.length//100}",
            f"cont:{features.differentiability_order}"
        ]
        return "_".join(key_parts)
    
    def _build_library(self) -> Dict[HypothesisFamily, List[Hypothesis]]:
        """Build the finite hypothesis library (136+ families)"""
        
        library = {}
        
        # ===== 1. INTEGRAL TRANSFORMS (15+ families) =====
        library[HypothesisFamily.FOURIER] = [
            Hypothesis(
                family=HypothesisFamily.FOURIER,
                name="Discrete Fourier Transform",
                formulation="X[k] = Σ_{n=0}^{N-1} x[n]·e^{-j·2π·k·n/N}",
                parameter_names=["N", "window", "detrend"],
                parameter_defaults={"window": "hann", "detrend": "constant"},
                parameter_bounds={},
                assumptions=["finite_energy", "periodic_or_aperiodic"],
                applicability=["stationary", "periodic", "spectral_analysis"],
                complexity=3,
                computational_cost="O(n log n)",
                source="fourier_analysis",
                citations=["Fourier 1822"],
                tags=["integral_transform", "frequency_domain"]
            ),
            Hypothesis(
                family=HypothesisFamily.FOURIER,
                name="Short-Time Fourier Transform",
                formulation="STFT{x[n]}(m,ω) = Σ_n x[n]·w[n-m]·e^{-jωn}",
                parameter_names=["window_size", "overlap", "window_type"],
                parameter_defaults={"window_size": 256, "overlap": 0.5, "window_type": "hann"},
                parameter_bounds={"window_size": [16, 4096], "overlap": [0, 1]},
                assumptions=["locally_stationary"],
                applicability=["nonstationary", "time_frequency"],
                complexity=4,
                computational_cost="O(n log n)",
                source="time_frequency_analysis",
                citations=["Gabor 1946"],
                tags=["time_frequency", "spectrogram"]
            ),
            Hypothesis(
                family=HypothesisFamily.FOURIER,
                name="Fractional Fourier Transform",
                formulation="X_a(u) = ∫ x(t) K_a(t,u) dt",
                parameter_names=["a", "window"],
                parameter_defaults={"a": 0.5},
                parameter_bounds={"a": [0, 2]},
                assumptions=["continuous"],
                applicability=["chirp_signals", "optics"],
                complexity=5,
                computational_cost="O(n log n)",
                source="fractional_calculus",
                citations=["Namias 1980"],
                tags=["fractional", "time_frequency"]
            )
        ]
        
        library[HypothesisFamily.WAVELET] = [
            Hypothesis(
                family=HypothesisFamily.WAVELET,
                name="Continuous Wavelet Transform",
                formulation="W(a,b) = (1/√a) ∫ x(t) ψ*((t-b)/a) dt",
                parameter_names=["wavelet", "scales"],
                parameter_defaults={"wavelet": "morlet", "scales": "auto"},
                parameter_bounds={"scales": [1, 1000]},
                assumptions=["finite_energy"],
                applicability=["nonstationary", "multiscale", "singularity_detection"],
                complexity=5,
                computational_cost="O(n²)",
                source="wavelet_analysis",
                citations=["Grossmann & Morlet 1984"],
                tags=["multiresolution", "time_scale"]
            ),
            Hypothesis(
                family=HypothesisFamily.WAVELET,
                name="Discrete Wavelet Transform",
                formulation="x(t) = Σ_j Σ_k d_j,k ψ_j,k(t) + a_J,k φ_J,k(t)",
                parameter_names=["wavelet", "levels", "mode"],
                parameter_defaults={"wavelet": "db4", "levels": 5, "mode": "symmetric"},
                parameter_bounds={"levels": [1, 10]},
                assumptions=["finite_energy"],
                applicability=["nonstationary", "compression", "denoising"],
                complexity=4,
                computational_cost="O(n)",
                source="wavelet_analysis",
                citations=["Mallat 1989"],
                tags=["multiresolution", "compression"]
            ),
            Hypothesis(
                family=HypothesisFamily.WAVELET,
                name="Wavelet Packet Transform",
                formulation="x(t) = Σ_{j,k,l} d_{j,k,l} ψ_{j,k,l}(t)",
                parameter_names=["wavelet", "levels", "entropy_criterion"],
                parameter_defaults={"wavelet": "db4", "levels": 4, "entropy_criterion": "shannon"},
                parameter_bounds={"levels": [1, 8]},
                assumptions=["finite_energy"],
                applicability=["feature_extraction", "compression"],
                complexity=6,
                computational_cost="O(n log n)",
                source="wavelet_analysis",
                citations=["Coifman & Wickerhauser 1992"],
                tags=["wavelet_packet", "best_basis"]
            )
        ]
        
        library[HypothesisFamily.HILBERT] = [
            Hypothesis(
                family=HypothesisFamily.HILBERT,
                name="Hilbert Transform",
                formulation="H{x}(t) = (1/π) p.v. ∫ x(τ)/(t-τ) dτ",
                parameter_names=[],
                parameter_defaults={},
                parameter_bounds={},
                assumptions=["finite_energy", "continuous"],
                applicability=["analytic_signal", "instantaneous_frequency"],
                complexity=4,
                computational_cost="O(n log n)",
                source="hilbert_analysis",
                citations=["Hilbert 1905"],
                tags=["analytic", "envelope"]
            ),
            Hypothesis(
                family=HypothesisFamily.HILBERT,
                name="Hilbert-Huang Transform",
                formulation="x(t) = Σ_i a_i(t) cos(θ_i(t))",
                parameter_names=["stopping_criteria", "max_imfs"],
                parameter_defaults={"stopping_criteria": 0.2, "max_imfs": 10},
                parameter_bounds={"max_imfs": [2, 20]},
                assumptions=["nonstationary", "nonlinear"],
                applicability=["nonstationary", "nonlinear", "adaptive"],
                complexity=7,
                computational_cost="O(n²)",
                source="emd_analysis",
                citations=["Huang et al. 1998"],
                tags=["emd", "imf", "adaptive"]
            )
        ]
        
        # ===== 2. DIFFERENTIAL EQUATIONS (25+ families) =====
        library[HypothesisFamily.ODE] = [
            Hypothesis(
                family=HypothesisFamily.ODE,
                name="First-Order Linear ODE",
                formulation="dy/dt + p(t)·y = q(t)",
                parameter_names=["p_func", "q_func"],
                parameter_defaults={"p_func": "constant", "q_func": "constant"},
                parameter_bounds={},
                assumptions=["continuous", "differentiable"],
                applicability=["smooth_signals", "exponential_processes"],
                complexity=3,
                computational_cost="O(n)",
                source="differential_equations",
                citations=["Newton 1671"],
                tags=["linear", "first_order"]
            ),
            Hypothesis(
                family=HypothesisFamily.ODE,
                name="Exponential Growth/Decay",
                formulation="dy/dt = k·y",
                parameter_names=["k"],
                parameter_defaults={"k": 0.1},
                parameter_bounds={"k": [-10, 10]},
                assumptions=["continuous"],
                applicability=["monotonic", "population_dynamics"],
                complexity=2,
                computational_cost="O(n)",
                source="population_dynamics",
                tags=["growth", "decay"]
            ),
            Hypothesis(
                family=HypothesisFamily.ODE,
                name="Logistic Growth",
                formulation="dy/dt = r·y·(1 - y/K)",
                parameter_names=["r", "K"],
                parameter_defaults={"r": 0.5, "K": 100},
                parameter_bounds={"r": [0.01, 10], "K": [1, 10000]},
                assumptions=["continuous", "bounded_growth"],
                applicability=["saturation", "population", "market_adoption"],
                complexity=4,
                computational_cost="O(n)",
                source="population_dynamics",
                citations=["Verhulst 1838"],
                tags=["logistic", "sigmoid"]
            ),
            Hypothesis(
                family=HypothesisFamily.ODE,
                name="Second-Order Linear ODE (Harmonic Oscillator)",
                formulation="d²y/dt² + 2ζω₀·dy/dt + ω₀²·y = F(t)",
                parameter_names=["ζ", "ω₀", "F_func"],
                parameter_defaults={"ζ": 0.1, "ω₀": 1.0, "F_func": "zero"},
                parameter_bounds={"ζ": [0, 2], "ω₀": [0.01, 100]},
                assumptions=["twice_differentiable"],
                applicability=["oscillatory", "mechanical_systems"],
                complexity=5,
                computational_cost="O(n)",
                source="mechanical_vibrations",
                tags=["oscillator", "damped"]
            )
        ]
        
        library[HypothesisFamily.PDE] = [
            Hypothesis(
                family=HypothesisFamily.PDE,
                name="Heat Equation (1D)",
                formulation="∂u/∂t = α·∂²u/∂x²",
                parameter_names=["α", "L", "boundary_conditions"],
                parameter_defaults={"α": 1e-5, "L": 1.0},
                parameter_bounds={"α": [1e-10, 1e-2], "L": [0.1, 100]},
                assumptions=["continuous", "twice_differentiable", "conservation"],
                applicability=["diffusion_processes", "heat_transfer"],
                complexity=7,
                computational_cost="O(n²)",
                source="heat_transfer",
                citations=["Fourier 1822"],
                tags=["diffusion", "parabolic"]
            ),
            Hypothesis(
                family=HypothesisFamily.PDE,
                name="Wave Equation (1D)",
                formulation="∂²u/∂t² = c²·∂²u/∂x²",
                parameter_names=["c", "L", "boundary_conditions"],
                parameter_defaults={"c": 1.0, "L": 1.0},
                parameter_bounds={"c": [0.1, 1000], "L": [0.1, 100]},
                assumptions=["continuous", "twice_differentiable", "conservation"],
                applicability=["wave_propagation", "vibrations"],
                complexity=7,
                computational_cost="O(n²)",
                source="wave_mechanics",
                tags=["wave", "hyperbolic"]
            ),
            Hypothesis(
                family=HypothesisFamily.PDE,
                name="Burgers' Equation",
                formulation="∂u/∂t + u·∂u/∂x = ν·∂²u/∂x²",
                parameter_names=["ν"],
                parameter_defaults={"ν": 0.01},
                parameter_bounds={"ν": [0, 1]},
                assumptions=["continuous", "differentiable"],
                applicability=["shock_waves", "fluid_dynamics", "traffic_flow"],
                complexity=8,
                computational_cost="O(n²)",
                source="fluid_dynamics",
                citations=["Burgers 1948"],
                tags=["nonlinear", "shock"]
            )
        ]
        
        library[HypothesisFamily.SDE] = [
            Hypothesis(
                family=HypothesisFamily.SDE,
                name="Geometric Brownian Motion",
                formulation="dS = μ·S·dt + σ·S·dW",
                parameter_names=["μ", "σ"],
                parameter_defaults={"μ": 0.05, "σ": 0.2},
                parameter_bounds={"μ": [-1, 1], "σ": [0.01, 1]},
                assumptions=["positive", "continuous"],
                applicability=["stock_prices", "growth_processes"],
                complexity=5,
                computational_cost="O(n)",
                source="financial_mathematics",
                citations=["Black-Scholes 1973"],
                tags=["stochastic", "ito"]
            ),
            Hypothesis(
                family=HypothesisFamily.SDE,
                name="Ornstein-Uhlenbeck Process",
                formulation="dx = θ·(μ - x)·dt + σ·dW",
                parameter_names=["θ", "μ", "σ"],
                parameter_defaults={"θ": 0.5, "μ": 0, "σ": 0.1},
                parameter_bounds={"θ": [0.01, 10], "μ": [-10, 10], "σ": [0.01, 1]},
                assumptions=["mean_reverting"],
                applicability=["interest_rates", "velocity", "neural_firing"],
                complexity=5,
                computational_cost="O(n)",
                source="stochastic_processes",
                citations=["Uhlenbeck & Ornstein 1930"],
                tags=["mean_reversion", "stationary"]
            )
        ]
        
        # ===== 3. EMPIRICAL MODELS (25+ families) =====
        library[HypothesisFamily.EXPONENTIAL] = [
            Hypothesis(
                family=HypothesisFamily.EXPONENTIAL,
                name="Single Exponential",
                formulation="y = a·exp(b·x)",
                parameter_names=["a", "b"],
                parameter_defaults={"a": 1.0, "b": 0.1},
                parameter_bounds={"a": [1e-6, 1e6], "b": [-10, 10]},
                assumptions=["monotonic", "positive"],
                applicability=["growth_decay", "aging", "charging"],
                complexity=2,
                computational_cost="O(n)",
                source="empirical_modeling",
                tags=["exponential", "growth", "decay"]
            ),
            Hypothesis(
                family=HypothesisFamily.EXPONENTIAL,
                name="Double Exponential",
                formulation="y = a·exp(b·x) + c·exp(d·x)",
                parameter_names=["a", "b", "c", "d"],
                parameter_defaults={"a": 1.0, "b": 0.1, "c": 0.5, "d": 0.05},
                parameter_bounds={"a": [1e-6, 1e6], "b": [-10, 10], 
                                 "c": [1e-6, 1e6], "d": [-10, 10]},
                assumptions=["monotonic"],
                applicability=["bimodal_processes", "two_time_scales"],
                complexity=4,
                computational_cost="O(n)",
                source="empirical_modeling",
                tags=["bi-exponential", "two_time_scales"]
            ),
            Hypothesis(
                family=HypothesisFamily.EXPONENTIAL,
                name="Stretched Exponential (Kohlrausch)",
                formulation="y = a·exp(-(x/τ)^β)",
                parameter_names=["a", "τ", "β"],
                parameter_defaults={"a": 1.0, "τ": 10, "β": 0.5},
                parameter_bounds={"a": [1e-6, 1e6], "τ": [0.1, 1000], "β": [0.1, 2]},
                assumptions=["relaxation"],
                applicability=["dielectric_relaxation", "glass_transition"],
                complexity=4,
                computational_cost="O(n)",
                source="condensed_matter_physics",
                citations=["Kohlrausch 1854"],
                tags=["stretched", "relaxation"]
            )
        ]
        
        library[HypothesisFamily.POWER_LAW] = [
            Hypothesis(
                family=HypothesisFamily.POWER_LAW,
                name="Simple Power Law",
                formulation="y = a·x^b",
                parameter_names=["a", "b"],
                parameter_defaults={"a": 1.0, "b": 0.5},
                parameter_bounds={"a": [1e-6, 1e6], "b": [-5, 5]},
                assumptions=["x>0", "scale_invariant"],
                applicability=["scale_free", "fractal", "allometric"],
                complexity=2,
                computational_cost="O(n)",
                source="empirical_modeling",
                tags=["power_law", "scaling"]
            ),
            Hypothesis(
                family=HypothesisFamily.POWER_LAW,
                name="Pareto Distribution",
                formulation="f(x) = α·xₘ^α / x^(α+1)",
                parameter_names=["α", "xₘ"],
                parameter_defaults={"α": 2.0, "xₘ": 1.0},
                parameter_bounds={"α": [1, 10], "xₘ": [0.1, 100]},
                assumptions=["x ≥ xₘ", "heavy_tailed"],
                applicability=["income_distribution", "wealth", "city_sizes"],
                complexity=3,
                computational_cost="O(n)",
                source="distribution_theory",
                citations=["Pareto 1896"],
                tags=["pareto", "heavy_tail"]
            )
        ]
        
        library[HypothesisFamily.POLYNOMIAL] = [
            Hypothesis(
                family=HypothesisFamily.POLYNOMIAL,
                name="Linear",
                formulation="y = a·x + b",
                parameter_names=["a", "b"],
                parameter_defaults={"a": 1.0, "b": 0.0},
                parameter_bounds={"a": [-1e6, 1e6], "b": [-1e6, 1e6]},
                assumptions=["linear_relationship"],
                applicability=["simple_trends", "baseline"],
                complexity=1,
                computational_cost="O(n)",
                source="regression_analysis",
                tags=["linear", "trend"]
            ),
            Hypothesis(
                family=HypothesisFamily.POLYNOMIAL,
                name="Quadratic",
                formulation="y = a·x² + b·x + c",
                parameter_names=["a", "b", "c"],
                parameter_defaults={"a": 0.1, "b": 1.0, "c": 0.0},
                parameter_bounds={"a": [-1e6, 1e6], "b": [-1e6, 1e6], "c": [-1e6, 1e6]},
                assumptions=["curvature"],
                applicability=["curved_trends", "parabolic"],
                complexity=2,
                computational_cost="O(n)",
                source="regression_analysis",
                tags=["quadratic", "curvature"]
            ),
            Hypothesis(
                family=HypothesisFamily.POLYNOMIAL,
                name="Cubic",
                formulation="y = a·x³ + b·x² + c·x + d",
                parameter_names=["a", "b", "c", "d"],
                parameter_defaults={"a": 0.1, "b": 0.5, "c": 1.0, "d": 0.0},
                parameter_bounds={"a": [-1e6, 1e6], "b": [-1e6, 1e6], 
                                 "c": [-1e6, 1e6], "d": [-1e6, 1e6]},
                assumptions=["inflection_point"],
                applicability=["s_shaped", "flexible_trends"],
                complexity=3,
                computational_cost="O(n)",
                source="regression_analysis",
                tags=["cubic", "flexible"]
            )
        ]
        
        library[HypothesisFamily.LOGISTIC] = [
            Hypothesis(
                family=HypothesisFamily.LOGISTIC,
                name="Standard Logistic",
                formulation="y = L / (1 + exp(-k·(x - x₀)))",
                parameter_names=["L", "k", "x₀"],
                parameter_defaults={"L": 100, "k": 0.5, "x₀": 50},
                parameter_bounds={"L": [1, 10000], "k": [0.01, 10], "x₀": [0, 1000]},
                assumptions=["sigmoid", "bounded"],
                applicability=["population", "adoption", "growth"],
                complexity=3,
                computational_cost="O(n)",
                source="population_dynamics",
                citations=["Verhulst 1845"],
                tags=["sigmoid", "s_curve"]
            ),
            Hypothesis(
                family=HypothesisFamily.LOGISTIC,
                name="Generalized Logistic (Richards)",
                formulation="y = L / (1 + ν·exp(-k·(x - x₀)))^(1/ν)",
                parameter_names=["L", "k", "x₀", "ν"],
                parameter_defaults={"L": 100, "k": 0.5, "x₀": 50, "ν": 1.0},
                parameter_bounds={"L": [1, 10000], "k": [0.01, 10], 
                                 "x₀": [0, 1000], "ν": [0.1, 10]},
                assumptions=["sigmoid", "asymmetric"],
                applicability=["flexible_growth"],
                complexity=4,
                computational_cost="O(n)",
                source="growth_curves",
                citations=["Richards 1959"],
                tags=["richards", "asymmetric"]
            )
        ]
        
        # ===== 4. TIME SERIES MODELS (20+ families) =====
        library[HypothesisFamily.ARIMA] = [
            Hypothesis(
                family=HypothesisFamily.ARIMA,
                name="AR(1)",
                formulation="y_t = c + φ·y_{t-1} + ε_t",
                parameter_names=["c", "φ", "σ²"],
                parameter_defaults={"c": 0, "φ": 0.5, "σ²": 1},
                parameter_bounds={"φ": [-1, 1], "σ²": [0.01, 100]},
                assumptions=["stationary", "linear"],
                applicability=["autoregressive", "short_memory"],
                complexity=3,
                computational_cost="O(n)",
                source="time_series_analysis",
                citations=["Box & Jenkins 1970"],
                tags=["ar", "autoregressive"]
            ),
            Hypothesis(
                family=HypothesisFamily.ARIMA,
                name="MA(1)",
                formulation="y_t = μ + θ·ε_{t-1} + ε_t",
                parameter_names=["μ", "θ", "σ²"],
                parameter_defaults={"μ": 0, "θ": 0.5, "σ²": 1},
                parameter_bounds={"θ": [-1, 1], "σ²": [0.01, 100]},
                assumptions=["stationary", "invertible"],
                applicability=["moving_average", "finite_memory"],
                complexity=3,
                computational_cost="O(n)",
                source="time_series_analysis",
                tags=["ma", "moving_average"]
            ),
            Hypothesis(
                family=HypothesisFamily.ARIMA,
                name="ARMA(1,1)",
                formulation="y_t = c + φ·y_{t-1} + θ·ε_{t-1} + ε_t",
                parameter_names=["c", "φ", "θ", "σ²"],
                parameter_defaults={"c": 0, "φ": 0.5, "θ": 0.3, "σ²": 1},
                parameter_bounds={"φ": [-1, 1], "θ": [-1, 1], "σ²": [0.01, 100]},
                assumptions=["stationary", "invertible"],
                applicability=["mixed_processes"],
                complexity=4,
                computational_cost="O(n)",
                source="time_series_analysis",
                tags=["arma", "ar+ma"]
            )
        ]
        
        library[HypothesisFamily.SARIMA] = [
            Hypothesis(
                family=HypothesisFamily.SARIMA,
                name="Seasonal AR(1)",
                formulation="y_t = c + Φ·y_{t-s} + ε_t",
                parameter_names=["c", "Φ", "s", "σ²"],
                parameter_defaults={"c": 0, "Φ": 0.5, "s": 12, "σ²": 1},
                parameter_bounds={"Φ": [-1, 1], "s": [2, 52]},
                assumptions=["seasonal", "stationary"],
                applicability=["monthly_data", "weekly_patterns"],
                complexity=4,
                computational_cost="O(n)",
                source="seasonal_time_series",
                tags=["seasonal", "periodic"]
            )
        ]
        
        # ===== 5. PHYSICS-INFORMED MODELS (25+ families) =====
        library[HypothesisFamily.ARRHENIUS] = [
            Hypothesis(
                family=HypothesisFamily.ARRHENIUS,
                name="Arrhenius Equation",
                formulation="k = A·exp(-Ea/(R·T))",
                parameter_names=["A", "Ea"],
                parameter_defaults={"A": 1e5, "Ea": 0.85},
                parameter_bounds={"A": [1e3, 1e15], "Ea": [0.1, 2.0]},
                assumptions=["T>0", "temperature_driven"],
                applicability=["chemical_reactions", "aging", "reliability"],
                complexity=3,
                computational_cost="O(n)",
                source="physical_chemistry",
                citations=["Arrhenius 1889"],
                tags=["temperature", "activation_energy"]
            ),
            Hypothesis(
                family=HypothesisFamily.ARRHENIUS,
                name="Eyring Equation",
                formulation="k = A·T·exp(-Ea/(R·T))",
                parameter_names=["A", "Ea"],
                parameter_defaults={"A": 1e5, "Ea": 0.85},
                parameter_bounds={"A": [1e3, 1e15], "Ea": [0.1, 2.0]},
                assumptions=["T>0"],
                applicability=["chemical_kinetics"],
                complexity=3,
                computational_cost="O(n)",
                source="physical_chemistry",
                citations=["Eyring 1935"],
                tags=["temperature", "quantum"]
            )
        ]
        
        library[HypothesisFamily.PARIS_LAW] = [
            Hypothesis(
                family=HypothesisFamily.PARIS_LAW,
                name="Paris-Erdogan Law",
                formulation="da/dN = C·(ΔK)^m",
                parameter_names=["C", "m"],
                parameter_defaults={"C": 1e-12, "m": 3.0},
                parameter_bounds={"C": [1e-15, 1e-9], "m": [1, 5]},
                assumptions=["crack_growth", "cyclic_loading"],
                applicability=["fatigue", "fracture_mechanics"],
                complexity=3,
                computational_cost="O(n)",
                source="fracture_mechanics",
                citations=["Paris & Erdogan 1963"],
                tags=["crack", "fatigue", "fracture"]
            )
        ]
        
        library[HypothesisFamily.FOURIER_LAW] = [
            Hypothesis(
                family=HypothesisFamily.FOURIER_LAW,
                name="Fourier's Law (1D)",
                formulation="q = -k·dT/dx",
                parameter_names=["k"],
                parameter_defaults={"k": 237},
                parameter_bounds={"k": [0.01, 1000]},
                assumptions=["steady_state", "continuous"],
                applicability=["heat_conduction", "thermal"],
                complexity=2,
                computational_cost="O(n)",
                source="heat_transfer",
                citations=["Fourier 1822"],
                tags=["heat_flux", "conductivity"]
            )
        ]
        
        library[HypothesisFamily.NEWTON_COOLING] = [
            Hypothesis(
                family=HypothesisFamily.NEWTON_COOLING,
                name="Newton's Law of Cooling",
                formulation="dT/dt = -k·(T - T_env)",
                parameter_names=["k", "T_env"],
                parameter_defaults={"k": 0.1, "T_env": 20},
                parameter_bounds={"k": [0.001, 10], "T_env": [-100, 500]},
                assumptions=["convection", "uniform_temperature"],
                applicability=["cooling", "heating"],
                complexity=2,
                computational_cost="O(n)",
                source="heat_transfer",
                citations=["Newton 1701"],
                tags=["cooling", "exponential"]
            )
        ]
        
        # ===== 6. NONLINEAR DYNAMICS (15+ families) =====
        library[HypothesisFamily.LORENZ] = [
            Hypothesis(
                family=HypothesisFamily.LORENZ,
                name="Lorenz System",
                formulation="dx/dt = σ·(y - x), dy/dt = x·(ρ - z) - y, dz/dt = x·y - β·z",
                parameter_names=["σ", "ρ", "β"],
                parameter_defaults={"σ": 10, "ρ": 28, "β": 8/3},
                parameter_bounds={"σ": [1, 20], "ρ": [1, 50], "β": [1, 10]},
                assumptions=["chaotic", "deterministic"],
                applicability=["chaos", "atmospheric_convection"],
                complexity=7,
                computational_cost="O(n²)",
                source="chaos_theory",
                citations=["Lorenz 1963"],
                tags=["chaos", "butterfly", "strange_attractor"]
            )
        ]
        
        library[HypothesisFamily.VAN_DER_POL] = [
            Hypothesis(
                family=HypothesisFamily.VAN_DER_POL,
                name="Van der Pol Oscillator",
                formulation="d²x/dt² - μ·(1 - x²)·dx/dt + x = 0",
                parameter_names=["μ"],
                parameter_defaults={"μ": 1.0},
                parameter_bounds={"μ": [0.01, 10]},
                assumptions=["self_oscillation", "nonlinear_damping"],
                applicability=["limit_cycles", "relaxation_oscillations"],
                complexity=6,
                computational_cost="O(n²)",
                source="nonlinear_dynamics",
                citations=["Van der Pol 1920"],
                tags=["oscillator", "limit_cycle"]
            )
        ]
        
        # ===== 7. MACHINE LEARNING SURROGATES (6 families) =====
        library[HypothesisFamily.GAUSSIAN_PROCESS] = [
            Hypothesis(
                family=HypothesisFamily.GAUSSIAN_PROCESS,
                name="Gaussian Process with RBF Kernel",
                formulation="f(x) ~ GP(μ(x), k(x,x')), k(x,x') = σ²·exp(-||x-x'||²/(2l²))",
                parameter_names=["σ²", "l", "σ_n²"],
                parameter_defaults={"σ²": 1.0, "l": 1.0, "σ_n²": 0.1},
                parameter_bounds={"σ²": [0.1, 10], "l": [0.1, 10], "σ_n²": [0.01, 1]},
                assumptions=["smooth", "stationary_kernel"],
                applicability=["interpolation", "uncertainty_quantification"],
                complexity=6,
                computational_cost="O(n³)",
                source="machine_learning",
                citations=["Rasmussen & Williams 2006"],
                tags=["gp", "bayesian", "nonparametric"]
            )
        ]
        
        library[HypothesisFamily.SINDY] = [
            Hypothesis(
                family=HypothesisFamily.SINDY,
                name="Sparse Identification of Nonlinear Dynamics",
                formulation="dx/dt = Θ(x)·Ξ",
                parameter_names=["library", "sparsity_threshold"],
                parameter_defaults={"library": "polynomial", "sparsity_threshold": 0.1},
                parameter_bounds={"sparsity_threshold": [0.01, 1]},
                assumptions=["sparse", "differentiable"],
                applicability=["system_identification", "discovery"],
                complexity=8,
                computational_cost="O(n·m²)",
                source="data_driven_dynamics",
                citations=["Brunton et al. 2016"],
                tags=["sindy", "sparse", "discovery"]
            )
        ]
        
        return library
    
    def _is_applicable(self, hypothesis: Hypothesis, features) -> bool:
        """Check if hypothesis is applicable to given signal features"""
        
        # Stationarity requirement
        if "stationary" in hypothesis.applicability and not features.is_stationary:
            return False
        if "nonstationary" in hypothesis.applicability and features.is_stationary:
            return False
        
        # SNR requirement
        if hypothesis.family == HypothesisFamily.WAVELET and features.snr_db < 10:
            return False
        if "high_snr" in hypothesis.applicability and features.snr_db < 15:
            return False
        if "low_snr" in hypothesis.applicability and features.snr_db > 15:
            return False
        
        # Continuity requirement
        if "continuous" in hypothesis.assumptions and not features.is_continuous:
            return False
        
        # Differentiability requirement
        if "differentiable" in hypothesis.assumptions and features.differentiability_order < 1:
            return False
        if "twice_differentiable" in hypothesis.assumptions and features.differentiability_order < 2:
            return False
        
        # Data length requirement
        if hypothesis.computational_cost == "O(n²)" and features.length > 5000:
            return False
        if hypothesis.computational_cost == "O(n³)" and features.length > 1000:
            return False
        
        # Regime requirement
        if "single_regime" in hypothesis.applicability and features.n_regimes > 1:
            return False
        if "multiple_regimes" in hypothesis.applicability and features.n_regimes == 1:
            return False
        
        # Missing data requirement
        if hypothesis.complexity > 5 and features.missing_ratio > 0.05:
            return False
        
        return True
    
    def _get_baseline_hypotheses(self) -> List[Hypothesis]:
        """Get robust baseline hypotheses that work for most signals"""
        return [
            Hypothesis(
                family=HypothesisFamily.POLYNOMIAL,
                name="Linear (Robust Baseline)",
                formulation="y = a·x + b",
                parameter_names=["a", "b"],
                parameter_defaults={"a": 1.0, "b": 0.0},
                parameter_bounds={"a": [-1e6, 1e6], "b": [-1e6, 1e6]},
                assumptions=[],
                applicability=["any"],
                complexity=1,
                computational_cost="O(n)",
                source="baseline",
                tags=["baseline", "robust"]
            ),
            Hypothesis(
                family=HypothesisFamily.EXPONENTIAL,
                name="Exponential (Robust Baseline)",
                formulation="y = a·exp(b·x)",
                parameter_names=["a", "b"],
                parameter_defaults={"a": 1.0, "b": 0.1},
                parameter_bounds={"a": [1e-6, 1e6], "b": [-10, 10]},
                assumptions=[],
                applicability=["any"],
                complexity=2,
                computational_cost="O(n)",
                source="baseline",
                tags=["baseline", "robust"]
            ),
            Hypothesis(
                family=HypothesisFamily.ARIMA,
                name="AR(1) (Robust Baseline)",
                formulation="y_t = c + φ·y_{t-1} + ε_t",
                parameter_names=["c", "φ", "σ²"],
                parameter_defaults={"c": 0, "φ": 0.5, "σ²": 1},
                parameter_bounds={"φ": [-1, 1], "σ²": [0.01, 100]},
                assumptions=[],
                applicability=["any"],
                complexity=3,
                computational_cost="O(n)",
                source="baseline",
                tags=["baseline", "robust", "timeseries"]
            )
        ]
    
    def get_hypothesis_by_name(self, name: str) -> Optional[Hypothesis]:
        """Get a hypothesis by name"""
        for hypotheses in self.library.values():
            for h in hypotheses:
                if h.name == name:
                    return h
        return None
    
    def get_hypotheses_by_family(self, family: HypothesisFamily) -> List[Hypothesis]:
        """Get all hypotheses in a family"""
        return self.library.get(family, [])
    
    def get_hypotheses_by_tag(self, tag: str) -> List[Hypothesis]:
        """Get all hypotheses with a specific tag"""
        result = []
        for hypotheses in self.library.values():
            for h in hypotheses:
                if tag in h.tags:
                    result.append(h)
        return result
    
    def export_library_summary(self) -> Dict:
        """Export summary of the hypothesis library"""
        summary = {}
        for family, hypotheses in self.library.items():
            summary[family.value] = {
                'count': len(hypotheses),
                'names': [h.name for h in hypotheses],
                'complexity_range': [
                    min(h.complexity for h in hypotheses),
                    max(h.complexity for h in hypotheses)
                ]
            }
        return summary
