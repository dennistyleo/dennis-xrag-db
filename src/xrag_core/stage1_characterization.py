"""
L1: Problem Characterization
Identifies mathematical nature of the signal with rigorous statistical tests
"""

import numpy as np
from scipy import stats, signal
from statsmodels.tsa.stattools import adfuller, kpss
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Optional, List
import warnings
from enum import Enum

class StationarityType(Enum):
    """Types of stationarity"""
    STRICTLY_STATIONARY = "strictly_stationary"
    WEAKLY_STATIONARY = "weakly_stationary"
    TREND_STATIONARY = "trend_stationary"
    DIFFERENCE_STATIONARY = "difference_stationary"
    NON_STATIONARY = "non_stationary"

class SignalClass(Enum):
    """Signal classification based on mathematical properties"""
    DETERMINISTIC = "deterministic"
    STOCHASTIC = "stochastic"
    CHAOTIC = "chaotic"
    PERIODIC = "periodic"
    QUASI_PERIODIC = "quasi_periodic"
    TRANSIENT = "transient"

@dataclass
class SignalFeatures:
    """Extracted mathematical features from raw signal"""
    
    # Stationarity
    is_stationary: bool
    stationarity_type: StationarityType
    stationarity_test: str
    stationarity_pvalue: float
    adf_statistic: float
    kpss_statistic: float
    
    # Signal quality
    snr_db: float
    signal_power: float
    noise_power: float
    peak_to_peak: float
    rms: float
    
    # Continuity
    is_continuous: bool
    discontinuity_points: List[int]
    differentiability_order: int
    has_jumps: bool
    has_cusps: bool
    
    # Statistical properties
    mean: float
    variance: float
    skewness: float
    kurtosis: float
    entropy: float
    
    # Temporal features
    length: int
    sampling_rate: Optional[float]
    has_missing_data: bool
    missing_indices: List[int]
    missing_ratio: float
    
    # Spectral properties
    dominant_frequencies: List[float]
    power_spectrum: np.ndarray
    bandwidth: float
    
    # Regime changes
    n_regimes: int
    change_points: List[int]
    
    # Signal classification
    signal_class: SignalClass
    complexity_measure: float  # 0-1 scale
    lyapunov_estimate: Optional[float]  # For chaotic signals
    
    # Raw feature vector for downstream stages
    feature_vector: np.ndarray
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        d = asdict(self)
        # Convert enums to strings
        d['stationarity_type'] = self.stationarity_type.value
        d['signal_class'] = self.signal_class.value
        # Convert numpy arrays to lists
        if isinstance(d['power_spectrum'], np.ndarray):
            d['power_spectrum'] = d['power_spectrum'].tolist()
        if isinstance(d['feature_vector'], np.ndarray):
            d['feature_vector'] = d['feature_vector'].tolist()
        return d

class ProblemCharacterizer:
    """
    L1: Problem Characterization Layer
    
    Identifies the mathematical nature of the signal using rigorous
    statistical tests and signal processing techniques.
    """
    
    def __init__(self):
        self.name = "XRAG-L1"
        self.version = "1.0.0"
        
    def characterize(self, 
                     signal: np.ndarray,
                     time: Optional[np.ndarray] = None,
                     sampling_rate: Optional[float] = None) -> SignalFeatures:
        """
        Characterize the mathematical nature of the signal
        
        Args:
            signal: Raw signal data (1D numpy array)
            time: Optional time vector
            sampling_rate: Optional sampling rate in Hz
            
        Returns:
            SignalFeatures object with extracted characteristics
            
        Raises:
            ValueError: If signal is invalid
        """
        
        # Validate input
        if not isinstance(signal, np.ndarray):
            signal = np.array(signal, dtype=np.float64)
        
        if len(signal) < 10:
            raise ValueError(f"Signal too short: {len(signal)} points (minimum 10)")
        
        if np.all(np.isnan(signal)):
            raise ValueError("Signal contains only NaN values")
        
        # Handle missing data
        signal_clean, missing_indices = self._handle_missing_data(signal)
        
        # Basic statistical properties
        mean = np.nanmean(signal_clean)
        variance = np.nanvar(signal_clean)
        std = np.sqrt(variance)
        
        # Handle edge cases
        if std == 0:
            # Constant signal
            std = 1e-12
            
        skewness = stats.skew(signal_clean[~np.isnan(signal_clean)])
        kurtosis = stats.kurtosis(signal_clean[~np.isnan(signal_clean)])
        
        # Signal quality assessment
        signal_power = np.nanmean(signal_clean ** 2)
        noise_power = self._estimate_noise_power(signal_clean)
        
        # Avoid division by zero
        if noise_power < 1e-12:
            noise_power = 1e-12
            
        snr_db = 10 * np.log10(signal_power / noise_power)
        
        # Clip to reasonable range
        snr_db = np.clip(snr_db, -20, 60)
        
        # Peak-to-peak and RMS
        peak_to_peak = np.nanmax(signal_clean) - np.nanmin(signal_clean)
        rms = np.sqrt(np.nanmean(signal_clean ** 2))
        
        # Stationarity tests
        stationarity_result = self._check_stationarity(signal_clean)
        
        # Continuity and differentiability
        continuity_result = self._check_continuity(signal_clean)
        
        # Data quality
        missing_ratio = len(missing_indices) / len(signal) if len(signal) > 0 else 0
        
        # Spectral analysis
        spectral_features = self._spectral_analysis(signal_clean, sampling_rate)
        
        # Regime change detection
        regime_features = self._detect_regime_changes(signal_clean)
        
        # Signal classification
        classification = self._classify_signal(
            signal_clean, 
            stationarity_result,
            spectral_features,
            continuity_result
        )
        
        # Entropy (complexity measure)
        entropy = self._compute_entropy(signal_clean)
        
        # Construct feature vector
        feature_vector = self._build_feature_vector(
            mean, variance, skewness, kurtosis,
            snr_db, 
            1.0 if stationarity_result['is_stationary'] else 0.0,
            continuity_result['differentiability_order'],
            regime_features['n_regimes'],
            missing_ratio,
            entropy,
            spectral_features['bandwidth']
        )
        
        return SignalFeatures(
            is_stationary=stationarity_result['is_stationary'],
            stationarity_type=stationarity_result['stationarity_type'],
            stationarity_test=stationarity_result['test_name'],
            stationarity_pvalue=stationarity_result['pvalue'],
            adf_statistic=stationarity_result.get('adf_stat', 0),
            kpss_statistic=stationarity_result.get('kpss_stat', 0),
            snr_db=float(snr_db),
            signal_power=float(signal_power),
            noise_power=float(noise_power),
            peak_to_peak=float(peak_to_peak),
            rms=float(rms),
            is_continuous=continuity_result['is_continuous'],
            discontinuity_points=continuity_result['discontinuity_points'],
            differentiability_order=continuity_result['differentiability_order'],
            has_jumps=continuity_result['has_jumps'],
            has_cusps=continuity_result['has_cusps'],
            mean=float(mean),
            variance=float(variance),
            skewness=float(skewness),
            kurtosis=float(kurtosis),
            entropy=float(entropy),
            length=len(signal),
            sampling_rate=sampling_rate,
            has_missing_data=len(missing_indices) > 0,
            missing_indices=missing_indices,
            missing_ratio=float(missing_ratio),
            dominant_frequencies=spectral_features['dominant_frequencies'],
            power_spectrum=spectral_features['power_spectrum'],
            bandwidth=float(spectral_features['bandwidth']),
            n_regimes=regime_features['n_regimes'],
            change_points=regime_features['change_points'],
            signal_class=classification['signal_class'],
            complexity_measure=float(classification['complexity']),
            lyapunov_estimate=classification.get('lyapunov'),
            feature_vector=feature_vector
        )
    
    def _handle_missing_data(self, signal: np.ndarray) -> Tuple[np.ndarray, List[int]]:
        """Handle missing data (NaNs and infinities)"""
        signal_clean = signal.copy()
        missing_indices = []
        
        for i, val in enumerate(signal_clean):
            if np.isnan(val) or np.isinf(val):
                missing_indices.append(i)
        
        if missing_indices:
            # Simple interpolation for missing values
            good_indices = [i for i in range(len(signal_clean)) if i not in missing_indices]
            if len(good_indices) > 1:
                signal_clean[missing_indices] = np.interp(
                    missing_indices, 
                    good_indices, 
                    signal_clean[good_indices]
                )
            else:
                # If too many missing, fill with mean
                mean_val = np.nanmean(signal_clean)
                if np.isnan(mean_val):
                    mean_val = 0
                signal_clean[missing_indices] = mean_val
        
        return signal_clean, missing_indices
    
    def _estimate_noise_power(self, signal: np.ndarray) -> float:
        """Estimate noise power using multiple methods"""
        if len(signal) < 10:
            return 1e-12
        
        # Method 1: MAD-based estimation (robust)
        median = np.median(signal)
        mad = np.median(np.abs(signal - median))
        mad_estimate = (mad / 0.6745) ** 2 if mad > 0 else 1e-12
        
        # Method 2: Wavelet-based estimation
        try:
            import pywt
            coeffs = pywt.wavedec(signal, 'db4', level=3)
            # Estimate noise from finest scale coefficients
            sigma = np.median(np.abs(coeffs[-1])) / 0.6745
            wavelet_estimate = sigma ** 2
        except:
            wavelet_estimate = mad_estimate
        
        # Method 3: Difference-based estimation
        diff_signal = np.diff(signal)
        diff_estimate = np.var(diff_signal) / 2
        
        # Combine estimates (weighted average)
        noise_power = 0.4 * mad_estimate + 0.4 * wavelet_estimate + 0.2 * diff_estimate
        
        return max(noise_power, 1e-12)
    
    def _check_stationarity(self, signal: np.ndarray) -> Dict:
        """Check stationarity using multiple tests"""
        result = {
            'is_stationary': False,
            'stationarity_type': StationarityType.NON_STATIONARY,
            'test_name': 'multiple',
            'pvalue': 0.5,
            'adf_stat': 0,
            'kpss_stat': 0
        }
        
        if len(signal) < 20:
            # Not enough data for reliable tests
            result['is_stationary'] = False
            result['stationarity_type'] = StationarityType.NON_STATIONARY
            result['pvalue'] = 0.5
            return result
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # ADF test (null: non-stationary)
                adf_result = adfuller(signal, autolag='AIC', regression='c')
                adf_stat = adf_result[0]
                adf_pvalue = adf_result[1]
                
                # KPSS test (null: stationary)
                kpss_result = kpss(signal, regression='c', nlags='auto')
                kpss_stat = kpss_result[0]
                kpss_pvalue = kpss_result[1]
                
                result['adf_stat'] = float(adf_stat)
                result['kpss_stat'] = float(kpss_stat)
                
                # Decision logic
                if kpss_pvalue > 0.05 and adf_pvalue < 0.05:
                    # Both tests agree on stationarity
                    result['is_stationary'] = True
                    result['stationarity_type'] = StationarityType.WEAKLY_STATIONARY
                    result['pvalue'] = float(max(kpss_pvalue, 1 - adf_pvalue))
                elif kpss_pvalue < 0.05 and adf_pvalue < 0.05:
                    # Both significant - differencing needed
                    result['is_stationary'] = False
                    result['stationarity_type'] = StationarityType.DIFFERENCE_STATIONARY
                    result['pvalue'] = float(min(kpss_pvalue, adf_pvalue))
                elif kpss_pvalue > 0.05 and adf_pvalue > 0.05:
                    # Inconclusive
                    result['is_stationary'] = False
                    result['stationarity_type'] = StationarityType.NON_STATIONARY
                    result['pvalue'] = float(min(kpss_pvalue, 1 - adf_pvalue))
                else:
                    # Mixed signals
                    result['is_stationary'] = kpss_pvalue > 0.05
                    result['stationarity_type'] = StationarityType.TREND_STATIONARY if adf_pvalue < 0.05 else StationarityType.NON_STATIONARY
                    result['pvalue'] = float(kpss_pvalue)
                    
        except Exception as e:
            # Fallback to variance ratio test
            half = len(signal) // 2
            var1 = np.var(signal[:half])
            var2 = np.var(signal[half:])
            
            if var1 > 0 and var2 > 0:
                ratio = var1 / var2
                result['is_stationary'] = 0.5 < ratio < 2.0
                result['test_name'] = 'variance_ratio'
                result['pvalue'] = float(abs(1 - ratio))
            else:
                result['is_stationary'] = False
                result['pvalue'] = 1.0
        
        return result
    
    def _check_continuity(self, signal: np.ndarray) -> Dict:
        """Check for discontinuities and estimate differentiability"""
        result = {
            'is_continuous': True,
            'discontinuity_points': [],
            'differentiability_order': 2,
            'has_jumps': False,
            'has_cusps': False
        }
        
        if len(signal) < 5:
            return result
        
        # Check for large jumps (discontinuities)
        diff = np.abs(np.diff(signal))
        if len(diff) > 0:
            threshold = 5 * np.std(diff) if np.std(diff) > 0 else 1e-6
            jump_indices = np.where(diff > threshold)[0]
            
            if len(jump_indices) > 0:
                result['is_continuous'] = False
                result['discontinuity_points'] = jump_indices.tolist()
                result['has_jumps'] = True
                result['differentiability_order'] = 0
                return result
        
        # Estimate differentiability order
        try:
            # First derivative smoothness
            first_diff = np.diff(signal)
            if len(first_diff) < 3:
                return result
                
            first_diff_norm = first_diff / (np.std(first_diff) + 1e-12)
            first_diff_roughness = np.std(np.diff(first_diff_norm))
            
            # Second derivative smoothness
            second_diff = np.diff(first_diff)
            if len(second_diff) < 3:
                result['differentiability_order'] = 1
                return result
                
            second_diff_norm = second_diff / (np.std(second_diff) + 1e-12)
            second_diff_roughness = np.std(np.diff(second_diff_norm))
            
            # Check for cusps (sharp corners)
            if first_diff_roughness > 2.0:
                result['has_cusps'] = True
                result['differentiability_order'] = 0
            elif second_diff_roughness > 2.0:
                result['differentiability_order'] = 1
            else:
                result['differentiability_order'] = 2
                
        except Exception:
            pass
        
        return result
    
    def _spectral_analysis(self, signal: np.ndarray, sampling_rate: Optional[float]) -> Dict:
        """Perform spectral analysis"""
        result = {
            'dominant_frequencies': [],
            'power_spectrum': np.array([]),
            'bandwidth': 0.0
        }
        
        n = len(signal)
        if n < 10:
            return result
        
        try:
            # Compute power spectrum
            fft_vals = np.fft.rfft(signal - np.mean(signal))
            power_spectrum = np.abs(fft_vals) ** 2
            freqs = np.fft.rfftfreq(n, d=1/sampling_rate if sampling_rate else 1)
            
            result['power_spectrum'] = power_spectrum
            
            if len(power_spectrum) > 1:
                # Find dominant frequencies (peaks)
                from scipy.signal import find_peaks
                peaks, properties = find_peaks(power_spectrum, height=np.max(power_spectrum)*0.1)
                
                if len(peaks) > 0:
                    # Sort by power
                    peak_powers = power_spectrum[peaks]
                    sorted_idx = np.argsort(peak_powers)[::-1]
                    
                    # Take top 5
                    top_peaks = peaks[sorted_idx[:5]]
                    result['dominant_frequencies'] = freqs[top_peaks].tolist()
                
                # Estimate bandwidth (frequency where power drops to half)
                max_power = np.max(power_spectrum)
                half_power_idx = np.where(power_spectrum > max_power/2)[0]
                if len(half_power_idx) > 1:
                    result['bandwidth'] = float(freqs[half_power_idx[-1]] - freqs[half_power_idx[0]])
                    
        except Exception as e:
            pass
        
        return result
    
    def _detect_regime_changes(self, signal: np.ndarray) -> Dict:
        """Detect regime changes using multiple methods"""
        result = {
            'n_regimes': 1,
            'change_points': []
        }
        
        if len(signal) < 30:
            return result
        
        try:
            # Method 1: CUSUM
            mean = np.mean(signal)
            cumsum = np.cumsum(signal - mean)
            
            if np.std(cumsum) > 0:
                # Normalize
                cumsum_norm = cumsum / np.std(cumsum)
                
                # Find significant change points
                threshold = 3.0
                changes = []
                
                for i in range(1, len(cumsum_norm)):
                    if abs(cumsum_norm[i] - cumsum_norm[i-1]) > threshold:
                        changes.append(i)
                
                # Method 2: Rolling statistics
                window = max(10, len(signal) // 20)
                if len(signal) > window * 2:
                    rolling_mean = np.convolve(signal, np.ones(window)/window, mode='valid')
                    rolling_std = np.array([
                        np.std(signal[i:i+window]) 
                        for i in range(len(signal)-window+1)
                    ])
                    
                    # Detect changes in rolling statistics
                    mean_changes = np.where(np.abs(np.diff(rolling_mean)) > 2*np.std(rolling_mean))[0]
                    std_changes = np.where(np.abs(np.diff(rolling_std)) > 2*np.std(rolling_std))[0]
                    
                    changes.extend(mean_changes.tolist())
                    changes.extend(std_changes.tolist())
                
                # Deduplicate and sort
                changes = sorted(set(changes))
                
                # Merge nearby changes
                merged = []
                min_distance = max(5, len(signal) // 50)
                
                for change in changes:
                    if not merged or change - merged[-1] > min_distance:
                        merged.append(change)
                
                result['change_points'] = merged
                result['n_regimes'] = len(merged) + 1
                
        except Exception as e:
            pass
        
        return result
    
    def _classify_signal(self, 
                         signal: np.ndarray,
                         stationarity: Dict,
                         spectral: Dict,
                         continuity: Dict) -> Dict:
        """Classify signal type"""
        result = {
            'signal_class': SignalClass.STOCHASTIC,
            'complexity': 0.5,
            'lyapunov': None
        }
        
        # Check for periodicity
        if len(spectral['dominant_frequencies']) > 0:
            dominant = spectral['dominant_frequencies'][0]
            
            # Check if signal is purely periodic
            if len(spectral['dominant_frequencies']) == 1:
                result['signal_class'] = SignalClass.PERIODIC
                result['complexity'] = 0.2
            elif len(spectral['dominant_frequencies']) <= 3:
                result['signal_class'] = SignalClass.QUASI_PERIODIC
                result['complexity'] = 0.4
        
        # Check for deterministic vs stochastic
        # Simple test: autocorrelation decay
        if len(signal) > 100:
            autocorr = np.correlate(signal - np.mean(signal), 
                                     signal - np.mean(signal), 
                                     mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            if len(autocorr) > 10:
                # Normalize
                if autocorr[0] != 0:
                    autocorr = autocorr / autocorr[0]
                    
                    # If autocorrelation persists, might be deterministic
                    if np.mean(np.abs(autocorr[10:20])) > 0.2:
                        result['signal_class'] = SignalClass.DETERMINISTIC
                        result['complexity'] = 0.6
        
        # Check for transient behavior
        if stationarity['is_stationary'] == False and len(spectral['dominant_frequencies']) == 0:
            result['signal_class'] = SignalClass.TRANSIENT
            result['complexity'] = 0.8
        
        # Adjust complexity based on entropy and stationarity
        result['complexity'] = np.clip(result['complexity'], 0, 1)
        
        return result
    
    def _compute_entropy(self, signal: np.ndarray) -> float:
        """Compute approximate entropy as complexity measure"""
        if len(signal) < 50:
            return 0.5
        
        try:
            # Normalize
            s = (signal - np.mean(signal)) / (np.std(signal) + 1e-12)
            
            # Approximate entropy parameters
            m = 2  # embedding dimension
            r = 0.2 * np.std(s)  # tolerance
            
            def _maxdist(xi, xj):
                return np.max(np.abs(xi - xj))
            
            def _phi(m):
                N = len(s)
                patterns = np.array([s[i:i+m] for i in range(N-m+1)])
                C = []
                
                for i in range(len(patterns)):
                    counts = 0
                    for j in range(len(patterns)):
                        if _maxdist(patterns[i], patterns[j]) <= r:
                            counts += 1
                    C.append(counts / (N-m+1))
                
                return np.mean(np.log(np.array(C) + 1e-12))
            
            # Compute approximate entropy
            apen = _phi(m) - _phi(m+1)
            
            # Normalize to 0-1
            apen_norm = 1 / (1 + np.exp(-apen))  # sigmoid
            
            return float(np.clip(apen_norm, 0, 1))
            
        except Exception:
            return 0.5
    
    def _build_feature_vector(self, *args) -> np.ndarray:
        """Build normalized feature vector for downstream stages"""
        # Collect all features
        features = []
        for arg in args:
            if isinstance(arg, (int, float, np.number)):
                features.append(float(arg))
            elif isinstance(arg, bool):
                features.append(1.0 if arg else 0.0)
            elif isinstance(arg, (list, np.ndarray)):
                features.extend([float(x) for x in arg[:5]])  # Limit to first 5
        
        # Ensure we have at least some features
        if len(features) < 10:
            features.extend([0.0] * (10 - len(features)))
        
        features = np.array(features[:20])  # Limit to 20 features
        
        # Normalize robustly
        if np.std(features) > 1e-12:
            features = (features - np.median(features)) / (np.std(features) + 1e-12)
            features = np.clip(features, -5, 5)  # Clip outliers
        
        return features
