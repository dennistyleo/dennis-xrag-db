"""
XRAG World - 世界模型和因果推理模塊
讓XRAG能夠理解因果關係、進行反事實推理和預測干預結果
"""

from .models.world_model import WorldModel, LatentWorldModel
from .models.causal_graph import CausalGraph, StructuralCausalModel
from .causal.discovery import CausalDiscovery, PCAlgorithm, FCIAlgorithm
from .causal.inference import CausalInference, DoOperator, CounterfactualEngine
from .reasoning.intervention import InterventionEngine, InterventionResult
from .reasoning.counterfactual import CounterfactualReasoner
from .utils.scm_builder import SCMBuilder, LinearSCM, NonLinearSCM

__version__ = "1.0.0"
__all__ = [
    'WorldModel', 'LatentWorldModel',
    'CausalGraph', 'StructuralCausalModel',
    'CausalDiscovery', 'PCAlgorithm', 'FCIAlgorithm',
    'CausalInference', 'DoOperator', 'CounterfactualEngine',
    'InterventionEngine', 'InterventionResult',
    'CounterfactualReasoner',
    'SCMBuilder', 'LinearSCM', 'NonLinearSCM'
]
