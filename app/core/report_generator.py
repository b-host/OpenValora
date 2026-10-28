"""
OpenValora - Report Generator Module
Gerador de Relatórios e Laudos de Avaliação Imobiliária Completos em conformidade com a ABNT NBR 14653-1 e NBR 14653-2.
Suporta personalização completa, logotipo personalizado, inclusão integral da tabela de dados amostrais e geração direta em PDF / Impressão.
"""

from typing import Dict, Any, Optional, List
import math
import base64
from pathlib import Path
import numpy as np
from .models import Project, RegressionModelResult
from .statistics import safe_float

def get_valora_logo_base64() -> str:
    """Retorna o logotipo oficial do OpenValora em base64 para renderização estática offline e em PDFs."""
    p = Path(__file__).parent.parent / "static" / "img" / "logo.png"
    if p.exists():
        try:
            return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"
        except Exception:
            pass
    return "/static/img/logo.png"

def format_number(val: Any, decimals: int = 2) -> str:
    """Formata valores numéricos para o padrão brasileiro (milhar com ponto, decimal com vírgula)."""
    if val is None or val == "":
        return "-"
    try:
        f = safe_float(val)
        if math.isnan(f) or math.isinf(f):
            return "-"
        formatted = f"{f:,.{decimals}f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return str(val)

def generate_laudo_html(project: Project, model: Optional[RegressionModelResult] = None, autoprint: bool = False) -> str:
    """Gera o HTML do Relatório / Laudo de Avaliação Completo conforme NBR 14653."""
    if not model:
        if project.modelos_calculados:
            idx = min(project.modelo_selecionado_idx, len(project.modelos_calculados) - 1)
            model = project.modelos_calculados[idx]
        else:
            return """
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head><meta charset="UTF-8"><title>Relatório de Avaliação - OpenValora</title></head>
            <body style="font-family: sans-serif; padding: 40px; text-align: center; color: #475569;">
                <div style="background: #fef2f2; border: 1px solid #f87171; border-radius: 8px; padding: 25px; max-width: 600px; margin: 40px auto;">
                    <h2 style="color: #dc2626; margin-top: 0;">Nenhum Modelo Calculado</h2>
                    <p>Para emitir o Relatório de Avaliação Imobiliária completo com as exigências da NBR 14653, execute o cálculo de regressão na aba <strong>Regressão Linear</strong>.</p>
                </div>
            </body>
            </html>
            """

    m = project.metadata
    nbr = model.nbr

    # Variável dependente
    dep_var_nome = model.var_dep_nome
    is_unitario = False
    for v in project.variaveis:
        if v.nome == dep_var_nome and v.unitario:
            is_unitario = True
            break
    unit_suffix = "/m²" if is_unitario else ""
    unit_label = "Valor Unitário Arredondado" if is_unitario else "Valor Avaliado Arredondado"

    # Imóvel avaliando (projeção principal)
    proj_info = model.projecoes[0] if model.projecoes else None

    # Logo personalizada ou padrão oficial do OpenValora
    logo_src = m.logo_base64.strip() if (getattr(m, "logo_base64", None) and m.logo_base64.strip()) else get_valora_logo_base64()
    logo_html = f"""
    <div style="margin-right: 20px; flex-shrink: 0;">
        <img src="{logo_src}" alt="Logomarca" style="max-height: 75px; max-width: 220px; object-fit: contain;">
    </div>
    """

    # Tabela de regressores HTML
    reg_rows = ""
    for r in model.regressores:
        inv_badge = "<span style='color:#dc2626;font-weight:bold;'> (Invertido)</span>" if r.sinal_invertido else ""
        t_color = "#16a34a" if r.significancia_pct <= 10.0 else ("#d97706" if r.significancia_pct <= 20.0 else "#dc2626")
        reg_rows += f"""
        <tr>
            <td style="padding: 6px 10px; border: 1px solid #cbd5e1; font-weight: 500;">{r.nome_exibicao}</td>
            <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: center; font-family: monospace;">{r.transformacao_codigo}</td>
            <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right; font-family: monospace;">{format_number(r.coeficiente, 6)}</td>
            <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right;">{format_number(r.erro_padrao, 6)}</td>
            <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right; font-weight: bold;">{format_number(r.t_calc, 3)}</td>
            <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right; font-weight: bold; color: {t_color};">{format_number(r.significancia_pct, 2)}%{inv_badge}</td>
            <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right;">{format_number(r.elasticidade_media, 4)}</td>
            <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right; font-weight: 500;">{format_number(r.vif, 2)}</td>
        </tr>
        """

    # Tabela ANOVA HTML
    anova = model.anova
    anova_html = f"""
    <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px;">
        <thead style="background-color: #f1f5f9;">
            <tr>
                <th style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: left;">Fonte de Variação</th>
                <th style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: center;">GL</th>
                <th style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right;">Soma dos Quadrados (SQ)</th>
                <th style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right;">Quadrado Médio (QM)</th>
                <th style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right;">F Calculado</th>
                <th style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right;">Significância do Teste F</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; font-weight: 600;">Regressão</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: center;">{anova.df_reg}</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right;">{format_number(anova.ss_reg, 4)}</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right;">{format_number(anova.ms_reg, 4)}</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right; font-weight: bold; color: #0284c7;">{format_number(anova.f_calc, 3)}</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right; font-weight: bold; color: #16a34a;">{format_number(anova.significancia_f_pct, 4)}%</td>
            </tr>
            <tr>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; font-weight: 600;">Resíduos</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: center;">{anova.df_res}</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right;">{format_number(anova.ss_res, 4)}</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right;">{format_number(anova.ms_res, 4)}</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: center; color: #94a3b8;" colspan="2">-</td>
            </tr>
            <tr style="background-color: #f8fafc; font-weight: bold;">
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1;">Total</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: center;">{anova.df_tot}</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: right;">{format_number(anova.ss_tot, 4)}</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: center; color: #94a3b8;" colspan="3">-</td>
            </tr>
        </tbody>
    </table>
    """

    # Enquadramento NBR itens
    nbr_fund_rows = ""
    if nbr:
        for it in nbr.requisitos_fundamentacao:
            cor_grau = "#16a34a" if it.grau_obtido == "III" else ("#0284c7" if it.grau_obtido == "II" else "#d97706")
            nbr_fund_rows += f"""
            <tr>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; font-weight: 500;">{it.item}</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; text-align: center; font-weight: bold; color: {cor_grau};">{it.grau_obtido}</td>
                <td style="padding: 6px 10px; border: 1px solid #cbd5e1; font-size: 11px; color: #475569;">{it.justificativa}</td>
            </tr>
            """

    # Mapa de resíduos por índice amostral
    res_map = {res.index: res for res in model.residuos} if model.residuos else {}

    # Variáveis ativas
    vars_ativas = [v for v in project.variaveis if v.habilitada]

    # Construção da TABELA COMPLETA DE DADOS AMOSTRAIS (Exigência do Usuário)
    # Cabeçalho da tabela de dados
    dados_th = "<th style='padding: 6px 8px; border: 1px solid #cbd5e1; text-align: center;'>Nº</th>"
    dados_th += "<th style='padding: 6px 8px; border: 1px solid #cbd5e1; text-align: center;'>Status</th>"
    for v in vars_ativas:
        dep_badge = " (Dep)" if v.nome == dep_var_nome else ""
        dados_th += f"<th style='padding: 6px 8px; border: 1px solid #cbd5e1; text-align: right; font-size: 11px;'>{v.nome}{dep_badge}</th>"
    dados_th += "<th style='padding: 6px 8px; border: 1px solid #cbd5e1; text-align: right; font-size: 11px;'>Estimado</th>"
    dados_th += "<th style='padding: 6px 8px; border: 1px solid #cbd5e1; text-align: right; font-size: 11px;'>Res. Padronizado</th>"

    # Linhas de dados da amostra
    dados_rows = ""
    valid_count = 0
    disabled_count = 0
    outlier_count = 0

    for idx, item in enumerate(project.dados):
        is_hab = item.habilitado
        is_out = item.outlier
        if not is_hab:
            disabled_count += 1
            status_text = "<span style='color:#64748b; font-size:10px; font-weight:bold;'>Desabilitado</span>"
            row_bg = "#f1f5f9; opacity: 0.75;"
        elif is_out:
            outlier_count += 1
            status_text = "<span style='color:#dc2626; font-size:10px; font-weight:bold;'>Outlier</span>"
            row_bg = "#fef2f2;"
        else:
            valid_count += 1
            status_text = "<span style='color:#16a34a; font-size:10px; font-weight:bold;'>Utilizado</span>"
            row_bg = "#ffffff;" if idx % 2 == 0 else "#f8fafc;"

        res_info = res_map.get(item.id)
        est_val_str = format_number(res_info.estimado, 2) if res_info else "-"
        res_padr_str = format_number(res_info.residuo_padronizado, 3) if res_info else "-"
        
        # Alerta se resíduo padronizado for maior que 2 DP
        res_style = "font-weight:bold; color:#dc2626;" if (res_info and abs(res_info.residuo_padronizado) > 2.0) else ""

        dados_rows += f"<tr style='background-color: {row_bg}'>"
        dados_rows += f"<td style='padding: 5px 8px; border: 1px solid #cbd5e1; text-align: center; font-weight: bold;'>{item.id}</td>"
        dados_rows += f"<td style='padding: 5px 8px; border: 1px solid #cbd5e1; text-align: center;'>{status_text}</td>"

        for v in vars_ativas:
            raw_v = item.valores.get(v.nome, "")
            formatted_v = format_number(raw_v, v.decimais) if v.tipo == 1 else str(raw_v)
            dados_rows += f"<td style='padding: 5px 8px; border: 1px solid #cbd5e1; text-align: right; font-size: 11px;'>{formatted_v}</td>"

        dados_rows += f"<td style='padding: 5px 8px; border: 1px solid #cbd5e1; text-align: right; font-size: 11px; font-family: monospace;'>{est_val_str}</td>"
        dados_rows += f"<td style='padding: 5px 8px; border: 1px solid #cbd5e1; text-align: right; font-size: 11px; font-family: monospace; {res_style}'>{res_padr_str}</td>"
        dados_rows += "</tr>"

    # Estatísticas Descritivas Básicas da Amostra (Média, DP, Min, Max)
    desc_rows = ""
    for v in vars_ativas:
        if v.tipo == 1:
            vals = []
            for item in project.dados:
                if item.habilitado and not item.outlier:
                    v_raw = item.valores.get(v.nome, None)
                    if v_raw is not None and str(v_raw).strip() != "":
                        vals.append(safe_float(v_raw))
            if vals:
                arr = np.array(vals)
                desc_rows += f"""
                <tr>
                    <td style="padding: 4px 8px; border: 1px solid #cbd5e1; font-weight: 500;">{v.nome}</td>
                    <td style="padding: 4px 8px; border: 1px solid #cbd5e1; text-align: right;">{len(arr)}</td>
                    <td style="padding: 4px 8px; border: 1px solid #cbd5e1; text-align: right;">{format_number(np.mean(arr), v.decimais)}</td>
                    <td style="padding: 4px 8px; border: 1px solid #cbd5e1; text-align: right;">{format_number(np.std(arr, ddof=1) if len(arr) > 1 else 0.0, v.decimais)}</td>
                    <td style="padding: 4px 8px; border: 1px solid #cbd5e1; text-align: right;">{format_number(np.min(arr), v.decimais)}</td>
                    <td style="padding: 4px 8px; border: 1px solid #cbd5e1; text-align: right;">{format_number(np.max(arr), v.decimais)}</td>
                </tr>
                """

    # Bloco de projeções dos imóveis avaliandos
    projecoes_html = ""
    if model.projecoes:
        for p in model.projecoes:
            vt_bloco = ""
            if p.valor_total_estimado:
                vt_bloco = f"""
                <div style="background-color: #f0fdf4; border: 2px solid #22c55e; border-radius: 8px; padding: 16px; margin-top: 15px;">
                    <div style="font-size: 13px; color: #166534; font-weight: 700; text-transform: uppercase;">Valor Total Avaliado do Imóvel</div>
                    <div style="font-size: 26px; color: #15803d; font-weight: 800; margin: 4px 0;">R$ {format_number(p.valor_total_estimado, 2)}</div>
                    <div style="font-size: 12px; color: #166534;">Área avaliada: {format_number(p.area_vinculada_valor, 2)} m² | Valor unitário arredondado: R$ {format_number(p.valor_arredondado, 2)}{unit_suffix}</div>
                </div>
                """
            projecoes_html += f"""
            <div class="section-box" style="margin-bottom: 12px;">
                <div class="grid-2">
                    <div>
                        <div><strong>Identificação:</strong> {p.identificacao}</div>
                        <div><strong>Estimativa Pontual:</strong> R$ {format_number(p.valor_estimado_unitario, 2)}{unit_suffix}</div>
                        <div><strong>{unit_label}:</strong> R$ {format_number(p.valor_arredondado, 2)}{unit_suffix}</div>
                    </div>
                    <div>
                        <div><strong>Intervalo de Confiança (80%):</strong> [R$ {format_number(p.ic_inferior, 2)} a R$ {format_number(p.ic_superior, 2)}]</div>
                        <div><strong>Amplitude do IC:</strong> {format_number(p.amplitude_ic_pct, 2)}% ({p.grau_precisao})</div>
                        <div><strong>Campo de Arbítrio (±15%):</strong> [R$ {format_number(p.campo_arbitrio_min, 2)} a R$ {format_number(p.campo_arbitrio_max, 2)}]</div>
                    </div>
                </div>
                {vt_bloco}
            </div>
            """
    else:
        projecoes_html = '<div class="section-box"><p>Nenhum imóvel avaliando cadastrado para este modelo.</p></div>'

    # Observações e parecer do avaliador
    obs_text = getattr(m, "observacoes", "").strip()
    obs_bloco = ""
    if obs_text:
        obs_linhas = "<br>".join(obs_text.splitlines())
        obs_bloco = f"""
        <h2>10. Considerações Finais e Observações Técnicas</h2>
        <div class="section-box" style="font-size: 12px; line-height: 1.6; text-align: justify;">
            {obs_linhas}
        </div>
        """

    # Identificação da norma aplicável (NBR 14653-2 Urbanos vs NBR 14653-3 Rurais)
    is_rural = (
        (model and model.nbr and "14653-3" in getattr(model.nbr, "norma_aplicada", ""))
        or getattr(m, "tipologia", 1) == 7
        or "rural" in (getattr(m, "descricao", "") or "").lower()
        or "rural" in (getattr(m, "subtitulo_relatorio", "") or "").lower()
        or "rural" in (getattr(m, "titulo_relatorio", "") or "").lower()
    )
    norma_codigo = "ABNT NBR 14653-3" if is_rural else "ABNT NBR 14653-2"
    norma_extenso = "Avaliação de Bens - Parte 3: Imóveis Rurais" if is_rural else "Avaliação de Bens - Parte 2: Imóveis Urbanos"
    tabela_norma = "Tabela 2 - NBR 14653-3" if is_rural else "Tabela 1 - NBR 14653-2"

    default_subtitulo = f"Em conformidade com a {norma_codigo} ({'Imóveis Rurais' if is_rural else 'Imóveis Urbanos'})"
    titulo_doc = getattr(m, "titulo_relatorio", None) or "RELATÓRIO DE AVALIAÇÃO IMOBILIÁRIA"
    subtitulo_doc = getattr(m, "subtitulo_relatorio", None)
    if not subtitulo_doc or "NBR 14653" in subtitulo_doc:
        subtitulo_doc = default_subtitulo
    solicitante_doc = getattr(m, "solicitante", None) or "Não informado"
    finalidade_doc = getattr(m, "finalidade", None) or "Determinação de Valor de Mercado"
    registro_prof_doc = getattr(m, "registro_profissional", None) or "Não informado"
    endereco_doc = getattr(m, "endereco_imovel", None) or "Conforme dados do imóvel e vistoria"

    # Informações profissionais e institucionais da empresa / perito para cabeçalho e rodapé
    qualificacao_prof_doc = getattr(m, "qualificacao_profissional", None) or "Engenheiro Avaliador"
    ibape_reg_doc = getattr(m, "ibape_registro", None) or ""
    empresa_nome_doc = getattr(m, "empresa_nome", None) or ""
    empresa_cnpj_doc = getattr(m, "empresa_cnpj", None) or ""
    empresa_crea_doc = getattr(m, "empresa_crea", None) or ""
    empresa_tel_doc = getattr(m, "empresa_telefone", None) or ""
    empresa_email_doc = getattr(m, "empresa_email", None) or ""
    empresa_site_doc = getattr(m, "empresa_site", None) or ""
    empresa_end_doc = getattr(m, "empresa_endereco", None) or ""

    # Construção dos Dados da Empresa / Profissional para o Cabeçalho (Alinhado à Esquerda no Topo)
    empresa_header_itens = []
    if empresa_nome_doc:
        empresa_header_itens.append(f"<div style='font-size: 14px; font-weight: 800; color: #0f172a; letter-spacing: 0.3px; text-transform: uppercase;'>{empresa_nome_doc}</div>")
    if empresa_cnpj_doc:
        empresa_header_itens.append(f"<div style='margin-top: 2px; font-size: 11px; color: #334155;'><strong>CNPJ/CPF:</strong> {empresa_cnpj_doc}</div>")
    if empresa_crea_doc:
        empresa_header_itens.append(f"<div style='margin-top: 2px; font-size: 11px; color: #334155;'><strong>CREA/CAU PJ:</strong> {empresa_crea_doc}</div>")
    if empresa_end_doc:
        empresa_header_itens.append(f"<div style='margin-top: 2px; font-size: 11px; color: #475569;'>{empresa_end_doc}</div>")
    
    contatos_line = []
    if empresa_tel_doc:
        contatos_line.append(f"<span>📞 {empresa_tel_doc}</span>")
    if empresa_email_doc:
        contatos_line.append(f"<span>✉️ {empresa_email_doc}</span>")
    if empresa_site_doc:
        contatos_line.append(f"<span>🌐 {empresa_site_doc}</span>")
    if contatos_line:
        empresa_header_itens.append("<div style='margin-top: 2px; font-size: 11px; font-weight: 500; color: #0284c7;'>" + " &nbsp;|&nbsp; ".join(contatos_line) + "</div>")

    empresa_header_html = ""
    if empresa_header_itens:
        empresa_header_html = f"""
        <div style="text-align: left; margin-bottom: 6px;">
            {"".join(empresa_header_itens)}
        </div>
        """

    # Construção do Rodapé Institucional Esteticamente Agradável (ao final do laudo)
    empresa_footer_itens = []
    if empresa_nome_doc:
        empresa_footer_itens.append(f"<div style='font-size: 12px; font-weight: 700; color: #0f172a; letter-spacing: 0.3px; text-transform: uppercase;'>{empresa_nome_doc}</div>")
    if empresa_cnpj_doc:
        empresa_footer_itens.append(f"<div style='margin-top: 2px; font-size: 10.5px; color: #334155;'><strong>CNPJ/CPF:</strong> {empresa_cnpj_doc}</div>")
    if empresa_crea_doc:
        empresa_footer_itens.append(f"<div style='margin-top: 2px; font-size: 10.5px; color: #334155;'><strong>CREA/CAU PJ:</strong> {empresa_crea_doc}</div>")
    if empresa_end_doc:
        empresa_footer_itens.append(f"<div style='margin-top: 2px; font-size: 10.5px; color: #475569;'>{empresa_end_doc}</div>")
    if contatos_line:
        empresa_footer_itens.append("<div style='margin-top: 3px; font-size: 10.5px; font-weight: 500; color: #0284c7;'>" + " &nbsp;|&nbsp; ".join(contatos_line) + "</div>")

    empresa_footer_html = ""
    if empresa_footer_itens:
        empresa_footer_html = f"""
        <div class="avoid-break" style="margin-top: 25px; border-top: 2px solid #0284c7; background: #f8fafc; border-radius: 6px; padding: 10px 18px; border: 1px solid #e2e8f0; font-size: 11px; color: #475569; line-height: 1.4; text-align: center;">
            {"".join(empresa_footer_itens)}
        </div>
        """

    # Normalidade estatísticas
    norm = model.normalidade
    norm_status_cor = "#16a34a" if norm.atende_normalidade else "#dc2626"
    norm_status_txt = "Atende aos pressupostos de normalidade" if norm.atende_normalidade else "Atenção: desvio de normalidade detectado"

    # Bloco de diagnósticos técnicos e sugestões normativas de ajuste
    diagnosticos_html = ""
    diags = getattr(model, "diagnosticos_tecnicos", []) or (nbr.diagnosticos_ajuste if nbr else [])
    if diags:
        itens_diag = "".join([f"<li style='margin-bottom: 5px;'>{d}</li>" for d in diags])
        diagnosticos_html = f"""
        <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0284c7; border-radius: 6px; padding: 12px 16px; margin-top: 12px; font-size: 11px; line-height: 1.5;">
            <div style="font-weight: 700; color: #0f172a; margin-bottom: 6px; text-transform: uppercase; font-size: 11px;">
                💡 Diagnóstico Técnico & Orientações Normativas de Ajuste (NBR 14653):
            </div>
            <ul style="margin: 0 0 0 16px; padding: 0; color: #334155;">
                {itens_diag}
            </ul>
        </div>
        """

    autoprint_script = """
    window.addEventListener('load', function() {
        setTimeout(function() {
            window.focus();
            window.print();
        }, 500);
    });
    """ if autoprint else ""

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>{titulo_doc} - {subtitulo_doc}</title>
        <script src="/static/vendor/html2pdf.bundle.min.js"></script>
        <style>
            @page {{
                size: A4 portrait;
                margin: 12mm 10mm 15mm 10mm;
            }}
            @media print {{
                body {{
                    font-size: 11pt;
                    padding: 0 !important;
                    background: #ffffff !important;
                }}
                .no-print {{
                    display: none !important;
                }}
                .page-break {{
                    page-break-before: always;
                    break-before: page;
                }}
                .avoid-break {{
                    page-break-inside: avoid;
                    break-inside: avoid;
                }}
                table {{
                    page-break-inside: auto;
                }}
                tr {{
                    page-break-inside: avoid;
                    page-break-after: auto;
                }}
                thead {{
                    display: table-header-group;
                }}
            }}

            * {{
                box-sizing: border-box;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                color: #0f172a;
                line-height: 1.45;
                margin: 0;
                padding: 30px;
                background-color: #f8fafc;
            }}

            .report-paper {{
                background-color: #ffffff;
                max-width: 960px;
                margin: 0 auto;
                padding: 35px 45px;
                border-radius: 8px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            }}

            @media print {{
                .report-paper {{
                    box-shadow: none !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    max-width: 100% !important;
                    border-radius: 0 !important;
                }}
            }}

            /* Barra de Ações Superior */
            .action-bar {{
                background: #0f172a;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                margin-bottom: 25px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
            }}
            .action-btn {{
                background: #0284c7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                transition: background 0.15s ease;
            }}
            .action-btn:hover {{
                background: #0369a1;
            }}
            .action-btn.secondary {{
                background: #334155;
            }}
            .action-btn.secondary:hover {{
                background: #475569;
            }}

            .header-laudo {{
                border-bottom: 3px solid #0f172a;
                padding-bottom: 15px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            h1 {{
                font-size: 20px;
                margin: 0;
                color: #0f172a;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            h2 {{
                font-size: 14px;
                margin: 20px 0 8px 0;
                color: #0f172a;
                border-left: 4px solid #0284c7;
                padding-left: 8px;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }}
            .section-box {{
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 12px 14px;
                margin-bottom: 12px;
            }}
            .grid-2 {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }}
            .grid-3 {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 10px;
            }}
            .badge-grau {{
                display: inline-block;
                padding: 3px 10px;
                border-radius: 9999px;
                font-weight: bold;
                font-size: 12px;
            }}
            .table-compact {{
                width: 100%;
                border-collapse: collapse;
                font-size: 11px;
                margin-top: 8px;
            }}
            .table-compact th {{
                background-color: #f1f5f9;
                color: #334155;
                font-weight: 600;
            }}
            .table-compact td, .table-compact th {{
                border: 1px solid #cbd5e1;
            }}
        </style>
    </head>
    <body>

        <!-- Barra de Ações Superior (Oculta na Impressão/PDF) -->
        <div class="action-bar no-print" style="max-width: 960px; margin: 0 auto 20px auto;">
            <div style="font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px;">
                <span>OpenValora &bull; Relatório NBR 14653</span>
            </div>
            <div style="display: flex; gap: 10px;">
                <button class="action-btn" onclick="downloadReportPDF()">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Baixar em PDF
                </button>
                <button class="action-btn secondary" onclick="window.print()">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
                    Imprimir
                </button>
                <button class="action-btn secondary" onclick="triggerParentCustomizer()">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                    Personalizar
                </button>
            </div>
        </div>

        <div class="report-paper" id="report-content">

            <!-- Cabeçalho Institucional: Logo e Dados da Empresa à Esquerda, Metadados à Direita -->
            <div class="header-laudo" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; padding-bottom: 14px;">
                <div style="display: flex; align-items: flex-start; text-align: left; gap: 16px;">
                    {logo_html}
                    <div style="text-align: left;">
                        {empresa_header_html}
                    </div>
                </div>
                <div style="text-align: right; font-size: 11px; color: #475569; flex-shrink: 0; padding-top: 4px;">
                    <div><strong>OpenValora v0.1.0</strong> &bull; Engenharia de Avaliações</div>
                    <div>Data: <strong>{m.data_criacao}</strong></div>
                    <div>Modelo Nº: <strong>{model.id}</strong></div>
                    <div style="margin-top: 4px; font-size: 10px; color: #64748b;">{norma_codigo}</div>
                </div>
            </div>

            <!-- Título e Subtítulo Centralizados do Relatório -->
            <div style="text-align: center; margin: 15px 0 22px 0; padding: 12px 14px; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px;">
                <h1 style="margin: 0; font-size: 21px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; color: #0f172a; text-align: center;">{titulo_doc}</h1>
                <div style="font-size: 13px; color: #475569; font-weight: 600; margin-top: 5px; text-align: center;">{subtitulo_doc}</div>
            </div>

            <!-- 1. Identificação -->
            <h2>1. Identificação do Trabalho, Partes e Imóvel</h2>
            <div class="section-box grid-2">
                <div>
                    <div><strong>Título do Trabalho:</strong> {m.nome}</div>
                    <div><strong>Contratante / Solicitante:</strong> {solicitante_doc}</div>
                    <div><strong>Finalidade da Avaliação:</strong> {finalidade_doc}</div>
                    <div><strong>Localização / Objeto:</strong> {endereco_doc}</div>
                </div>
                <div>
                    <div><strong>Responsável Técnico:</strong> {m.autor or "Nome do Responsável"} ({qualificacao_prof_doc})</div>
                    <div><strong>Registro Profissional:</strong> {registro_prof_doc} {f"| {ibape_reg_doc}" if ibape_reg_doc else ""}</div>
                    {f"<div><strong>Empresa / Escritório:</strong> {empresa_nome_doc}</div>" if empresa_nome_doc else ""}
                    {f"<div><strong>CNPJ / CPF:</strong> {empresa_cnpj_doc}</div>" if empresa_cnpj_doc else ""}
                    {f"<div><strong>Registro CREA/CAU PJ:</strong> {empresa_crea_doc}</div>" if empresa_crea_doc else ""}
                    {f"<div><strong>Contato / Tel:</strong> {empresa_tel_doc} {f'| {empresa_email_doc}' if empresa_email_doc else ''}</div>" if empresa_tel_doc or empresa_email_doc else ""}
                    <div><strong>Norma Técnica de Referência:</strong> ABNT NBR 14653-1 e {norma_codigo}</div>
                </div>
            </div>

            <!-- 2. Metodologia -->
            <h2>2. Metodologia Avaliatória e Tratamento por Inferência Estatística</h2>
            <div class="section-box" style="font-size: 12px; text-align: justify; line-height: 1.5;">
                O presente trabalho foi elaborado com estrita observância às prescrições da norma brasileira <strong>{norma_codigo}</strong> ({norma_extenso}). Utilizou-se o <strong>Método Comparativo Direto de Dados de Mercado (MCDDM)</strong>, com tratamento estatístico através de <strong>Regressão Linear Múltipla</strong> pelo método dos Mínimos Quadrados Ordinários (MQO). A variável dependente adotada foi <strong>{dep_var_nome}</strong> ({unit_label}), explicada pelas variáveis independentes representativas das características físicas, construtivas, locacionais e de mercado da amostra coletada.
            </div>

            <!-- 3. Tabela Completa de Dados Amostrais -->
            <div class="avoid-break">
                <h2>3. Tabela Completa de Dados Amostrais Utilizados nos Cálculos</h2>
                <div style="font-size: 11px; color: #64748b; margin-bottom: 6px;">
                    Total de dados coletados: <strong>{len(project.dados)}</strong> | Válidos na regressão: <strong>{valid_count}</strong> | Outliers descartados: <strong>{outlier_count}</strong> | Desabilitados: <strong>{disabled_count}</strong>
                </div>
                <div style="overflow-x: auto; margin-bottom: 12px;">
                    <table class="table-compact">
                        <thead>
                            <tr>
                                {dados_th}
                            </tr>
                        </thead>
                        <tbody>
                            {dados_rows}
                        </tbody>
                    </table>
                </div>

                <div style="font-size: 12px; font-weight: 600; margin-top: 10px; color: #334155;">Estatísticas Descritivas Básicas da Amostra (Dados Válidos)</div>
                <table class="table-compact" style="margin-bottom: 12px;">
                    <thead>
                        <tr>
                            <th style="padding: 4px 8px; text-align: left;">Variável</th>
                            <th style="padding: 4px 8px; text-align: right;">Nº Obs.</th>
                            <th style="padding: 4px 8px; text-align: right;">Média</th>
                            <th style="padding: 4px 8px; text-align: right;">Desvio Padrão</th>
                            <th style="padding: 4px 8px; text-align: right;">Mínimo</th>
                            <th style="padding: 4px 8px; text-align: right;">Máximo</th>
                        </tr>
                    </thead>
                    <tbody>
                        {desc_rows}
                    </tbody>
                </table>
            </div>

            <div class="page-break"></div>

            <!-- 4. Equação de Regressão -->
            <h2>4. Equação de Regressão Linear Ajustada</h2>
            <div style="background-color: #0f172a; color: #f8fafc; border-radius: 6px; padding: 14px; font-family: monospace; font-size: 13px; margin-bottom: 12px; word-break: break-all;">
                {model.equacao_texto}
            </div>

            <div class="grid-2" style="margin-bottom: 12px;">
                <div class="section-box" style="margin: 0; font-size: 12px;">
                    <div><strong>Coeficiente de Determinação (R²):</strong> {format_number(model.r2, 4)} ({format_number(model.r2 * 100, 2)}%)</div>
                    <div><strong>Coeficiente de Correlação (R):</strong> {format_number(model.r, 4)}</div>
                    <div><strong>R² Ajustado (R²aj):</strong> {format_number(model.r2_ajustado, 4)} ({format_number(model.r2_ajustado * 100, 2)}%)</div>
                </div>
                <div class="section-box" style="margin: 0; font-size: 12px;">
                    <div><strong>R² no Espaço Original:</strong> {format_number(model.r2_original, 4)} ({format_number(model.r2_original * 100, 2)}%)</div>
                    <div><strong>Erro Padrão da Regressão:</strong> {format_number(model.erro_padrao, 4)}</div>
                    <div><strong>Estatística Durbin-Watson:</strong> {format_number(model.durbin_watson, 4)} ({model.durbin_watson_status})</div>
                </div>
            </div>

            <!-- 5. ANOVA -->
            <h2>5. Análise de Variância (ANOVA) e Significância Global</h2>
            {anova_html}

            <!-- 6. Regressores -->
            <h2>6. Análise Individual dos Regressores (Teste t de Student & VIF)</h2>
            <table class="table-compact" style="margin-bottom: 15px;">
                <thead>
                    <tr>
                        <th style="padding: 6px 10px; text-align: left;">Variável</th>
                        <th style="padding: 6px 10px; text-align: center;">Transf.</th>
                        <th style="padding: 6px 10px; text-align: right;">Coeficiente (β)</th>
                        <th style="padding: 6px 10px; text-align: right;">Erro Padrão</th>
                        <th style="padding: 6px 10px; text-align: right;">t Calculado</th>
                        <th style="padding: 6px 10px; text-align: right;">Signif. Individual</th>
                        <th style="padding: 6px 10px; text-align: right;">Elasticidade</th>
                        <th style="padding: 6px 10px; text-align: right;">VIF</th>
                    </tr>
                </thead>
                <tbody>
                    {reg_rows}
                </tbody>
            </table>

            <!-- 7. Diagnósticos Residuais e Normalidade -->
            <div class="avoid-break">
                <h2>7. Análise dos Resíduos e Diagnósticos de Hipóteses Básicas</h2>
                <div class="grid-2">
                    <div class="section-box" style="font-size: 12px;">
                        <div style="font-weight: 600; color: #1e293b; margin-bottom: 6px;">Distribuição dos Resíduos Padronizados</div>
                        <div>&bull; Resíduos em ±1 DP: <strong>{format_number(norm.dentro_1_dp_pct, 1)}%</strong> (Ref. Gauss: ~68,0%)</div>
                        <div>&bull; Resíduos em ±2 DP: <strong>{format_number(norm.dentro_2_dp_pct, 1)}%</strong> (Ref. Gauss: ~95,0%)</div>
                        <div>&bull; Resíduos em ±3 DP: <strong>{format_number(norm.dentro_3_dp_pct, 1)}%</strong> (Ref. Gauss: ~99,0%)</div>
                    </div>
                    <div class="section-box" style="font-size: 12px;">
                        <div style="font-weight: 600; color: #1e293b; margin-bottom: 6px;">Testes Estatísticos de Aderência</div>
                        <div>&bull; Kolmogorov-Smirnov: stat = <strong>{format_number(norm.ks_stat, 4)}</strong> (p-valor: {format_number(norm.ks_pvalor * 100, 2)}%)</div>
                        {f"<div>&bull; Shapiro-Wilk: W = <strong>{format_number(norm.shapiro_stat, 4)}</strong> (p-valor: {format_number(norm.shapiro_pvalor * 100, 2)}%)</div>" if getattr(norm, 'shapiro_stat', None) is not None else ""}
                        <div>&bull; Diagnóstico de Normalidade: <strong style="color: {norm_status_cor};">{norm_status_txt}</strong></div>
                        <div>&bull; Homocedasticidade: <strong>{'Verificada e aceita' if model.homocedastico else 'Heterocedasticidade detectada'}</strong>{f" (Breusch-Pagan p-valor: {format_number(model.breusch_pagan_pvalor * 100, 2)}%)" if getattr(model, 'breusch_pagan_pvalor', None) is not None else ""}</div>
                    </div>
                </div>
            </div>

            <!-- 8. Enquadramento NBR 14653 -->
            <div class="avoid-break">
                <h2>8. Enquadramento Normativo na {norma_codigo}</h2>
                <div class="grid-2" style="margin-bottom: 12px;">
                    <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; text-align: center;">
                        <div style="font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase;">Grau de Fundamentação</div>
                        <div style="font-size: 24px; font-weight: 800; color: #0284c7; margin-top: 4px;">{nbr.grau_fundamentacao if nbr else 'N/A'}</div>
                        <div style="font-size: 11px; color: #64748b; margin-top: 2px;">{nbr.resumo_analitico if nbr else ''}</div>
                    </div>
                    <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; text-align: center;">
                        <div style="font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase;">Grau de Precisão</div>
                        <div style="font-size: 24px; font-weight: 800; color: #16a34a; margin-top: 4px;">{nbr.grau_precisao if nbr else 'N/A'}</div>
                        <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Amplitude do IC a 80%: <strong>{format_number(nbr.amplitude_ic_pct if nbr else 0, 2)}%</strong></div>
                    </div>
                </div>

                <table class="table-compact" style="margin-bottom: 15px;">
                    <thead>
                        <tr>
                            <th style="padding: 6px 10px; text-align: left;">Item de Avaliação ({tabela_norma})</th>
                            <th style="padding: 6px 10px; text-align: center; width: 80px;">Grau</th>
                            <th style="padding: 6px 10px; text-align: left;">Critério & Justificativa Técnica</th>
                        </tr>
                    </thead>
                    <tbody>
                        {nbr_fund_rows}
                    </tbody>
                </table>
                {diagnosticos_html}
            </div>

            <!-- 9. Imóvel Avaliando -->
            <div class="avoid-break">
                <h2>9. Resultado da Avaliação do Imóvel Avaliando</h2>
                {projecoes_html}
            </div>

            <!-- Observações Personalizadas -->
            {obs_bloco}

            <!-- Encerramento e Assinatura -->
            <div class="avoid-break" style="margin-top: 40px; padding-top: 25px; border-top: 1px solid #cbd5e1; display: flex; justify-content: space-between; align-items: flex-end;">
                <div>
                    <div style="width: 320px; border-bottom: 1.5px solid #0f172a; margin-bottom: 8px;"></div>
                    <div style="font-weight: 800; font-size: 15px; color: #0f172a;">{m.autor or "Nome do Responsável"}</div>
                    <div style="font-size: 12px; font-weight: 600; color: #334155;">{qualificacao_prof_doc}</div>
                    <div style="font-size: 11px; color: #475569;">Registro Profissional: <strong>{registro_prof_doc}</strong></div>
                    {f"<div style='font-size: 11px; color: #64748b;'>Especialista: <strong>{ibape_reg_doc}</strong></div>" if ibape_reg_doc else ""}
                </div>
                <div style="text-align: right; font-size: 11px; color: #64748b; line-height: 1.6;">
                    <div><strong>Data do Laudo / Relatório:</strong> {m.data_criacao}</div>
                    <div>Local de Referência: {m.endereco_imovel.split(',')[0] if m.endereco_imovel else 'Imóvel Avaliando'}</div>
                    <div style="font-size: 10px; color: #94a3b8; margin-top: 4px;">OpenValora &bull; Software Livre de Avaliação Imobiliária</div>
                </div>
            </div>

            <!-- Rodapé Institucional da Empresa / Profissional -->
            {empresa_footer_html}

        </div>

        <script>
            {autoprint_script}

            function triggerParentCustomizer() {{
                if (window.parent && window.parent !== window) {{
                    window.parent.postMessage({{ type: 'OPEN_REPORT_CUSTOMIZER' }}, '*');
                }} else {{
                    alert('Para personalizar título, logotipo, solicitante e observações, acesse a aba Relatório no painel principal do OpenValora.');
                }}
            }}

            function downloadReportPDF() {{
                const el = document.getElementById('report-content');
                if (!el) return;

                const filename = 'Relatorio_OpenValora_{(m.nome or "Modelo").replace(" ", "_")}.pdf';
                const opt = {{
                    margin: [10, 8, 12, 8],
                    filename: filename,
                    image: {{ type: 'jpeg', quality: 0.98 }},
                    html2canvas: {{ scale: 2, useCORS: true, logging: false }},
                    jsPDF: {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
                }};

                if (window.html2pdf) {{
                    const btn = document.querySelector('.action-btn');
                    const origText = btn ? btn.innerHTML : '';
                    if (btn) btn.innerHTML = 'Gerando PDF...';

                    window.html2pdf().set(opt).from(el).save().then(function() {{
                        if (btn) btn.innerHTML = origText;
                    }}).catch(function(err) {{
                        console.error('Erro ao gerar PDF:', err);
                        if (btn) btn.innerHTML = origText;
                        alert('Falha ao gerar o arquivo PDF. Você também pode clicar em "Imprimir" e selecionar "Salvar como PDF".');
                    }});
                }} else {{
                    window.print();
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html
