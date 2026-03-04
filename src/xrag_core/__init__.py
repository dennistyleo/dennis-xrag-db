"""
XRAG Core - 5-Stage Axiom Generation Engine
Extreme Reliability Axiom Generator for mathematical model discovery
"""

from .xrag_engine import XRAGEngine, XRAGResult
from .stage1_characterization import ProblemCharacterizer, SignalFeatures
from .stage2_generation import PathwayGenerator, Hypothesis, HypothesisFamily
from .stage3_feasibility import FeasibilityAssessor, FeasibilityResult
from .stage4_calibration import ParameterCalibrator, CalibratedModel
from .stage5_explainability import ExplainabilityEngine, AuditReport

__version__ = "2.0.0"
__all__ = [
    'XRAGEngine', 'XRAGResult',
    'ProblemCharacterizer', 'SignalFeatures',
    'PathwayGenerator', 'Hypothesis', 'HypothesisFamily',
    'FeasibilityAssessor', 'FeasibilityResult',
    'ParameterCalibrator', 'CalibratedModel',
    'ExplainabilityEngine', 'AuditReport'
]
