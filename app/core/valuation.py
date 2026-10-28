"""
OpenValora - Valuation Module
Cálculo de projeção de valores para o imóvel avaliando, intervalos de confiança,
campo de arbítrio, arredondamento regulamentar e extrapolação.
"""

import numpy as np
from scipy import stats
from typing import Dict, Any, List, Tuple, Optional
from .models import SubjectProperty, ValuationResult, Variable
from .statistics import (
    TRANSFORMATIONS, apply_transformation, apply_inverse_transformation, safe_float
)

def evaluate_subject(
    subject: SubjectProperty,
    variables: List[Variable],
    dep_var: Variable,
    indep_vars: List[Variable],
    transf_dep: str,
    transf_indep: List[str],
    betas: np.ndarray,
    inv_xtx: np.ndarray,
    se: float,
    df_res: int,
    conf_level: float = 0.80,
    arbitrio_pct: float = 15.0,
    arredondamento_pct: float = 1.0,
    sample_bounds: Optional[Dict[str, Tuple[float, float]]] = None
) -> Tuple[ValuationResult, int, float]:
    """
    Avalia um imóvel sujeito/avaliando com a equação de regressão selecionada.
    Retorna o resultado da avaliação, o número de extrapolações e a maior razão de extrapolação.
    """
    # 1. Monta o vetor x0 transformado
    x0_transf = [1.0]  # Intercepto
    extrapolations = 0
    max_extrap_ratio = 1.0

    for i, var in enumerate(indep_vars):
        val = safe_float(subject.valores.get(var.nome, 0.0))
        t_code = transf_indep[i]

        # Checa extrapolação em relação à amostra
        if sample_bounds and var.nome in sample_bounds:
            min_val, max_val = sample_bounds[var.nome]
            if val < min_val:
                extrapolations += 1
                ratio = min_val / max(1e-6, val)
                if ratio > max_extrap_ratio:
                    max_extrap_ratio = ratio
            elif val > max_val:
                extrapolations += 1
                ratio = val / max(1e-6, max_val)
                if ratio > max_extrap_ratio:
                    max_extrap_ratio = ratio

        # Aplica a transformação matemática
        val_t = float(apply_transformation(t_code, np.array([val]))[0])
        x0_transf.append(val_t)

    x0 = np.array(x0_transf, dtype=float)

    # 2. Estimativa pontual no espaço transformado
    y0_transf = float(x0 @ betas) if not np.any(np.isnan(x0)) and not np.any(np.isnan(betas)) else 0.0

    # 3. Inversão para o espaço original do valor
    y0_orig = float(apply_inverse_transformation(transf_dep, np.array([y0_transf]))[0])
    if np.isnan(y0_orig) or y0_orig <= 0:
        y0_orig = 1.0

    # 4. Variância da estimativa da média e Intervalo de Confiança (80% NBR 14653)
    # var(y0_transf) = se^2 * (x0^T * (X^T X)^-1 * x0)
    try:
        var_est = float(se ** 2 * (x0 @ inv_xtx @ x0))
        if np.isnan(var_est) or var_est < 0:
            var_est = se ** 2
    except Exception:
        var_est = se ** 2

    se_est = float(np.sqrt(max(1e-12, var_est)))

    t_crit = float(stats.t.ppf(1.0 - (1.0 - conf_level) / 2.0, df_res))

    y0_transf_inf = y0_transf - t_crit * se_est
    y0_transf_sup = y0_transf + t_crit * se_est

    ic_inf = float(apply_inverse_transformation(transf_dep, np.array([y0_transf_inf]))[0])
    ic_sup = float(apply_inverse_transformation(transf_dep, np.array([y0_transf_sup]))[0])
    if np.isnan(ic_inf) or ic_inf <= 0:
        ic_inf = y0_orig * 0.85
    if np.isnan(ic_sup) or ic_sup <= 0:
        ic_sup = y0_orig * 1.15

    if ic_inf > ic_sup:
        ic_inf, ic_sup = ic_sup, ic_inf

    amplitude_pct = float(((ic_sup - ic_inf) / max(1e-6, y0_orig)) * 100.0)
    if np.isnan(amplitude_pct):
        amplitude_pct = 30.0

    # 5. Campo de Arbítrio (usualmente +/- 15% conforme item 8.2.1.6 da NBR 14653-2)
    arb_fator = arbitrio_pct / 100.0
    campo_min = float(y0_orig * (1.0 - arb_fator))
    campo_max = float(y0_orig * (1.0 + arb_fator))

    # 6. Arredondamento regulamentar (em até 1% conforme NBR 14653)
    # Se valor unitário alto, arredonda para número conveniente
    if y0_orig > 1000:
        step = 10.0 ** (int(np.log10(y0_orig)) - 2)
        valor_arred = round(y0_orig / step) * step
    elif y0_orig > 100:
        valor_arred = round(y0_orig)
    else:
        valor_arred = round(y0_orig, 2)

    # 7. Cálculo do Valor Total se unitário
    valor_total = None
    area_vinculada = None
    if dep_var.unitario:
        # Busca variável vinculada
        if 0 <= dep_var.var_vinculada < len(variables):
            var_area = variables[dep_var.var_vinculada]
            area_val = safe_float(subject.valores.get(var_area.nome, 0.0))
            if area_val > 0:
                area_vinculada = area_val
                valor_total = valor_arred * area_val
        else:
            # Tenta buscar por nome 'área'
            for v in variables:
                if "área" in v.nome.lower() or "area" in v.nome.lower():
                    area_val = safe_float(subject.valores.get(v.nome, 0.0))
                    if area_val > 0:
                        area_vinculada = area_val
                        valor_total = valor_arred * area_val
                        break

    # Grau de Precisão
    if amplitude_pct <= 30.0:
        grau_prec = "Grau III"
    elif amplitude_pct <= 40.0:
        grau_prec = "Grau II"
    elif amplitude_pct <= 50.0:
        grau_prec = "Grau I"
    else:
        grau_prec = "Não Enquadrado"

    result = ValuationResult(
        sujeito_id=subject.id,
        identificacao=subject.identificacao,
        valor_estimado_unitario=round(y0_orig, 2),
        valor_total_estimado=round(valor_total, 2) if valor_total else None,
        area_vinculada_valor=round(area_vinculada, 2) if area_vinculada else None,
        ic_inferior=round(ic_inf, 2),
        ic_superior=round(ic_sup, 2),
        amplitude_ic_pct=round(amplitude_pct, 2),
        campo_arbitrio_min=round(campo_min, 2),
        campo_arbitrio_max=round(campo_max, 2),
        valor_arredondado=round(valor_arred, 2),
        grau_precisao=grau_prec,
        grau_fundamentacao=""
    )

    return result, extrapolations, max_extrap_ratio
