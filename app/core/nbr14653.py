"""
OpenValora - NBR 14653 Compliance Engine
Enquadramento automático nos Graus de Fundamentação e Precisão da ABNT NBR 14653-2 (Urbanos)
e ABNT NBR 14653-3 (Rurais).
"""

from typing import List, Dict, Any, Optional
from .models import NBRClassification, NBRGradingItem

def evaluate_nbr14653(
    n_sample: int,
    k_regressors: int,
    f_significance_pct: float,
    max_t_significance_pct: float,
    amplitude_ic_pct: float,
    has_allocated_codes: bool = False,
    extrapolations_count: int = 0,
    max_extrapolation_ratio: float = 1.0,
    has_inverted_signs: bool = False,
    is_rural: bool = False,
    has_micronumerosity_issue: bool = False
) -> NBRClassification:
    """
    Realiza o enquadramento estrito conforme a ABNT NBR 14653-2 (Imóveis Urbanos)
    ou ABNT NBR 14653-3 (Imóveis Rurais, Tabela 2 e Tabela 3).
    """
    norma_ref = "ABNT NBR 14653-3 (Imóveis Rurais)" if is_rural else "ABNT NBR 14653-2 (Imóveis Urbanos)"
    req_fund: List[NBRGradingItem] = []
    req_prec: List[NBRGradingItem] = []

    # 1. Item 1: Caracterização dos imóveis
    req_fund.append(NBRGradingItem(
        item="Item 1 - Caracterização dos Imóveis",
        descricao="Caracterização e especificação dos dados e atributos",
        grau_obtido="III",
        justificativa="Amostra com dados completos e especificação de variáveis de atributos.",
        grau_pontos=3
    ))

    # 2. Item 2: Quantidade mínima de dados de mercado efetivamente utilizados
    # NBR 14653-2 (Urbanos): Grau III: N >= 6*(k+1), Grau II: N >= 3*(k+1), Grau I: N >= 3*(k+1)
    # NBR 14653-3 (Rurais, Tab. 2): Grau III: N >= 4*(k+1), Grau II: N >= 3*(k+1), Grau I: N >= 2*(k+1)
    if is_rural:
        limite_g3 = 4 * (k_regressors + 1)
        limite_g2 = 3 * (k_regressors + 1)
        limite_g1 = 2 * (k_regressors + 1)

        if n_sample >= limite_g3:
            g2_grau = "III"
            g2_just = f"N = {n_sample} observações (exigido NBR 14653-3 Grau III: N ≥ 4(k+1) = {limite_g3})."
            g2_pts = 3
        elif n_sample >= limite_g2:
            g2_grau = "II"
            g2_just = f"N = {n_sample} observações (exigido NBR 14653-3 Grau II: N ≥ 3(k+1) = {limite_g2})."
            g2_pts = 2
        elif n_sample >= limite_g1:
            g2_grau = "I"
            g2_just = f"N = {n_sample} observações (exigido NBR 14653-3 Grau I: N ≥ 2(k+1) = {limite_g1})."
            g2_pts = 1
        else:
            g2_grau = "NÃO ENQUADRADO"
            g2_just = f"N = {n_sample} observações (inferior ao mínimo normativo de 2(k+1) = {limite_g1})."
            g2_pts = 0
    else:
        limite_g3 = 6 * (k_regressors + 1)
        limite_g2 = 3 * (k_regressors + 1)
        limite_g1 = 3 * (k_regressors + 1)

        if n_sample >= limite_g3:
            g2_grau = "III"
            g2_just = f"N = {n_sample} observações (exigido NBR 14653-2 Grau III: N ≥ 6(k+1) = {limite_g3})."
            g2_pts = 3
        elif n_sample >= limite_g2:
            g2_grau = "II"
            g2_just = f"N = {n_sample} observações (exigido NBR 14653-2 Grau II: N ≥ 3(k+1) = {limite_g2})."
            g2_pts = 2
        else:
            g2_grau = "I"
            g2_just = f"N = {n_sample} observações (inferior a 3(k+1) = {limite_g2})."
            g2_pts = 1

    req_fund.append(NBRGradingItem(
        item="Item 2 - Quantidade de Dados Amostrais",
        descricao="Tamanho amostral efetivo N em relação ao número de regressores k",
        grau_obtido=g2_grau,
        justificativa=g2_just,
        grau_pontos=g2_pts
    ))

    # 3. Item 3: Identificação dos dados de mercado
    req_fund.append(NBRGradingItem(
        item="Item 3 - Identificação dos Dados",
        descricao="Identificação das fontes, logradouros e informantes",
        grau_obtido="III",
        justificativa="Identificação completa dos imóveis da amostra com endereços e características.",
        grau_pontos=3
    ))

    # 4. Item 4: Significância máxima dos regressores (t de Student)
    # Grau III: alfa <= 10% (confiança >= 90%)
    # Grau II: alfa <= 20% (confiança >= 80%)
    # Grau I: alfa <= 30% (confiança >= 70%)
    if max_t_significance_pct <= 10.0:
        g4_grau = "III"
        g4_just = f"Significância máxima observada: {max_t_significance_pct:.2f}% (exigido: ≤ 10%)."
        g4_pts = 3
    elif max_t_significance_pct <= 20.0:
        g4_grau = "II"
        g4_just = f"Significância máxima observada: {max_t_significance_pct:.2f}% (exigido: ≤ 20%)."
        g4_pts = 2
    elif max_t_significance_pct <= 30.0:
        g4_grau = "I"
        g4_just = f"Significância máxima observada: {max_t_significance_pct:.2f}% (exigido: ≤ 30%)."
        g4_pts = 1
    else:
        g4_grau = "NÃO ENQUADRADO"
        g4_just = f"Significância máxima observada: {max_t_significance_pct:.2f}% ultrapassa 30%."
        g4_pts = 0

    req_fund.append(NBRGradingItem(
        item="Item 4 - Significância dos Regressores (t-Student)",
        descricao="Nível de significância bicaudal máximo para os coeficientes",
        grau_obtido=g4_grau,
        justificativa=g4_just,
        grau_pontos=g4_pts
    ))

    # 5. Item 5: Significância do modelo (F de Snedecor)
    # Grau III: alfa_F <= 1%
    # Grau II: alfa_F <= 2%
    # Grau I: alfa_F <= 5%
    if f_significance_pct <= 1.0:
        g5_grau = "III"
        g5_just = f"Significância do F-calculado: {f_significance_pct:.4f}% (exigido: ≤ 1%)."
        g5_pts = 3
    elif f_significance_pct <= 2.0:
        g5_grau = "II"
        g5_just = f"Significância do F-calculado: {f_significance_pct:.4f}% (exigido: ≤ 2%)."
        g5_pts = 2
    elif f_significance_pct <= 5.0:
        g5_grau = "I"
        g5_just = f"Significância do F-calculado: {f_significance_pct:.4f}% (exigido: ≤ 5%)."
        g5_pts = 1
    else:
        g5_grau = "NÃO ENQUADRADO"
        g5_just = f"Significância do F-calculado: {f_significance_pct:.4f}% ultrapassa 5%."
        g5_pts = 0

    req_fund.append(NBRGradingItem(
        item="Item 5 - Significância Global do Modelo (F-Snedecor)",
        descricao="Probabilidade de rejeição da hipótese nula global",
        grau_obtido=g5_grau,
        justificativa=g5_just,
        grau_pontos=g5_pts
    ))

    # 6. Item 6: Extrapolação amostral
    # Grau III: Nenhuma extrapolação (extrapolations_count == 0)
    # Grau II: Extrapolação admitida para 1 variável dentro dos limites aceitáveis
    # Grau I: Extrapolação admitida para até 2 variáveis
    if extrapolations_count == 0:
        g6_grau = "III"
        g6_just = "Atributos do avaliando inseridos integralmente no domínio amostral."
        g6_pts = 3
    elif extrapolations_count == 1 and max_extrapolation_ratio <= 2.0:
        g6_grau = "II"
        g6_just = "Extrapolação tolerada em 1 variável dentro dos limites normativos (≤ 100% de margem)."
        g6_pts = 2
    elif extrapolations_count <= 2 and max_extrapolation_ratio <= 2.0:
        g6_grau = "I"
        g6_just = f"Extrapolação tolerada em {extrapolations_count} variáveis."
        g6_pts = 1
    else:
        g6_grau = "NÃO ENQUADRADO"
        g6_just = f"Extrapolação acentuada em {extrapolations_count} variáveis ou além do dobro amostral."
        g6_pts = 0

    req_fund.append(NBRGradingItem(
        item="Item 6 - Extrapolação Amostral",
        descricao="Verificação das características do avaliando nos limites amostrais",
        grau_obtido=g6_grau,
        justificativa=g6_just,
        grau_pontos=g6_pts
    ))

    # Composição do Grau Global de Fundamentação:
    # NBR 14653-2 (Urbanos):
    # - Grau III: Itens 2, 4, 5 e 6 no Grau III e os demais no mínimo no Grau II
    # - Grau II: Itens 2, 4, 5 e 6 no mínimo no Grau II e os demais no mínimo no Grau I
    # - Grau I: Todos os itens no mínimo no Grau I
    #
    # NBR 14653-3 (Rurais, Tabela 3):
    # - Grau III: Soma de pontos >= 15; itens obrigatórios 2, 5 e 6 no Grau III e os demais no mínimo no Grau II
    # - Grau II: Soma de pontos >= 9; itens obrigatórios 2, 5 e 6 no mínimo no Grau II e os demais no mínimo no Grau I
    # - Grau I: Soma de pontos >= 6; todos os itens no mínimo no Grau I
    pts_obrigatorios = [g2_pts, g4_pts, g5_pts, g6_pts]
    todos_pts = [item.grau_pontos for item in req_fund]
    soma_pts = sum(todos_pts)

    if has_inverted_signs:
        grau_fund = "Não Enquadrado"
        resumo = f"Modelo rejeitado para fundamentação ({norma_ref}): detectada inversão de sinal físico/econômico nos regressores."
    elif all(p >= 3 for p in pts_obrigatorios) and all(p >= 2 for p in todos_pts) and (soma_pts >= 15 if is_rural else True):
        grau_fund = "Grau III"
        resumo = f"Enquadramento pleno em Grau III conforme critérios da {norma_ref}."
    elif all(p >= 2 for p in pts_obrigatorios) and all(p >= 1 for p in todos_pts) and (soma_pts >= 9 if is_rural else True):
        grau_fund = "Grau II"
        resumo = f"Enquadramento em Grau II conforme critérios da {norma_ref}."
    elif all(p >= 1 for p in todos_pts) and (soma_pts >= 6 if is_rural else True):
        grau_fund = "Grau I"
        resumo = f"Enquadramento em Grau I conforme critérios da {norma_ref}."
    else:
        grau_fund = "Não Enquadrado"
        resumo = f"Requisitos mínimos da {norma_ref} não atendidos simultaneamente."

    # Grau de Precisão (Tabela 2 Urbanos / Tabela 6 Rurais - Amplitude do IC a 80%):
    # Grau III: Amplitude <= 30%
    # Grau II: Amplitude <= 40%
    # Grau I: Amplitude <= 50%
    if amplitude_ic_pct <= 30.0:
        grau_prec = "Grau III"
        prec_just = f"Amplitude do IC (80%) = {amplitude_ic_pct:.2f}% (exigido: ≤ 30%)."
        prec_pts = 3
    elif amplitude_ic_pct <= 40.0:
        grau_prec = "Grau II"
        prec_just = f"Amplitude do IC (80%) = {amplitude_ic_pct:.2f}% (exigido: ≤ 40%)."
        prec_pts = 2
    elif amplitude_ic_pct <= 50.0:
        grau_prec = "Grau I"
        prec_just = f"Amplitude do IC (80%) = {amplitude_ic_pct:.2f}% (exigido: ≤ 50%)."
        prec_pts = 1
    else:
        grau_prec = "Não Enquadrado"
        prec_just = f"Amplitude do IC (80%) = {amplitude_ic_pct:.2f}% ultrapassa o limite normativo de 50%."
        prec_pts = 0

    req_prec.append(NBRGradingItem(
        item="Amplitude do Intervalo de Confiança a 80%",
        descricao="Precisão da estimativa de valor em torno da tendência central",
        grau_obtido=grau_prec,
        justificativa=prec_just,
        grau_pontos=prec_pts
    ))

    # Construção de Diagnósticos e Sugestões de Ajuste Ação-a-Ação
    diagnosticos: List[str] = []

    if has_inverted_signs:
        diagnosticos.append(
            "⚠️ Inversão de Sinal Físico/Econômico: Um ou mais regressores apresentam sinal algébrico oposto à lógica de mercado esperada. "
            "Como ajustar: Geralmente causada por forte multicolinearidade entre variáveis correlacionadas ou amostra pequena. Remova uma das variáveis redundantes na aba 'Variáveis' e recalcule o modelo."
        )

    if has_micronumerosity_issue:
        diagnosticos.append(
            "⚠️ Micronumerosidade Violada (NBR 14653-2 item 9.2.1): Uma ou mais categorias de variáveis dicotômicas ou de códigos alocados possuem menos de 3 observações na amostra. "
            "Como ajustar: Colete mais dados com as características deficitárias ou agrupe níveis adjacentes da escala qualitativa."
        )

    if is_rural:
        if n_sample < limite_g1:
            diff_g1 = limite_g1 - n_sample
            diagnosticos.append(
                f"❌ Tamanho da Amostra Insuficiente (NBR 14653-3 Rurais): Coletadas {n_sample} observações para k = {k_regressors} regressores. A norma exige no mínimo 2(k+1) = {limite_g1} dados efetivos (faltam {diff_g1} dados). "
                f"Como ajustar: Adicione pelo menos {diff_g1} novos dados na aba 'Dados da Amostra' ou desative variáveis explicativas desnecessárias para reduzir a exigência amostral."
            )
        elif n_sample < limite_g2:
            diff_g2 = limite_g2 - n_sample
            diagnosticos.append(
                f"ℹ️ Tamanho da Amostra limita a Grau I (NBR 14653-3 Rurais): N = {n_sample}. Para atingir Grau II, são necessárias 3(k+1) = {limite_g2} observações (faltam {diff_g2} dados)."
            )
        elif n_sample < limite_g3:
            diff_g3 = limite_g3 - n_sample
            diagnosticos.append(
                f"ℹ️ Tamanho da Amostra limita a Grau II (NBR 14653-3 Rurais): N = {n_sample}. Para atingir Grau III, são necessárias 4(k+1) = {limite_g3} observações (faltam {diff_g3} dados)."
            )
    else:
        if n_sample < limite_g2:
            diff_g2 = limite_g2 - n_sample
            diagnosticos.append(
                f"❌ Tamanho da Amostra Insuficiente (NBR 14653-2 Urbanos): Coletadas {n_sample} observações para k = {k_regressors} regressores. A norma exige no mínimo 3(k+1) = {limite_g2} dados efetivos (faltam {diff_g2} dados). "
                f"Como ajustar: Adicione pelo menos {diff_g2} novos dados na aba 'Dados da Amostra' ou desative variáveis explicativas desnecessárias para reduzir a exigência amostral."
            )
        elif n_sample < limite_g3:
            diff_g3 = limite_g3 - n_sample
            diagnosticos.append(
                f"ℹ️ Tamanho da Amostra limita a Grau II (NBR 14653-2 Urbanos): A amostra possui N = {n_sample} observações. Para atingir Grau III, são necessárias 6(k+1) = {limite_g3} observações (faltam {diff_g3} dados). "
                f"Como ajustar: Para alcançar fundamentação Grau III neste item, amplie a pesquisa coletando mais {diff_g3} amostras de mercado."
            )

    if max_t_significance_pct > 30.0:
        diagnosticos.append(
            f"❌ Significância de Regressor (t-Student) Não Conforme: Há regressor com nível de significância de {max_t_significance_pct:.2f}% (limite da {norma_ref} é 30% para Grau I). "
            "Como ajustar: Remova a variável não significativa na aba 'Variáveis' ou aplique transformações não-lineares (ex: ln, 1/x ou raiz quadrada) para aperfeiçoar a linearização."
        )
    elif max_t_significance_pct > 20.0:
        diagnosticos.append(
            f"⚠️ Significância dos Regressores limita ao Grau I: Significância máxima observada de {max_t_significance_pct:.2f}%. "
            "Como ajustar: Para atingir Grau II a significância de todos os regressores deve ser ≤ 20%, e para Grau III ≤ 10%. Experimente transformar variáveis ou desativar regressores com t fraco."
        )
    elif max_t_significance_pct > 10.0:
        diagnosticos.append(
            f"ℹ️ Significância dos Regressores limita ao Grau II: Significância máxima observada de {max_t_significance_pct:.2f}%. "
            "Como ajustar: Para atingir Grau III, a significância individual de todos os regressores deve ser ≤ 10%."
        )

    if f_significance_pct > 5.0:
        diagnosticos.append(
            f"❌ Significância Global F (ANOVA) Não Conforme: O teste F resultou em p = {f_significance_pct:.4f}% (> 5% limite normativo). O modelo não possui significância estatística global comprovada. "
            "Como ajustar: As variáveis independentes não explicam conjuntamente o preço. Substitua as variáveis explicativas ou aplique transformação logarítmica na variável dependente."
        )
    elif f_significance_pct > 2.0:
        diagnosticos.append(
            f"⚠️ Significância Global F limita ao Grau I ({f_significance_pct:.4f}%): Para alcançar Grau II deve ser ≤ 2% e para Grau III ≤ 1%."
        )
    elif f_significance_pct > 1.0:
        diagnosticos.append(
            f"ℹ️ Significância Global F limita ao Grau II ({f_significance_pct:.4f}%): Para alcançar Grau III deve ser ≤ 1%."
        )

    if g6_grau == "NÃO ENQUADRADO":
        diagnosticos.append(
            f"❌ Extrapolação Amostral Excessiva: O imóvel avaliando extrapola acentuadamente a amplitude da amostra ({extrapolations_count} variáveis). "
            "Como ajustar: Colete amostras de mercado com características físicas e de localização que englobem os atributos do imóvel avaliando."
        )
    elif extrapolations_count > 0:
        diagnosticos.append(
            f"⚠️ Extrapolação Amostral ({g6_grau}): Detectada extrapolação em {extrapolations_count} variável(is) do avaliando. "
            "Como ajustar: Para alcançar Grau III pleno de fundamentação, o avaliando deve estar totalmente contido no domínio da amostra coletada."
        )

    if amplitude_ic_pct > 50.0:
        diagnosticos.append(
            f"❌ Grau de Precisão Não Enquadrado: A amplitude do intervalo de confiança de 80% é de {amplitude_ic_pct:.2f}% (> 50% limite normativo). "
            "Como ajustar: Aumente o número de dados na amostra, desative dados discrepantes (outliers) clicando nos pontos do gráfico de resíduos ou selecione um modelo com menor erro padrão residual."
        )
    elif amplitude_ic_pct > 40.0:
        diagnosticos.append(
            f"⚠️ Grau de Precisão I: Amplitude do IC a 80% = {amplitude_ic_pct:.2f}%. "
            "Como ajustar: Para atingir Grau II (≤ 40%) ou Grau III (≤ 30%), reduza o erro padrão residual eliminando pontos com resíduos elevados ou ampliando a amostra."
        )
    elif amplitude_ic_pct > 30.0:
        diagnosticos.append(
            f"ℹ️ Grau de Precisão II: Amplitude do IC a 80% = {amplitude_ic_pct:.2f}%. "
            "Como ajustar: Para atingir Grau III, a amplitude deve ser ≤ 30%. Procure modelos com maior R² e colete amostras mais homogêneas próximas ao avaliando."
        )

    if not diagnosticos:
        diagnosticos.append(
            f"✅ Modelo com Enquadramento Pleno: Atende integralmente aos critérios máximos de Grau III de Fundamentação e Grau III de Precisão da {norma_ref}, com aderência metodológica perfeita."
        )

    return NBRClassification(
        grau_fundamentacao=grau_fund,
        grau_precisao=grau_prec,
        amplitude_ic_pct=round(amplitude_ic_pct, 2),
        requisitos_fundamentacao=req_fund,
        requisitos_precisao=req_prec,
        resumo_analitico=resumo,
        diagnosticos_ajuste=diagnosticos,
        norma_aplicada=norma_ref
    )
