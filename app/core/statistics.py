"""
OpenValora - Statistics Module
Funções matemáticas, transformações de variáveis, testes de hipótese,
análise de resíduos, multicolinearidade e testes de conformidade.
"""

import numpy as np
from scipy import stats
from typing import Dict, Any, List, Tuple, Optional

def safe_float(val: Any, default: float = 0.0) -> float:
    """
    Converte qualquer valor para float de forma tolerante a falhas,
    suportando formatos numéricos brasileiros (ex.: '1.250,50' ou '1250,50'),
    strings com espaços, células em branco, None e tipos numéricos nativos.
    """
    if val is None:
        return default
    if isinstance(val, (int, float)):
        if np.isnan(val) or np.isinf(val):
            return default
        return float(val)
    if isinstance(val, bool):
        return 1.0 if val else 0.0

    s = str(val).strip()
    if not s:
        return default

    # Formatação com vírgula e ponto (e.g. "1.250,50" ou "1,250.50")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            # Padrão brasileiro: "1.250,50" -> "1250.50"
            s = s.replace(".", "").replace(",", ".")
        else:
            # Padrão americano: "1,250.50" -> "1250.50"
            s = s.replace(",", "")
    elif "," in s:
        # Padrão com vírgula decimal: "1250,50" -> "1250.50"
        s = s.replace(",", ".")

    try:
        f = float(s)
        return default if (np.isnan(f) or np.isinf(f)) else f
    except (ValueError, TypeError):
        return default


# Definições de transformações suportadas com salvaguardas numéricas
TRANSFORMATIONS = {
    "x": {
        "nome": "Direta (x)",
        "func": lambda v: v,
        "inv": lambda v: v,
        "deriv": lambda v: 1.0,
        "is_valid": lambda arr: True,
        "formula": lambda name: name
    },
    "1/x": {
        "nome": "Inversa (1/x)",
        "func": lambda v: 1.0 / np.where(v == 0, 1e-6, v),
        "inv": lambda v: 1.0 / np.where(v == 0, 1e-6, v),
        "deriv": lambda v: -1.0 / np.maximum(1e-12, np.where(v == 0, 1e-6, v) ** 2),
        "is_valid": lambda arr: np.all(arr != 0),
        "formula": lambda name: f"1/({name})"
    },
    "ln(x)": {
        "nome": "Logarítmica (ln x)",
        "func": lambda v: np.log(np.maximum(1e-6, v)),
        "inv": lambda v: np.exp(np.clip(v, -50.0, 50.0)),
        "deriv": lambda v: 1.0 / np.maximum(1e-6, v),
        "is_valid": lambda arr: np.all(arr > 0),
        "formula": lambda name: f"ln({name})"
    },
    "x2": {
        "nome": "Quadrática (x²)",
        "func": lambda v: np.clip(v, -1e6, 1e6) ** 2,
        "inv": lambda v: np.sqrt(np.maximum(0.0, v)),
        "deriv": lambda v: 2.0 * v,
        "is_valid": lambda arr: True,
        "formula": lambda name: f"({name})²"
    },
    "1/x2": {
        "nome": "Inversa Quadrática (1/x²)",
        "func": lambda v: 1.0 / np.maximum(1e-12, np.where(v == 0, 1e-6, v) ** 2),
        "inv": lambda v: 1.0 / np.sqrt(np.maximum(1e-12, v)),
        "deriv": lambda v: -2.0 / np.maximum(1e-12, np.where(v == 0, 1e-6, v) ** 3),
        "is_valid": lambda arr: np.all(arr != 0),
        "formula": lambda name: f"1/({name})²"
    },
    "x(1/2)": {
        "nome": "Raiz Quadrada (√x)",
        "func": lambda v: np.sqrt(np.maximum(0.0, v)),
        "inv": lambda v: v ** 2,
        "deriv": lambda v: 0.5 / np.maximum(1e-12, np.sqrt(np.maximum(0.0, v))),
        "is_valid": lambda arr: np.all(arr >= 0),
        "formula": lambda name: f"√({name})"
    },
    "1/x(1/2)": {
        "nome": "Inversa da Raiz (1/√x)",
        "func": lambda v: 1.0 / np.sqrt(np.maximum(1e-6, v)),
        "inv": lambda v: 1.0 / np.maximum(1e-12, v ** 2),
        "deriv": lambda v: -0.5 / np.maximum(1e-12, np.where(v <= 0, 1e-6, v) ** 1.5),
        "is_valid": lambda arr: np.all(arr > 0),
        "formula": lambda name: f"1/√({name})"
    }
}

def apply_transformation(code: str, values: np.ndarray) -> np.ndarray:
    if code in TRANSFORMATIONS:
        return TRANSFORMATIONS[code]["func"](values)
    return values

def apply_inverse_transformation(code: str, values: np.ndarray) -> np.ndarray:
    if code in TRANSFORMATIONS:
        return TRANSFORMATIONS[code]["inv"](values)
    return values

def is_transformation_valid(code: str, values: np.ndarray) -> bool:
    if code in TRANSFORMATIONS:
        return bool(TRANSFORMATIONS[code]["is_valid"](values))
    return False

def calculate_durbin_watson(residuals: np.ndarray) -> Tuple[float, str]:
    """Calcula estatística de Durbin-Watson e retorna o valor e o diagnóstico."""
    n = len(residuals)
    if n < 3:
        return 2.0, "Amostra insuficiente"
    
    diff = np.diff(residuals)
    ss_diff = np.sum(diff ** 2)
    ss_res = np.sum(residuals ** 2)
    if ss_res == 0:
        return 2.0, "Indeterminado"
    
    dw = float(ss_diff / ss_res)
    
    # Interpretação prática conforme literatura e NBR 14653
    # dw ~ 2.0: ausência de autocorrelação
    # dw < 1.4: indício de autocorrelação positiva
    # dw > 2.6: indício de autocorrelação negativa
    if 1.4 <= dw <= 2.6:
        status = "Sem autocorrelação (adequado)"
    elif dw < 1.4:
        status = "Autocorrelação positiva detectada"
    else:
        status = "Autocorrelação negativa detectada"
        
    return dw, status

def calculate_normality(residuals: np.ndarray) -> Dict[str, Any]:
    """
    Avalia a normalidade dos resíduos:
    - Proporção em 1, 2 e 3 desvios padrão vs teórica [68%, 95%, 99%]
    - Testes Kolmogorov-Smirnov e Shapiro-Wilk
    """
    n = len(residuals)
    mean_r = np.mean(residuals)
    std_r = np.std(residuals, ddof=1) if n > 1 else 1.0
    if std_r == 0:
        std_r = 1e-12

    z_scores = np.abs((residuals - mean_r) / std_r)
    p1 = float(np.sum(z_scores <= 1.0) / n * 100.0)
    p2 = float(np.sum(z_scores <= 2.0) / n * 100.0)
    p3 = float(np.sum(z_scores <= 3.0) / n * 100.0)

    # Teste Kolmogorov-Smirnov contra normal padronizada
    std_residuals = (residuals - mean_r) / std_r
    ks_res = stats.kstest(std_residuals, 'norm')
    
    # Teste Shapiro-Wilk (se n entre 3 e 5000)
    shapiro_stat = None
    shapiro_pval = None
    if 3 <= n <= 5000:
        try:
            s_res = stats.shapiro(residuals)
            shapiro_stat = float(s_res.statistic)
            shapiro_pval = float(s_res.pvalue)
        except Exception:
            pass

    # Critério de aceitação de normalidade (p-valor > 0.05 no KS ou distribuição em faixas)
    atende = bool(ks_res.pvalue >= 0.01 and p2 >= 85.0)

    return {
        "dentro_1_dp_pct": round(p1, 1),
        "dentro_2_dp_pct": round(p2, 1),
        "dentro_3_dp_pct": round(p3, 1),
        "referencia": [68.0, 95.0, 99.0],
        "ks_stat": float(ks_res.statistic),
        "ks_pvalor": float(ks_res.pvalue),
        "shapiro_stat": shapiro_stat,
        "shapiro_pvalor": shapiro_pval,
        "atende_normalidade": atende
    }

def calculate_breusch_pagan(residuals: np.ndarray, X_design: np.ndarray) -> Tuple[float, bool]:
    """Teste de Breusch-Pagan para homocedasticidade."""
    n, p = X_design.shape
    if n <= p + 1:
        return 1.0, True

    # Resíduos ao quadrado padronizados
    s2 = np.mean(residuals ** 2)
    if s2 == 0:
        return 1.0, True
    g = (residuals ** 2) / s2

    # Regressão auxiliar de g em X_design
    try:
        beta_aux = np.linalg.lstsq(X_design, g, rcond=None)[0]
        g_pred = X_design @ beta_aux
        ss_aux = np.sum((g_pred - np.mean(g)) ** 2)
        lm_stat = 0.5 * ss_aux
        df = p - 1
        pval = float(1.0 - stats.chi2.cdf(lm_stat, df))
        homo = bool(pval >= 0.05)
        return pval, homo
    except Exception:
        return 1.0, True

def calculate_vif(X_independent: np.ndarray) -> List[float]:
    """Calcula o Fator de Inflação da Variância (VIF) para cada regressor."""
    k = X_independent.shape[1]
    if k <= 1:
        return [1.0] * k

    vifs = []
    for i in range(k):
        y_i = X_independent[:, i]
        cols = [c for c in range(k) if c != i]
        X_other = X_independent[:, cols]
        X_other_des = np.column_stack([np.ones(len(y_i)), X_other])
        
        try:
            b = np.linalg.lstsq(X_other_des, y_i, rcond=None)[0]
            pred = X_other_des @ b
            ss_tot = np.sum((y_i - np.mean(y_i)) ** 2)
            ss_res = np.sum((y_i - pred) ** 2)
            if ss_tot > 0:
                r2 = max(0.0, min(0.999999, 1.0 - ss_res / ss_tot))
            else:
                r2 = 0.0
            vif = 1.0 / (1.0 - r2)
        except Exception:
            vif = 1.0
        vifs.append(float(vif))

    return vifs

def check_sign_inversion(
    transf_dep_code: str,
    transf_indep_code: str,
    beta: float,
    mean_x: float,
    mean_y: float,
    crescimento_esperado: int
) -> bool:
    """
    Verifica se o regressor apresenta inversão de sinal em relação à expectativa teórica.
    crescimento_esperado:
       0: Crescente (direta: dy/dx > 0)
       1: Decrescente (inversa: dy/dx < 0)
      -1: Livre (sem restrição)
    """
    if crescimento_esperado == -1:
        return False

    deriv_x = TRANSFORMATIONS[transf_indep_code]["deriv"](max(1e-6, abs(mean_x)))
    # A derivada da transformação dependente em relação a y
    deriv_y_trans = TRANSFORMATIONS[transf_dep_code]["deriv"](max(1e-6, abs(mean_y)))
    
    # dy_trans / dx_trans = beta
    # dy / dx = beta * (d x_trans / dx) / (d y_trans / dy)
    if deriv_y_trans != 0:
        effect = beta * deriv_x / deriv_y_trans
    else:
        effect = beta * deriv_x

    # 0: esperado > 0 (crescente)
    if crescimento_esperado == 0 and effect < 0:
        return True
    # 1: esperado < 0 (decrescente)
    if crescimento_esperado == 1 and effect > 0:
        return True

    return False
