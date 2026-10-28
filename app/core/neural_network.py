"""
OpenValora - Artificial Neural Network Module (RNA)
Módulo de Redes Neurais Artificiais (Perceptron Multicamadas / MLP)
para avaliação de imóveis e inferência estatística avançada.
"""

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List, Optional

from .models import Project, Variable, SubjectProperty
from .statistics import safe_float

def train_rna(
    project: Project,
    hidden_layer_sizes: tuple = (8,),
    activation: str = "logistic",  # 'logistic' (sigmoide), 'relu', 'tanh'
    max_iter: int = 1500,
    learning_rate_init: float = 0.01,
    solver: str = "lbfgs",  # 'lbfgs' (quasi-Newton / LM style) ou 'adam'
    bagging: bool = False,
    n_bags: int = 5
) -> Dict[str, Any]:
    """
    Treina a Rede Neural Artificial (RNA) com os dados da amostra e avalia os imóveis avaliandos.
    """
    amostra = [item for item in project.dados if item.habilitado]
    if len(amostra) < 5:
        raise ValueError("Amostra insuficiente para treinamento de RNA (mínimo de 5 dados).")

    # Localiza variável dependente
    dep_var = None
    for v in project.variaveis:
        if v.classificacao == 7 and v.habilitada:
            dep_var = v
            break
    if not dep_var:
        num_vars = [v for v in project.variaveis if v.tipo == 1 and v.habilitada]
        if not num_vars:
            raise ValueError("Nenhuma variável dependente ou numérica habilitada para a Rede Neural.")
        dep_var = num_vars[-1]

    # Variáveis de entrada
    input_vars = [
        v for v in project.variaveis
        if v.tipo == 1 and v.habilitada and v.id != dep_var.id and v.nome != dep_var.nome
    ]
    if not input_vars:
        raise ValueError("Nenhuma variável de entrada numérica habilitada para a RNA.")

    # Matrizes com parsing defensivo (safe_float)
    X_raw = np.array([
        [safe_float(item.valores.get(v.nome, 0.0)) for v in input_vars]
        for item in amostra
    ], dtype=float)

    y_raw = np.array([
        safe_float(item.valores.get(dep_var.nome, 0.0))
        for item in amostra
    ], dtype=float)

    # Padronização de escala
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()

    X_scaled = scaler_x.fit_transform(X_raw)
    y_scaled = scaler_y.fit_transform(y_raw.reshape(-1, 1)).ravel()

    models = []
    if bagging and n_bags > 1:
        n_samples = len(X_scaled)
        for _ in range(n_bags):
            # Bootstrap resample
            boot_indices = np.random.choice(n_samples, size=n_samples, replace=True)
            X_b, y_b = X_scaled[boot_indices], y_scaled[boot_indices]
            
            mlp = MLPRegressor(
                hidden_layer_sizes=hidden_layer_sizes,
                activation=activation,
                solver=solver,
                max_iter=max_iter,
                learning_rate_init=learning_rate_init,
                random_state=None
            )
            mlp.fit(X_b, y_b)
            models.append(mlp)
    else:
        mlp = MLPRegressor(
            hidden_layer_sizes=hidden_layer_sizes,
            activation=activation,
            solver=solver,
            max_iter=max_iter,
            learning_rate_init=learning_rate_init,
            random_state=42
        )
        mlp.fit(X_scaled, y_scaled)
        models.append(mlp)

    # Predição na amostra
    preds_scaled = np.mean([m.predict(X_scaled) for m in models], axis=0)
    y_pred = scaler_y.inverse_transform(preds_scaled.reshape(-1, 1)).ravel()

    # Métricas
    residuals = y_raw - y_pred
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_raw - np.mean(y_raw)) ** 2)
    r2 = float(max(0.0, 1.0 - ss_res / ss_tot)) if ss_tot > 0 else 0.0
    r = float(np.sqrt(r2))
    rmse = float(np.sqrt(np.mean(residuals ** 2)))
    mae = float(np.mean(np.abs(residuals)))
    mape = float(np.mean(np.abs(residuals) / np.maximum(1e-6, np.abs(y_raw))) * 100.0)

    # Tabela detalhada de resíduos da amostra
    amostra_residuos = []
    for i in range(len(amostra)):
        obs = float(y_raw[i])
        est = float(y_pred[i])
        res = float(residuals[i])
        res_rel = float(abs(res) / max(1e-6, obs) * 100.0)
        amostra_residuos.append({
            "index": amostra[i].id,
            "observado": round(obs, 2),
            "estimado": round(est, 2),
            "residuo": round(res, 2),
            "residuo_relativo_pct": round(res_rel, 2)
        })

    # Predição para os imóveis avaliandos
    proj_results = []
    for proj in project.projecoes:
        x_proj_raw = np.array([
            [safe_float(proj.valores.get(v.nome, 0.0)) for v in input_vars]
        ], dtype=float)
        x_proj_scaled = scaler_x.transform(x_proj_raw)
        p_scaled = np.mean([m.predict(x_proj_scaled) for m in models], axis=0)
        y_proj = float(scaler_y.inverse_transform(p_scaled.reshape(-1, 1))[0, 0])
        y_proj = max(0.01, y_proj)

        # Arredondamento regulamentar NBR 14653
        if y_proj > 1000:
            step = 10.0 ** (int(np.log10(y_proj)) - 2)
            valor_arred = round(y_proj / step) * step
        elif y_proj > 100:
            valor_arred = round(y_proj)
        else:
            valor_arred = round(y_proj, 2)

        # Se valor unitário e tem área vinculada
        valor_total = None
        if dep_var.unitario:
            if 0 <= dep_var.var_vinculada < len(project.variaveis):
                var_area = project.variaveis[dep_var.var_vinculada]
                area_v = safe_float(proj.valores.get(var_area.nome, 0.0))
                if area_v > 0:
                    valor_total = valor_arred * area_v
            else:
                for v in project.variaveis:
                    if "área" in v.nome.lower() or "area" in v.nome.lower():
                        area_v = safe_float(proj.valores.get(v.nome, 0.0))
                        if area_v > 0:
                            valor_total = valor_arred * area_v
                            break

        proj_results.append({
            "sujeito_id": proj.id,
            "identificacao": proj.identificacao,
            "valor_estimado_unitario": round(y_proj, 2),
            "valor_arredondado": round(valor_arred, 2),
            "valor_total_estimado": round(valor_total, 2) if valor_total else None,
            "campo_arbitrio_min": round(y_proj * 0.85, 2),
            "campo_arbitrio_max": round(y_proj * 1.15, 2)
        })

    # Loss curve (se disponível do primeiro modelo)
    loss_curve = [float(l) for l in getattr(models[0], "loss_curve_", [])]

    resultado = {
        "arquitetura": f"Camada Oculta: {hidden_layer_sizes}, Ativação: {activation}, Solver: {solver}",
        "r": round(r, 5),
        "r2": round(r2, 5),
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "mape_pct": round(mape, 2),
        "n_iter": int(models[0].n_iter_) if hasattr(models[0], "n_iter_") else max_iter,
        "loss_curve": loss_curve,
        "amostra_residuos": amostra_residuos,
        "projecoes": proj_results
    }

    return resultado
