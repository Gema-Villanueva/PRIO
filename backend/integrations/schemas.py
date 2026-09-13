from dataclasses import dataclass


# Resultado común para cualquier proveedor de modelos.
@dataclass(frozen=True)
class GenerationResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    provider: str
    model: str
    estimated_cost_usd: float