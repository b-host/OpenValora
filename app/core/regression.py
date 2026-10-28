"""
OpenValora - Regression Engine
Motor de Regressão Linear Múltipla com linearização de variáveis,
busca combinatória otimizada em dois estágios, estimação por MQ e MV,
diagnóstico de resíduos e enquadramento ABNT NBR 14653 (Urbanos e Rurais).
"""

import itertools
import numpy as np
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional

from .models import (
    Project, Variable, SampleItem, RegressionModelResult,
    RegressorResult, AnovaTable, ResidualItem, NormalityResult,
    CalculationOptions
)
from .statistics import (
    TRANSFORMATIONS, apply_transformation, apply_inverse_transformation,
    is_transformation_valid, calculate_durbin_watson, calculate_normality,
    calculate_breusch_pagan, calculate_vif, check_sign_inversion, safe_float
)
from .nbr14653 import evaluate_nbr14653
from .valuation import evaluate_subject

def run_regression_search(project: Project) -> List[RegressionModelResult]:
    """
    Executa a busca de modelos de regressão linear para o projeto.
    Utiliza triagem vetorial em dois estágios para máxima performance.
    """
    # 1. Filtra dados habilitados
    amostra = [item for item in project.dados if item.habilitado]
    if len(amostra) < 4:
        raise ValueError("Amostra insuficiente. Mínimo de 4 observações habilitadas necessárias.")

    # 2. Localiza a variável dependente
    dep_var: Optional[Variable] = None
    for v in project.variaveis:
        if v.classificacao == 7 and v.habilitada:
            dep_var = v
            break
    if not dep_var:
        # Pega a última numérica habilitada
        num_vars = [v for v in project.variaveis if v.tipo == 1 and v.habilitada]
        if not num_vars:
            raise ValueError("Nenhuma variável numérica habilitada encontrada.")
        dep_var = num_vars[-1]

    # 3. Variáveis independentes numéricas habilitadas
    indep_vars = [
        v for v in project.variaveis
        if v.tipo == 1 and v.habilitada and v.id != dep_var.id and v.nome != dep_var.nome
    ]
    if not indep_vars:
        # Fallback: ativa variáveis numéricas não-dependentes disponíveis
        fallbacks = [
            v for v in project.variaveis
            if v.tipo == 1 and v.id != dep_var.id and v.nome != dep_var.nome
        ]
        if fallbacks:
            for v in fallbacks:
                v.habilitada = True
            indep_vars = fallbacks
        else:
            raise ValueError("Nenhuma variável independente numérica encontrada.")

    # Deduplicação defensiva de variáveis independentes
    seen_indep_names = set()
    unique_indep = []
    for v in indep_vars:
        if v.nome not in seen_indep_names:
            seen_indep_names.add(v.nome)
            unique_indep.append(v)
    indep_vars = unique_indep

    # 4. Extrai matrizes originais com parsing defensivo (safe_float)
    n_sample = len(amostra)
    y_raw = np.array([safe_float(item.valores.get(dep_var.nome, 0.0)) for item in amostra], dtype=float)
    
    X_raw_cols = []
    for var in indep_vars:
        col = np.array([safe_float(item.valores.get(var.nome, 0.0)) for item in amostra], dtype=float)
        X_raw_cols.append(col)
    X_raw = np.column_stack(X_raw_cols)

    # 4.1 Checagem de micronumerosidade para variáveis qualitativas e dicotômicas (NBR 14653-2 item 9.2.1)
    micronumerosity_warnings: List[str] = []
    has_micronumerosity = False
    for j, var in enumerate(indep_vars):
        if var.classificacao in (2, 4):  # Qualitativa (Códigos Alocados) ou Dicotômica
            col_vals = X_raw[:, j]
            uniques, counts = np.unique(col_vals, return_counts=True)
            for u_val, cnt in zip(uniques, counts):
                if cnt < 3:
                    has_micronumerosity = True
                    u_str = f"{u_val:g}" if isinstance(u_val, (int, float)) else str(u_val)
                    micronumerosity_warnings.append(
                        f"⚠️ Micronumerosidade Violada na variável '{var.nome}': o código/categoria {u_str} possui apenas {cnt} dado(s) na amostra (mínimo de 3 exigido pelo item 9.2.1 da NBR 14653-2)."
                    )

    # 5. Determina transformações válidas
    opcoes = project.opcoes
    t_candidates = opcoes.transformacoes if opcoes.transformacoes else ["x", "1/x", "ln(x)"]

    # Dependente: suporta x e ln(x) se y > 0
    dep_transf_candidates = ["x"]
    if "ln(x)" in t_candidates and np.all(y_raw > 0):
        dep_transf_candidates.append("ln(x)")

    # Independentes: verifica quais transformações são válidas para cada coluna
    # Códigos Alocados e Dicotômicas mantêm exclusivamente transformação linear direta (x) conforme NBR 14653
    indep_transf_map = []
    for j, var in enumerate(indep_vars):
        col_vals = X_raw[:, j]
        valid_t = []
        if var.classificacao in (2, 4):
            valid_t = ["x"]
        else:
            for t_code in t_candidates:
                if is_transformation_valid(t_code, col_vals):
                    valid_t.append(t_code)
            if not valid_t:
                valid_t = ["x"]
        indep_transf_map.append(valid_t)

    # 6. Gera combinações de modelos
    candidate_specs = []
    if opcoes.metodo == "simplificado":
        # Método simplificado (greedy): para cada regressor escolhe a transformação que mais correlaciona com y_transf
        for dep_t in dep_transf_candidates:
            y_t = apply_transformation(dep_t, y_raw)
            best_indep_t = []
            for j, var in enumerate(indep_vars):
                best_t = "x"
                best_corr = -1.0
                for t_code in indep_transf_map[j]:
                    x_t = apply_transformation(t_code, X_raw[:, j])
                    std_x = np.std(x_t)
                    if std_x > 0:
                        corr = abs(float(np.corrcoef(x_t, y_t)[0, 1]))
                        if corr > best_corr:
                            best_corr = corr
                            best_t = t_code
                best_indep_t.append(best_t)
            candidate_specs.append((dep_t, tuple(best_indep_t)))
            # Inclui também o modelo puramente linear de referência
            linear_indep = tuple(["x"] * len(indep_vars))
            if linear_indep != tuple(best_indep_t):
                candidate_specs.append((dep_t, linear_indep))
    else:
        # Método todas as regressões possíveis (combinação de transformações)
        indep_combinations = list(itertools.islice(itertools.product(*indep_transf_map), 600))
        for dep_t in dep_transf_candidates:
            for indep_comb in indep_combinations:
                candidate_specs.append((dep_t, indep_comb))

    # Bounds da amostra para controle de extrapolação
    sample_bounds = {}
    for j, var in enumerate(indep_vars):
        sample_bounds[var.nome] = (float(np.min(X_raw[:, j])), float(np.max(X_raw[:, j])))

    mean_y = float(np.mean(y_raw))
    mean_xs = [float(np.mean(X_raw[:, j])) for j in range(len(indep_vars))]
    ss_tot_orig = float(np.sum((y_raw - mean_y) ** 2))
    k_reg = len(indep_vars)
    df_res = n_sample - k_reg - 1
    if df_res <= 0:
        raise ValueError(f"Amostra insuficiente ({n_sample} observações) para {k_reg} regressores. Necessário N > k + 1.")

    # ==================== ESTÁGIO 1: TRIAGEM RÁPIDA VETORIZADA ====================
    scored_candidates = []

    for spec_idx, (dep_t, indep_t_tuple) in enumerate(candidate_specs):
        try:
            y_t = apply_transformation(dep_t, y_raw)
            ss_tot_t = float(np.sum((y_t - np.mean(y_t)) ** 2))
            if ss_tot_t <= 0:
                continue

            X_t_cols = [
                apply_transformation(indep_t_tuple[j], X_raw[:, j])
                for j in range(k_reg)
            ]
            X_t = np.column_stack(X_t_cols)
            X_design = np.column_stack([np.ones(n_sample), X_t])

            xtx = X_design.T @ X_design
            cond = np.linalg.cond(xtx)
            if cond > 1e12:
                continue

            inv_xtx = np.linalg.inv(xtx)
            betas = inv_xtx @ (X_design.T @ y_t)

            y_t_pred = X_design @ betas
            res_t = y_t - y_t_pred
            ss_res_t = float(np.sum(res_t ** 2))
            r2_t = float(max(0.0, 1.0 - ss_res_t / ss_tot_t))

            # Predição e resíduos no espaço original
            y_orig_pred = apply_inverse_transformation(dep_t, y_t_pred)
            y_orig_pred = np.maximum(0.01, y_orig_pred)
            res_orig = y_raw - y_orig_pred
            ss_res_orig = float(np.sum(res_orig ** 2))
            r2_orig = float(max(0.0, 1.0 - ss_res_orig / ss_tot_orig)) if ss_tot_orig > 0 else 0.0

            # Checagem de inversão de sinal físico-econômico
            has_inv = False
            for j, var in enumerate(indep_vars):
                if var.crescimento != -1:
                    bj = float(betas[j + 1])
                    t_code = indep_t_tuple[j]
                    if check_sign_inversion(dep_t, t_code, bj, mean_xs[j], mean_y, var.crescimento):
                        has_inv = True
                        break

            # ANOVA F aproximado
            ms_reg_t = (ss_tot_t - ss_res_t) / k_reg
            ms_res_t = ss_res_t / df_res
            f_calc = float(ms_reg_t / max(1e-12, ms_res_t))

            # Ordenação conforme critérios normativos e estatísticos:
            # - se 'estimativa': ordena por R² original
            # - se 'regressao': ordena por R² transformado
            # - modelos com inversão de sinal são penalizados
            inversion_penalty = -10.0 if has_inv else 0.0
            primary = r2_orig if opcoes.selecao_modelo == "estimativa" else r2_t
            sort_score = (inversion_penalty, primary, f_calc)

            scored_candidates.append({
                "sort_score": sort_score,
                "spec_idx": spec_idx,
                "dep_t": dep_t,
                "indep_t_tuple": indep_t_tuple,
                "X_t": X_t,
                "X_design": X_design,
                "inv_xtx": inv_xtx,
                "betas": betas,
                "y_t": y_t,
                "y_t_pred": y_t_pred,
                "res_t": res_t,
                "ss_res_t": ss_res_t,
                "ss_tot_t": ss_tot_t,
                "r2_t": r2_t,
                "y_orig_pred": y_orig_pred,
                "res_orig": res_orig,
                "ss_res_orig": ss_res_orig,
                "r2_orig": r2_orig,
                "has_inv": has_inv,
                "f_calc": f_calc,
                "ms_reg_t": ms_reg_t,
                "ms_res_t": ms_res_t
            })
        except Exception:
            continue

    if not scored_candidates:
        raise ValueError("Nenhum modelo válido pôde ser calculado com as opções selecionadas.")

    # Ordena pelo score
    scored_candidates.sort(key=lambda item: item["sort_score"], reverse=True)

    # Mantém apenas os TOP modelos (conforme limite_modelos) para cálculo detalhado completo
    limite = min(len(scored_candidates), max(10, project.opcoes.limite_modelos))
    top_candidates = scored_candidates[:limite]

    # ==================== ESTÁGIO 2: CÁLCULO DETALHADO DOS TOP MODELOS ====================
    is_rural = (
        project.metadata.tipologia == 7
        or "rural" in (project.metadata.descricao or "").lower()
        or "rural" in (project.metadata.subtitulo_relatorio or "").lower()
        or "rural" in (project.metadata.titulo_relatorio or "").lower()
    )
    is_mv = (opcoes.estimador == "mv")

    models_evaluated: List[RegressionModelResult] = []

    for rank_idx, item in enumerate(top_candidates):
        dep_t = item["dep_t"]
        indep_t_tuple = item["indep_t_tuple"]
        X_t = item["X_t"]
        X_design = item["X_design"]
        inv_xtx = item["inv_xtx"]
        betas = item["betas"]
        y_t_pred = item["y_t_pred"]
        res_t = item["res_t"]
        ss_res_t = item["ss_res_t"]
        ss_tot_t = item["ss_tot_t"]
        r2_t = item["r2_t"]
        y_orig_pred = item["y_orig_pred"]
        res_orig = item["res_orig"]
        ss_res_orig = item["ss_res_orig"]
        r2_orig = item["r2_orig"]
        f_calc = item["f_calc"]
        ms_reg_t = item["ms_reg_t"]
        ms_res_t = item["ms_res_t"]

        r_t = float(np.sqrt(r2_t))
        r2_adj_t = float(1.0 - (ss_res_t / df_res) / (ss_tot_t / (n_sample - 1)))
        r_orig = float(np.sqrt(r2_orig))

        # Estimação por Mínimos Quadrados (MQ) ou Máxima Verossimilhança (MV)
        if is_mv:
            sigma2 = ss_res_t / n_sample
            se_t = float(np.sqrt(sigma2))
            cov_beta = sigma2 * inv_xtx
            se_orig = float(np.sqrt(ss_res_orig / n_sample))
        else:
            sigma2 = ss_res_t / df_res
            se_t = float(np.sqrt(sigma2))
            cov_beta = sigma2 * inv_xtx
            se_orig = float(np.sqrt(ss_res_orig / df_res))

        se_betas = np.sqrt(np.maximum(1e-12, np.diag(cov_beta)))
        t_calcs = betas / se_betas
        p_val_t = 2.0 * (1.0 - stats.t.cdf(np.abs(t_calcs), df_res if not is_mv else n_sample))
        sig_t_pct = p_val_t * 100.0

        # ANOVA
        df_reg = k_reg
        df_tot = n_sample - 1
        ss_reg_t = ss_tot_t - ss_res_t
        p_val_f = float(1.0 - stats.f.cdf(f_calc, df_reg, df_res))
        sig_f_pct = float(p_val_f * 100.0)

        anova = AnovaTable(
            ss_reg=round(float(ss_reg_t), 4),
            ss_res=round(float(ss_res_t), 4),
            ss_tot=round(float(ss_tot_t), 4),
            df_reg=df_reg,
            df_res=df_res,
            df_tot=df_tot,
            ms_reg=round(float(ms_reg_t), 4),
            ms_res=round(float(ms_res_t), 4),
            f_calc=round(f_calc, 3),
            p_valor_f=p_val_f,
            significancia_f_pct=round(sig_f_pct, 4)
        )

        # VIF (Fator de Inflação da Variância)
        vifs = calculate_vif(X_t)

        # Regressores detalhados
        regressores_info: List[RegressorResult] = []
        has_inversion = False
        max_t_sig = 0.0

        for j, var in enumerate(indep_vars):
            bj = float(betas[j + 1])
            se_bj = float(se_betas[j + 1])
            t_j = float(t_calcs[j + 1])
            p_j = float(p_val_t[j + 1])
            sig_j = float(sig_t_pct[j + 1])
            if sig_j > max_t_sig:
                max_t_sig = sig_j

            t_code = indep_t_tuple[j]
            mean_x = mean_xs[j]

            # Elasticidade média = (dy/dx) * (x_bar / y_bar)
            deriv_x = TRANSFORMATIONS[t_code]["deriv"](max(1e-6, abs(mean_x)))
            deriv_y = TRANSFORMATIONS[dep_t]["deriv"](max(1e-6, abs(mean_y)))
            if deriv_y != 0 and mean_y != 0:
                dy_dx = bj * deriv_x / deriv_y
                elast = float(dy_dx * mean_x / mean_y)
            else:
                elast = 0.0

            # Inversão de sinal
            is_inv = check_sign_inversion(
                dep_t, t_code, bj, mean_x, mean_y, var.crescimento
            )
            if is_inv:
                has_inversion = True

            expr = TRANSFORMATIONS[t_code]["formula"](var.nome)
            regressores_info.append(RegressorResult(
                nome_original=var.nome,
                nome_exibicao=var.nome,
                transformacao_codigo=t_code,
                expressao=expr,
                coeficiente=round(bj, 6),
                erro_padrao=round(se_bj, 6),
                t_calc=round(t_j, 3),
                p_valor=round(p_j, 5),
                significancia_pct=round(sig_j, 2),
                elasticidade_media=round(elast, 4),
                crescimento_esperado=var.crescimento,
                sinal_invertido=is_inv,
                vif=round(vifs[j], 2)
            ))

        # Resíduos e pontos de influência (Cook e Leverage)
        hat_diag = np.diag(X_design @ inv_xtx @ X_design.T)
        residuos_info: List[ResidualItem] = []
        
        for i in range(n_sample):
            obs = float(y_raw[i])
            est = float(y_orig_pred[i])
            res_ord = float(res_orig[i])
            res_rel = float(abs(res_ord) / max(1e-6, obs) * 100.0)
            
            hii = float(hat_diag[i])
            e_t_i = float(res_t[i])
            denom = se_t * np.sqrt(max(1e-6, 1.0 - hii))
            r_stud = float(e_t_i / denom) if denom > 0 else 0.0
            r_padr = float(e_t_i / se_t) if se_t > 0 else 0.0

            if 1.0 - hii > 1e-6:
                d_cook = float((r_stud ** 2 / (k_reg + 1)) * (hii / (1.0 - hii)))
            else:
                d_cook = 0.0

            is_out = bool(abs(r_stud) > 2.0 or res_rel > 40.0)
            is_inf = bool(d_cook > 1.0 or (hii > 2.0 * (k_reg + 1) / n_sample))

            residuos_info.append(ResidualItem(
                index=amostra[i].id,
                observado=round(obs, 2),
                estimado=round(est, 2),
                residuo_ordinario=round(res_ord, 2),
                residuo_padronizado=round(r_padr, 3),
                residuo_studentizado=round(r_stud, 3),
                residuo_relativo_pct=round(res_rel, 2),
                distancia_cook=round(d_cook, 4),
                leverage=round(hii, 4),
                is_outlier=is_out,
                is_influente=is_inf
            ))

        # Durbin-Watson
        dw, dw_status = calculate_durbin_watson(res_t)

        # Normalidade dos resíduos
        norm_res = calculate_normality(res_t)

        # Homocedasticidade Breusch-Pagan
        bp_pval, is_homo = calculate_breusch_pagan(res_t, X_design)

        # Equação textual formatada
        intercepto = float(betas[0])
        eq_dep_str = TRANSFORMATIONS[dep_t]["formula"](dep_var.nome)
        terms = [f"{intercepto:.4f}"]
        for reg in regressores_info:
            sinal = "+" if reg.coeficiente >= 0 else "-"
            terms.append(f"{sinal} {abs(reg.coeficiente):.4f} * {reg.expressao}")
        equacao_str = f"{eq_dep_str} = " + " ".join(terms)

        # Avaliação de sujeitos / Projeções para este modelo
        proj_results = []
        total_extrap = 0
        max_extrap_r = 1.0

        for proj in project.projecoes:
            val_res, extrap, r_extrap = evaluate_subject(
                subject=proj,
                variables=project.variaveis,
                dep_var=dep_var,
                indep_vars=indep_vars,
                transf_dep=dep_t,
                transf_indep=list(indep_t_tuple),
                betas=betas,
                inv_xtx=inv_xtx,
                se=se_t,
                df_res=df_res,
                conf_level=opcoes.nivel_confianca,
                arbitrio_pct=opcoes.campo_arbitrio_pct,
                arredondamento_pct=opcoes.arredondamento_pct,
                sample_bounds=sample_bounds
            )
            proj_results.append(val_res)
            if extrap > total_extrap:
                total_extrap = extrap
            if r_extrap > max_extrap_r:
                max_extrap_r = r_extrap

        # Enquadramento ABNT NBR 14653
        amp_ic = proj_results[0].amplitude_ic_pct if proj_results else 30.0
        nbr_class = evaluate_nbr14653(
            n_sample=n_sample,
            k_regressors=k_reg,
            f_significance_pct=sig_f_pct,
            max_t_significance_pct=max_t_sig,
            amplitude_ic_pct=amp_ic,
            extrapolations_count=total_extrap,
            max_extrapolation_ratio=max_extrap_r,
            has_inverted_signs=has_inversion,
            is_rural=is_rural,
            has_micronumerosity_issue=has_micronumerosity
        )

        for pr in proj_results:
            pr.grau_fundamentacao = nbr_class.grau_fundamentacao

        # Diagnósticos técnicos e orientações de ajuste normativo
        diag_list = list(nbr_class.diagnosticos_ajuste) if nbr_class else []
        norm_obj = NormalityResult(**norm_res)

        # Micronumerosidade
        for w in micronumerosity_warnings:
            if w not in diag_list:
                diag_list.append(w)

        # Checagem de Multicolinearidade (VIF)
        altos_vif = [r for r in regressores_info if r.vif > 10.0]
        if altos_vif:
            nomes_vif = ", ".join([f"'{r.nome_exibicao}' (VIF={r.vif:.1f})" for r in altos_vif])
            diag_list.append(
                f"⚠️ Multicolinearidade Severa Detectada: {nomes_vif}. "
                "Como ajustar: Variáveis com VIF > 10 contêm forte dependência linear mútua. Remova uma das variáveis redundantes ou agregue-as em um índice ponderado."
            )

        # Checagem de Normalidade dos Resíduos
        if not norm_obj.atende_normalidade:
            diag_list.append(
                "⚠️ Desvio de Normalidade nos Resíduos: Os testes estatísticos indicam dispersão residual não estritamente gaussiana. "
                "Como ajustar: Aplique transformação logarítmica (ln) na variável dependente para estabilizar a variância."
            )

        # Checagem de Outliers
        outliers_res = [r for r in residuos_info if r.is_outlier]
        if outliers_res:
            out_ids = ", ".join([f"#{r.index}" for r in outliers_res[:6]])
            if len(outliers_res) > 6:
                out_ids += f" e mais {len(outliers_res) - 6}"
            diag_list.append(
                f"⚠️ Presença de Outliers ({len(outliers_res)} observações): Amostras {out_ids} possuem resíduo padronizado |r| > 2. "
                "Como ajustar: Clique nos pontos no gráfico de dispersão/resíduos para localizá-los diretamente na tabela de dados e avalie se houve erro de coleta ou se devem ser desabilitados temporariamente."
            )

        # Checagem de Durbin-Watson (Autocorrelação)
        if dw < 1.3 or dw > 2.7:
            diag_list.append(
                f"ℹ️ Autocorrelação Residual (Durbin-Watson = {dw:.2f}): Afastado do valor ideal (DW ≈ 2.0). "
                "Como ajustar: Se a amostra tiver componente temporal ou espacial pronunciado, considere inclusão de variável de localização ou data de evento."
            )

        model_obj = RegressionModelResult(
            id=rank_idx + 1,
            equacao_texto=equacao_str,
            transformacao_dep=dep_t,
            var_dep_nome=dep_var.nome,
            regressores=regressores_info,
            intercepto=round(intercepto, 6),
            r=round(r_t, 5),
            r2=round(r2_t, 5),
            r2_ajustado=round(r2_adj_t, 5),
            r2_original=round(r2_orig, 5),
            r_original=round(r_orig, 5),
            erro_padrao=round(se_t, 5),
            erro_padrao_original=round(se_orig, 2),
            durbin_watson=round(dw, 4),
            durbin_watson_status=dw_status,
            anova=anova,
            residuos=residuos_info,
            normalidade=norm_obj,
            breusch_pagan_pvalor=round(bp_pval, 4) if bp_pval else None,
            homocedastico=is_homo,
            inversao_detectada=has_inversion,
            nbr=nbr_class,
            projecoes=proj_results,
            diagnosticos_tecnicos=diag_list
        )
        models_evaluated.append(model_obj)

    return models_evaluated
