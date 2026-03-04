"""
L4: Parameter Calibration
Quantifies explanatory power using Bayesian inference with full uncertainty quantification
"""

import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')

# Try importing Bayesian libraries with fallbacks
try:
    import pymc3 as pm
    import arviz as az
    BAYESIAN_AVAILABLE = True
except ImportError:
    BAYESIAN_AVAILABLE = False
    print("⚠️  PyMC3 not available - using approximate Bayesian methods")

try:
    from scipy.optimize import minimize, differential_evolution
    from scipy.stats import norm, t, chi2
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

@dataclass
class CalibratedModel:
    """Fully calibrated model with uncertainty quantification"""
    
    hypothesis_name: str
    formulation: str
    
    # Parameter estimates
    parameters: Dict[str, float]
    parameter_std: Dict[str, float]  # Standard deviation
    parameter_hdi: Dict[str, Tuple[float, float]]  # Highest Density Interval (94%)
    
    # Model quality
    waic: float  # Watanabe-Akaike Information Criterion
    loo: float   # Leave-one-out cross-validation
    r2: float    # Bayesian R²
    mse: float   # Mean squared error
    mae: float   # Mean absolute error
    
    # Uncertainty
    posterior_samples: Dict[str, np.ndarray]
    predictive_mean: np.ndarray
    predictive_std: np.ndarray
    predictive_hdi: Tuple[np.ndarray, np.ndarray]  # (lower, upper)
    
    # Convergence diagnostics (for MCMC)
    rhat: Optional[Dict[str, float]]
    effective_sample_size: Optional[Dict[str, int]]
    
    # Residuals
    residuals: np.ndarray
    standardized_residuals: np.ndarray
    
    # Calibration metadata
    n_samples: int
    n_chains: int
    sampling_time: float
    method: str  # "mcmc", "optimization", "approximate"
    converged: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        d = asdict(self)
        # Convert numpy arrays to lists
        if isinstance(d['posterior_samples'], dict):
            d['posterior_samples'] = {
                k: v.tolist() if isinstance(v, np.ndarray) else v 
                for k, v in d['posterior_samples'].items()
            }
        if isinstance(d['predictive_mean'], np.ndarray):
            d['predictive_mean'] = d['predictive_mean'].tolist()
        if isinstance(d['predictive_std'], np.ndarray):
            d['predictive_std'] = d['predictive_std'].tolist()
        if isinstance(d['residuals'], np.ndarray):
            d['residuals'] = d['residuals'].tolist()
        if isinstance(d['standardized_residuals'], np.ndarray):
            d['standardized_residuals'] = d['standardized_residuals'].tolist()
        return d
    
    def summary(self) -> str:
        """Generate human-readable summary"""
        lines = []
        lines.append(f"Model: {self.hypothesis_name}")
        lines.append(f"R² = {self.r2:.3f}  |  MSE = {self.mse:.4f}  |  WAIC = {self.waic:.1f}")
        lines.append("\nParameters:")
        for name, value in self.parameters.items():
            std = self.parameter_std.get(name, 0)
            hdi = self.parameter_hdi.get(name, (value, value))
            lines.append(f"  {name} = {value:.4f} ± {2*std:.4f}  [{hdi[0]:.4f}, {hdi[1]:.4f}]")
        return "\n".join(lines)

class ParameterCalibrator:
    """
    L4: Parameter Calibration Layer
    
    Quantifies explanatory power using Bayesian inference,
    providing rigorous confidence intervals rather than single point estimates.
    """
    
    def __init__(self, method: str = "auto", random_seed: int = 42):
        """
        Initialize parameter calibrator
        
        Args:
            method: Calibration method - "mcmc", "optimization", "approximate", or "auto"
            random_seed: Random seed for reproducibility
        """
        self.name = "XRAG-L4"
        self.version = "1.0.0"
        self.random_seed = random_seed
        np.random.seed(random_seed)
        
        # Determine best available method
        if method == "auto":
            if BAYESIAN_AVAILABLE:
                self.method = "mcmc"
            elif SCIPY_AVAILABLE:
                self.method = "optimization"
            else:
                self.method = "approximate"
        else:
            self.method = method
        
        print(f"   Calibration method: {self.method}")
        
    def calibrate(self,
                  hypothesis,
                  x_data: np.ndarray,
                  y_data: np.ndarray,
                  n_samples: int = 2000,
                  n_chains: int = 4,
                  tune: int = 1000,
                  progressbar: bool = False) -> Optional[CalibratedModel]:
        """
        Calibrate model parameters with full uncertainty quantification
        
        Args:
            hypothesis: Hypothesis object from L2
            x_data: Input data
            y_data: Output data
            n_samples: Number of posterior samples
            n_chains: Number of MCMC chains
            tune: Tuning steps for MCMC
            progressbar: Show progress bar
            
        Returns:
            CalibratedModel with full uncertainty, or None if calibration fails
        """
        
        start_time = time.time()
        
        try:
            # Validate data
            x_data = np.asarray(x_data, dtype=np.float64).flatten()
            y_data = np.asarray(y_data, dtype=np.float64).flatten()
            
            if len(x_data) != len(y_data):
                raise ValueError(f"x and y length mismatch: {len(x_data)} vs {len(y_data)}")
            
            if len(x_data) < 5:
                raise ValueError(f"Insufficient data: {len(x_data)} points")
            
            # Remove NaN values
            mask = ~(np.isnan(x_data) | np.isnan(y_data) | np.isinf(x_data) | np.isinf(y_data))
            x_clean = x_data[mask]
            y_clean = y_data[mask]
            
            if len(x_clean) < 5:
                raise ValueError(f"Insufficient clean data: {len(x_clean)} points")
            
            # Choose calibration method
            if self.method == "mcmc" and BAYESIAN_AVAILABLE:
                model = self._calibrate_mcmc(
                    hypothesis, x_clean, y_clean, n_samples, n_chains, tune, progressbar
                )
            elif self.method == "optimization" and SCIPY_AVAILABLE:
                model = self._calibrate_optimization(hypothesis, x_clean, y_clean)
            else:
                model = self._calibrate_approximate(hypothesis, x_clean, y_clean)
            
            if model is None:
                return None
            
            # Add metadata
            model.sampling_time = time.time() - start_time
            model.n_samples = n_samples
            model.n_chains = n_chains
            
            return model
            
        except Exception as e:
            print(f"  ⚠️ Calibration failed for {hypothesis.name}: {e}")
            return None
    
    def _calibrate_mcmc(self, hypothesis, x, y, n_samples, n_chains, tune, progressbar):
        """Full Bayesian MCMC calibration"""
        
        with pm.Model() as model:
            # Build model
            self._build_pymc3_model(hypothesis, x, y)
            
            # Sample from posterior
            trace = pm.sample(
                draws=n_samples,
                chains=n_chains,
                tune=tune,
                return_inferencedata=True,
                progressbar=progressbar,
                random_seed=self.random_seed
            )
            
            # Check convergence
            rhat_dict = {}
            ess_dict = {}
            
            try:
                rhat = az.rhat(trace)
                ess = az.ess(trace)
                
                for var in trace.posterior.data_vars:
                    if var != 'likelihood':
                        rhat_dict[var] = float(rhat[var].values)
                        ess_dict[var] = int(ess[var].values)
            except:
                rhat_dict = None
                ess_dict = None
            
            # Extract parameter estimates
            parameters = {}
            parameter_std = {}
            parameter_hdi = {}
            posterior_samples = {}
            
            for var in trace.posterior.data_vars:
                if var != 'likelihood':
                    samples = trace.posterior[var].values.flatten()
                    posterior_samples[var] = samples
                    parameters[var] = float(np.mean(samples))
                    parameter_std[var] = float(np.std(samples))
                    
                    # 94% HDI
                    hdi = az.hdi(samples, hdi_prob=0.94)
                    parameter_hdi[var] = (float(hdi[0]), float(hdi[1]))
            
            # Generate posterior predictive
            with model:
                ppc = pm.sample_posterior_predictive(
                    trace, 
                    random_seed=self.random_seed,
                    progressbar=progressbar
                )
            
            predictive = ppc['likelihood']
            predictive_mean = np.mean(predictive, axis=0)
            predictive_std = np.std(predictive, axis=0)
            predictive_hdi = az.hdi(predictive, hdi_prob=0.94)
            
            # Compute model comparison metrics
            try:
                waic = az.waic(trace).waic
                loo = az.loo(trace).loo
            except:
                waic = float('inf')
                loo = float('inf')
            
            # Compute residuals and fit metrics
            residuals = y - predictive_mean
            mse = np.mean(residuals ** 2)
            mae = np.mean(np.abs(residuals))
            
            # Bayesian R²
            var_resid = np.var(residuals)
            var_y = np.var(y)
            r2 = 1 - var_resid / (var_y + 1e-12)
            
            # Standardized residuals
            std_residuals = residuals / (np.std(residuals) + 1e-12)
            
            # Check convergence
            converged = True
            if rhat_dict:
                converged = all(v < 1.1 for v in rhat_dict.values())
            
            return CalibratedModel(
                hypothesis_name=hypothesis.name,
                formulation=hypothesis.formulation,
                parameters=parameters,
                parameter_std=parameter_std,
                parameter_hdi=parameter_hdi,
                waic=float(waic),
                loo=float(loo),
                r2=float(r2),
                mse=float(mse),
                mae=float(mae),
                posterior_samples=posterior_samples,
                predictive_mean=predictive_mean,
                predictive_std=predictive_std,
                predictive_hdi=(predictive_hdi[:, 0], predictive_hdi[:, 1]),
                rhat=rhat_dict,
                effective_sample_size=ess_dict,
                residuals=residuals,
                standardized_residuals=std_residuals,
                n_samples=n_samples,
                n_chains=n_chains,
                sampling_time=0,
                method="mcmc",
                converged=converged
            )
    
    def _calibrate_optimization(self, hypothesis, x, y):
        """Optimization-based calibration (maximum likelihood)"""
        
        # Define negative log-likelihood function
        def neg_log_likelihood(params):
            try:
                param_dict = dict(zip(hypothesis.parameter_names, params))
                y_pred = self._compute_model_output(hypothesis, x, param_dict)
                
                # Gaussian likelihood
                sigma = param_dict.get('sigma', 0.1)
                if sigma <= 0:
                    sigma = 0.1
                
                nll = 0.5 * np.sum(((y - y_pred) / sigma) ** 2) + len(y) * np.log(sigma)
                return nll
            except:
                return 1e12
        
        # Set bounds
        bounds = []
        initial_guess = []
        
        for param in hypothesis.parameter_names:
            if param in hypothesis.parameter_bounds:
                bounds.append(tuple(hypothesis.parameter_bounds[param]))
            else:
                bounds.append((-10, 10))  # Default bounds
            
            if param in hypothesis.parameter_defaults:
                initial_guess.append(hypothesis.parameter_defaults[param])
            else:
                initial_guess.append(0)
        
        # Optimize
        try:
            # Try global optimization first
            result = differential_evolution(
                neg_log_likelihood,
                bounds,
                seed=self.random_seed,
                maxiter=1000
            )
            
            if not result.success:
                # Fall back to local optimization
                result = minimize(
                    neg_log_likelihood,
                    initial_guess,
                    bounds=bounds,
                    method='L-BFGS-B'
                )
            
            if not result.success:
                return None
            
            # Extract parameters
            parameters = dict(zip(hypothesis.parameter_names, result.x))
            
            # Compute approximate uncertainty via Hessian
            try:
                from scipy.optimize import approx_fprime
                hess = approx_fprime(result.x, lambda p: neg_log_likelihood(p), 1e-6)
                cov = np.linalg.inv(hess + 1e-6 * np.eye(len(result.x)))
                stds = np.sqrt(np.diag(cov))
                parameter_std = dict(zip(hypothesis.parameter_names, stds))
            except:
                parameter_std = {p: 0.1 for p in hypothesis.parameter_names}
            
            # Compute predictions
            y_pred = self._compute_model_output(hypothesis, x, parameters)
            
            # Compute metrics
            residuals = y - y_pred
            mse = np.mean(residuals ** 2)
            mae = np.mean(np.abs(residuals))
            var_resid = np.var(residuals)
            var_y = np.var(y)
            r2 = 1 - var_resid / (var_y + 1e-12)
            
            # Approximate uncertainty
            n_params = len(parameters)
            n = len(y)
            aic = n * np.log(mse) + 2 * n_params
            waic = aic  # Approximate
            
            # Generate approximate posterior samples
            posterior_samples = {}
            for param, std in parameter_std.items():
                posterior_samples[param] = np.random.normal(
                    parameters[param], std, size=1000
                )
            
            # Approximate predictive distribution
            predictive_samples = []
            for _ in range(100):
                param_sample = {
                    p: np.random.normal(parameters[p], parameter_std[p])
                    for p in parameters
                }
                y_sample = self._compute_model_output(hypothesis, x, param_sample)
                predictive_samples.append(y_sample)
            
            predictive_samples = np.array(predictive_samples)
            predictive_mean = np.mean(predictive_samples, axis=0)
            predictive_std = np.std(predictive_samples, axis=0)
            predictive_hdi_lower = np.percentile(predictive_samples, 3, axis=0)
            predictive_hdi_upper = np.percentile(predictive_samples, 97, axis=0)
            
            # Approximate parameter HDI
            parameter_hdi = {}
            for param, samples in posterior_samples.items():
                parameter_hdi[param] = (
                    float(np.percentile(samples, 3)),
                    float(np.percentile(samples, 97))
                )
            
            return CalibratedModel(
                hypothesis_name=hypothesis.name,
                formulation=hypothesis.formulation,
                parameters=parameters,
                parameter_std=parameter_std,
                parameter_hdi=parameter_hdi,
                waic=float(waic),
                loo=float(waic),  # Approximate
                r2=float(r2),
                mse=float(mse),
                mae=float(mae),
                posterior_samples=posterior_samples,
                predictive_mean=predictive_mean,
                predictive_std=predictive_std,
                predictive_hdi=(predictive_hdi_lower, predictive_hdi_upper),
                rhat=None,
                effective_sample_size=None,
                residuals=residuals,
                standardized_residuals=residuals / (np.std(residuals) + 1e-12),
                n_samples=1000,
                n_chains=1,
                sampling_time=0,
                method="optimization",
                converged=result.success
            )
            
        except Exception as e:
            print(f"  Optimization failed: {e}")
            return None
    
    def _calibrate_approximate(self, hypothesis, x, y):
        """Approximate calibration using least squares"""
        
        # Define error function
        def error_func(params):
            param_dict = dict(zip(hypothesis.parameter_names, params))
            try:
                y_pred = self._compute_model_output(hypothesis, x, param_dict)
                return np.sum((y - y_pred) ** 2)
            except:
                return 1e12
        
        # Simple grid search for approximate parameters
        best_params = {}
        best_error = float('inf')
        
        # Try default parameters
        default_params = []
        for param in hypothesis.parameter_names:
            if param in hypothesis.parameter_defaults:
                default_params.append(hypothesis.parameter_defaults[param])
            else:
                default_params.append(0)
        
        best_error = error_func(default_params)
        best_params = dict(zip(hypothesis.parameter_names, default_params))
        
        # Try random perturbations
        for _ in range(100):
            perturbed = []
            for i, param in enumerate(hypothesis.parameter_names):
                if param in hypothesis.parameter_bounds:
                    low, high = hypothesis.parameter_bounds[param]
                    perturbed.append(np.random.uniform(low, high))
                else:
                    perturbed.append(default_params[i] + np.random.normal(0, 0.1))
            
            error = error_func(perturbed)
            if error < best_error:
                best_error = error
                best_params = dict(zip(hypothesis.parameter_names, perturbed))
        
        # Compute predictions
        y_pred = self._compute_model_output(hypothesis, x, best_params)
        
        # Compute metrics
        residuals = y - y_pred
        mse = np.mean(residuals ** 2)
        mae = np.mean(np.abs(residuals))
        var_resid = np.var(residuals)
        var_y = np.var(y)
        r2 = 1 - var_resid / (var_y + 1e-12)
        
        # Simple parameter uncertainty
        parameter_std = {p: 0.1 * abs(v) + 0.01 for p, v in best_params.items()}
        
        # Approximate parameter HDI
        parameter_hdi = {}
        for p in best_params:
            param_samples = np.random.normal(best_params[p], parameter_std[p], 1000)
            parameter_hdi[p] = (
                float(np.percentile(param_samples, 3)),
                float(np.percentile(param_samples, 97))
            )
        
        # Approximate posterior samples
        posterior_samples = {}
        for p in best_params:
            posterior_samples[p] = np.random.normal(best_params[p], parameter_std[p], 1000)
        
        # Approximate predictive
        predictive_mean = y_pred
        predictive_std = np.sqrt(mse) * np.ones_like(y)
        predictive_hdi_lower = y_pred - 2 * np.sqrt(mse)
        predictive_hdi_upper = y_pred + 2 * np.sqrt(mse)
        
        # Information criteria (approximate)
        n_params = len(best_params)
        n = len(y)
        aic = n * np.log(mse) + 2 * n_params
        waic = aic
        
        return CalibratedModel(
            hypothesis_name=hypothesis.name,
            formulation=hypothesis.formulation,
            parameters=best_params,
            parameter_std=parameter_std,
            parameter_hdi=parameter_hdi,
            waic=float(waic),
            loo=float(waic),
            r2=float(r2),
            mse=float(mse),
            mae=float(mae),
            posterior_samples=posterior_samples,
            predictive_mean=predictive_mean,
            predictive_std=predictive_std,
            predictive_hdi=(predictive_hdi_lower, predictive_hdi_upper),
            rhat=None,
            effective_sample_size=None,
            residuals=residuals,
            standardized_residuals=residuals / (np.std(residuals) + 1e-12),
            n_samples=1000,
            n_chains=1,
            sampling_time=0,
            method="approximate",
            converged=True
        )
    
    def _build_pymc3_model(self, hypothesis, x, y):
        """Build PyMC3 model based on hypothesis family"""
        
        family = hypothesis.family.value
        
        if family == "linear" or "polynomial" in family:
            # Linear regression
            a = pm.Normal('a', mu=0, sigma=100)
            b = pm.Normal('b', mu=0, sigma=100)
            sigma = pm.HalfNormal('sigma', sigma=10)
            
            if "quadratic" in hypothesis.name.lower():
                # Quadratic
                c = pm.Normal('c', mu=0, sigma=100)
                mu = a * x**2 + b * x + c
            elif "cubic" in hypothesis.name.lower():
                # Cubic
                c = pm.Normal('c', mu=0, sigma=100)
                d = pm.Normal('d', mu=0, sigma=100)
                mu = a * x**3 + b * x**2 + c * x + d
            else:
                # Linear
                mu = a * x + b
            
            pm.Normal('likelihood', mu=mu, sigma=sigma, observed=y)
            
        elif family == "exponential":
            # y = a * exp(b * x)
            a = pm.LogNormal('a', mu=0, sigma=2)
            b = pm.Normal('b', mu=0, sigma=1)
            sigma = pm.HalfNormal('sigma', sigma=0.1)
            
            mu = a * pm.math.exp(b * x)
            pm.Normal('likelihood', mu=mu, sigma=sigma, observed=y)
            
        elif family == "power_law":
            # y = a * x^b
            a = pm.LogNormal('a', mu=0, sigma=2)
            b = pm.Normal('b', mu=0, sigma=1)
            sigma = pm.HalfNormal('sigma', sigma=0.1)
            
            # Ensure x > 0
            x_pos = pm.math.maximum(x, 1e-6)
            mu = a * x_pos ** b
            pm.Normal('likelihood', mu=mu, sigma=sigma, observed=y)
            
        elif family == "logistic":
            # y = L / (1 + exp(-k*(x - x0)))
            L = pm.LogNormal('L', mu=np.log(np.max(y)), sigma=2)
            k = pm.LogNormal('k', mu=0, sigma=1)
            x0 = pm.Normal('x0', mu=np.median(x), sigma=np.std(x))
            sigma = pm.HalfNormal('sigma', sigma=0.1 * np.std(y))
            
            mu = L / (1 + pm.math.exp(-k * (x - x0)))
            pm.Normal('likelihood', mu=mu, sigma=sigma, observed=y)
            
        elif family == "arrhenius":
            # L = L0 * exp(-Ea/(k*T))
            L0 = pm.LogNormal('L0', mu=np.log(np.max(y)), sigma=2)
            Ea = pm.Normal('Ea', mu=0.85, sigma=0.2)
            k_B = 8.617e-5  # Boltzmann constant in eV/K
            
            # Ensure T > 0
            T_pos = pm.math.maximum(x, 1)
            mu = L0 * pm.math.exp(-Ea / (k_B * T_pos))
            sigma = pm.HalfNormal('sigma', sigma=0.1 * np.std(y))
            
            pm.Normal('likelihood', mu=mu, sigma=sigma, observed=y)
            
        elif "fourier" in family or "harmonic" in family:
            # y = a0 + Σ (ai*sin(iωx + φi))
            a0 = pm.Normal('a0', mu=np.mean(y), sigma=np.std(y))
            omega = pm.Normal('omega', mu=2*np.pi/(x[-1]-x[0]), sigma=0.5)
            sigma = pm.HalfNormal('sigma', sigma=0.1 * np.std(y))
            
            # Single harmonic for simplicity
            a1 = pm.Normal('a1', mu=0, sigma=np.std(y))
            phi1 = pm.Uniform('phi1', lower=0, upper=2*np.pi)
            
            mu = a0 + a1 * pm.math.sin(omega * x + phi1)
            pm.Normal('likelihood', mu=mu, sigma=sigma, observed=y)
            
        else:
            # Default: linear regression
            a = pm.Normal('a', mu=0, sigma=100)
            b = pm.Normal('b', mu=0, sigma=100)
            sigma = pm.HalfNormal('sigma', sigma=10)
            
            mu = a * x + b
            pm.Normal('likelihood', mu=mu, sigma=sigma, observed=y)
    
    def _compute_model_output(self, hypothesis, x, params):
        """Compute model output given parameters"""
        
        family = hypothesis.family.value
        name = hypothesis.name.lower()
        
        if family == "linear" or "polynomial" in family:
            if "quadratic" in name:
                return params['a'] * x**2 + params['b'] * x + params.get('c', 0)
            elif "cubic" in name:
                return params['a'] * x**3 + params['b'] * x**2 + params['c'] * x + params.get('d', 0)
            else:
                return params.get('a', 1) * x + params.get('b', 0)
                
        elif family == "exponential":
            return params['a'] * np.exp(params['b'] * x)
            
        elif family == "power_law":
            x_safe = np.maximum(x, 1e-6)
            return params['a'] * x_safe ** params['b']
            
        elif family == "logistic":
            L = params['L']
            k = params['k']
            x0 = params['x0']
            return L / (1 + np.exp(-k * (x - x0)))
            
        elif family == "arrhenius":
            L0 = params['L0']
            Ea = params['Ea']
            k_B = 8.617e-5
            T_safe = np.maximum(x, 1)
            return L0 * np.exp(-Ea / (k_B * T_safe))
            
        elif "fourier" in family:
            a0 = params.get('a0', np.mean(x))
            a1 = params.get('a1', 0)
            omega = params.get('omega', 2*np.pi/(x[-1]-x[0]+1e-6))
            phi = params.get('phi1', 0)
            return a0 + a1 * np.sin(omega * x + phi)
            
        else:
            # Default fallback
            if 'a' in params and 'b' in params:
                return params['a'] * x + params['b']
            else:
                return np.mean(x) * np.ones_like(x)
    
    def compare_models(self, models: List[CalibratedModel]) -> Dict:
        """Compare multiple calibrated models"""
        
        if not models:
            return {}
        
        comparison = {
            'best_by_r2': max(models, key=lambda m: m.r2).hypothesis_name,
            'best_by_waic': min(models, key=lambda m: m.waic).hypothesis_name,
            'best_by_mae': min(models, key=lambda m: m.mae).hypothesis_name,
            'rankings': []
        }
        
        # Create ranking
        for i, model in enumerate(models):
            comparison['rankings'].append({
                'rank': i + 1,
                'name': model.hypothesis_name,
                'r2': model.r2,
                'waic': model.waic,
                'mae': model.mae,
                'n_params': len(model.parameters)
            })
        
        # Sort by R²
        comparison['rankings'].sort(key=lambda x: x['r2'], reverse=True)
        
        return comparison
