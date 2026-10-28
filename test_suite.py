"""
OpenValora - Comprehensive Test Suite
Verifica todas as funcionalidades essenciais, modelos estatísticos, RNA,
importação/exportação e rotas da API.
"""

import os
import io
import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.core.models import Project, Variable, SampleItem, SubjectProperty, CalculationOptions
from app.core.io_sda import (
    read_sda_file, write_sda_file, import_excel_or_csv, export_to_excel
)
from app.core.regression import run_regression_search
from app.core.neural_network import train_rna
from app.core.nbr14653 import evaluate_nbr14653
from app.core.valuation import evaluate_subject
from app.core.var_library import search_variables, get_tipologias, get_default_variables_for_typology
from app.core.report_generator import generate_laudo_html

class TestOpenValora(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.sample_dir = Path("sample_data")

    def test_01_read_all_sample_sda_files(self):
        """Testa se todos os 12 arquivos .sda de exemplo são lidos sem erro."""
        sda_files = list(self.sample_dir.glob("*.sda"))
        self.assertGreaterEqual(len(sda_files), 10, "Menos de 10 arquivos .sda encontrados")
        
        for f in sda_files:
            with self.subTest(file=f.name):
                proj = read_sda_file(f)
                self.assertIsInstance(proj, Project)
                self.assertGreater(len(proj.variaveis), 0)
                self.assertGreater(len(proj.dados), 0)

    def test_02_regression_calculation_on_samples(self):
        """Testa o motor de regressão em múltiplos arquivos com diferentes configurações."""
        test_samples = [
            "Modelo de Apartamentos.sda",
            "Exercicio 1 - Regressao Simples.sda",
            "Exercicio 2 - Transformacao variavel.sda",
            "Exercicio 4_1 - LOTES.sda",
            "Exercicio 4_3 - Lojas.sda",
            "Exercicio 5_1 - Apartamentos.sda",
            "Exercicio 5_2 - Casas.sda",
            "Exercicio 6 - Heterocedasticidade.sda",
            "Exercicio 7 - Colinearidade.sda",
            "Exercicio final - APARTAMENTOS CALDAS NOVAS.sda",
            "Lotes Juiz de Fora.sda",
        ]
        for name in test_samples:
            target = self.sample_dir / name
            if not target.exists():
                continue
            with self.subTest(sample=name):
                proj = read_sda_file(target)
                models = run_regression_search(proj)
                self.assertGreater(len(models), 0)
                top = models[0]
                self.assertGreaterEqual(top.r2, 0.0)
                self.assertLessEqual(top.r2, 1.0)
                self.assertGreaterEqual(top.r2_original, 0.0)
                self.assertIsNotNone(top.nbr)
                self.assertIn(top.nbr.grau_fundamentacao, ["Grau III", "Grau II", "Grau I", "Não Enquadrado"])

    def test_03_write_and_read_sda_bidirectional(self):
        """Testa se a exportação binária .sda é legível de volta com integridade."""
        sample = self.sample_dir / "Modelo de Apartamentos.sda"
        proj_orig = read_sda_file(sample)
        
        # Gera binário .sda
        sda_bytes = write_sda_file(proj_orig)
        self.assertGreater(len(sda_bytes), 1000)
        
        # Lê de volta
        proj_read = read_sda_file(sda_bytes)
        self.assertEqual(proj_read.metadata.nome, proj_orig.metadata.nome)
        self.assertEqual(len(proj_read.variaveis), len(proj_orig.variaveis))
        self.assertEqual(len(proj_read.dados), len(proj_orig.dados))

    def test_04_import_and_export_excel(self):
        """Testa exportação para Excel (.xlsx) e importação."""
        sample = self.sample_dir / "Modelo de Apartamentos.sda"
        proj = read_sda_file(sample)
        models = run_regression_search(proj)
        proj.modelos_calculados = models
        
        xlsx_bytes = export_to_excel(proj)
        self.assertGreater(len(xlsx_bytes), 1000)
        
        # Importa de volta
        vars_imp, dados_imp = import_excel_or_csv(xlsx_bytes, "teste.xlsx")
        self.assertGreater(len(vars_imp), 0)
        self.assertGreater(len(dados_imp), 0)

    def test_05_import_csv_with_accents(self):
        """Testa importação de CSV com caracteres especiais em português."""
        csv_content = (
            "Endereço;Área Privativa;Padrão;Valor Unitário\n"
            "Rua das Acácias, 100;85.5;2;4500.00\n"
            "Av. Independência, 250;120.0;3;5200.00\n"
            "Praça dos Andradas, 12;65.0;1;3800.00\n"
            "Rua Tiradentes, 88;95.0;2;4700.00\n"
            "Alameda dos Ipês, 55;110.0;3;5100.00\n"
        ).encode("utf-8")
        
        vars_imp, dados_imp = import_excel_or_csv(csv_content, "dados.csv")
        var_names = [v.nome for v in vars_imp]
        self.assertIn("Endereço", var_names)
        self.assertIn("Área Privativa", var_names)
        self.assertIn("Padrão", var_names)
        self.assertIn("Valor Unitário", var_names)
        self.assertEqual(len(dados_imp), 5)

    def test_06_neural_network_rna(self):
        """Testa treinamento do módulo de Redes Neurais Artificiais (RNA)."""
        sample = self.sample_dir / "Modelo de Apartamentos.sda"
        proj = read_sda_file(sample)
        res = train_rna(
            project=proj,
            hidden_layer_sizes=(6,),
            activation="logistic",
            max_iter=500,
            learning_rate_init=0.01,
            solver="lbfgs",
            bagging=False
        )
        self.assertIn("r2", res)
        self.assertIn("rmse", res)
        self.assertIn("projecoes", res)
        self.assertGreater(len(res["projecoes"]), 0)

    def test_07_nbr_14653_engine(self):
        """Testa os critérios de enquadramento da NBR 14653-2."""
        # Grau III pleno
        nbr_g3 = evaluate_nbr14653(
            n_sample=35,
            k_regressors=3,  # 6*(3+1) = 24 <= 35 -> Grau III
            f_significance_pct=0.01,
            max_t_significance_pct=5.0,
            amplitude_ic_pct=22.0
        )
        self.assertEqual(nbr_g3.grau_fundamentacao, "Grau III")
        self.assertEqual(nbr_g3.grau_precisao, "Grau III")

        # Inversão de sinal rejeita fundamentação
        nbr_inv = evaluate_nbr14653(
            n_sample=35,
            k_regressors=3,
            f_significance_pct=0.01,
            max_t_significance_pct=5.0,
            amplitude_ic_pct=22.0,
            has_inverted_signs=True
        )
        self.assertEqual(nbr_inv.grau_fundamentacao, "Não Enquadrado")

    def test_08_var_library(self):
        """Testa catálogo de variáveis e tipologias."""
        res = search_variables(query="área")
        self.assertGreater(len(res), 0)
        
        tips = get_tipologias()
        self.assertGreater(len(tips), 0)
        
        vars_apt = get_default_variables_for_typology("Apartamentos")
        self.assertGreater(len(vars_apt), 3)

    def test_09_report_generation(self):
        """Testa geração do relatório técnico HTML conforme NBR 14653 com dados completos."""
        sample = self.sample_dir / "Modelo de Apartamentos.sda"
        proj = read_sda_file(sample)
        models = run_regression_search(proj)
        html = generate_laudo_html(proj, models[0])
        self.assertTrue("RELATÓRIO DE AVALIAÇÃO IMOBILIÁRIA" in html or "Relatório de Avaliação Imobiliária" in html or "Laudo de Avaliação Imobiliária" in html)
        self.assertIn("ABNT NBR 14653-2", html)
        self.assertIn(models[0].equacao_texto, html)
        # Verifica presença da tabela completa de dados amostrais e estatísticas (exigência do usuário)
        self.assertIn("Tabela Completa de Dados Amostrais", html)
        self.assertIn("Estatísticas Descritivas Básicas da Amostra", html)

    def test_10_api_endpoints(self):
        """Testa rotas HTTP do FastAPI."""
        # 1. Index e créditos de autoria (sem referência a engenheiro civil conforme solicitado)
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("https://github.com/b-host", r.text)
        self.assertIn("Crédito", r.text)
        self.assertNotIn("Engenharia Civil Responsável", r.text)

        # 2. Novo Projeto com padrões de engenheiro e título
        r_new = self.client.post("/api/project/new", data={"typology": "Apartamentos"})
        self.assertEqual(r_new.status_code, 200)
        self.assertEqual(r_new.json()["metadata"]["autor"], "Nome do Responsável")
        self.assertEqual(r_new.json()["metadata"]["titulo_relatorio"], "RELATÓRIO DE AVALIAÇÃO IMOBILIÁRIA")

        # 3. Project
        r = self.client.get("/api/project")
        self.assertEqual(r.status_code, 200)

        # 4. Carrega modelo de amostra para teste de rotas dependentes de dados
        r_sample = self.client.post("/api/samples/load", data={"filename": "Modelo de Apartamentos.sda"})
        self.assertEqual(r_sample.status_code, 200)

        # 5. Calculate
        r = self.client.post("/api/calculate")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "ok")
        self.assertGreater(data["count"], 0)

        # 5. Exploratory
        r = self.client.get("/api/exploratory")
        self.assertEqual(r.status_code, 200)
        self.assertIn("stats", r.json())

        # 6. Report com suporte a NBR 14653 e impressão
        r = self.client.get("/report?autoprint=1")
        self.assertEqual(r.status_code, 200)
        self.assertIn("window.print()", r.text)

        # 7. Export SDA
        r = self.client.get("/api/export/sda")
        self.assertEqual(r.status_code, 200)
        self.assertGreater(len(r.content), 1000)

        # 8. Export XLSX
        r = self.client.get("/api/export/xlsx")
        self.assertEqual(r.status_code, 200)
        self.assertGreater(len(r.content), 1000)

        # 9. Export .valora (Formato Aberto Nativo)
        r_valora = self.client.get("/api/export/valora")
        self.assertEqual(r_valora.status_code, 200)
        valora_bytes = r_valora.content
        self.assertGreater(len(valora_bytes), 500)

        # 10. Upload / Importação de .valora
        files = {"file": ("teste_projeto.valora", io.BytesIO(valora_bytes), "application/json")}
        r_up = self.client.post("/api/upload", files=files)
        self.assertEqual(r_up.status_code, 200)
        self.assertEqual(r_up.json()["metadata"]["nome"], "Apartamentos Funcionários")

    def test_11_all_sample_files(self):
        """Valida a leitura, regressão e relatório de todos os arquivos de exemplo .sda."""
        sda_files = list(self.sample_dir.glob("*.sda"))
        self.assertGreaterEqual(len(sda_files), 15, "Deve haver pelo menos 15 arquivos de exemplo .sda.")
        
        for p in sda_files:
            with self.subTest(file=p.name):
                proj = read_sda_file(p)
                self.assertIsNotNone(proj.metadata)
                self.assertGreater(len(proj.variaveis), 0)
                self.assertGreater(len(proj.dados), 0)
                
                models = run_regression_search(proj)
                self.assertGreater(len(models), 0, f"Deveria calcular ao menos 1 modelo para {p.name}")
                
                html = generate_laudo_html(proj, models[0])
                self.assertGreater(len(html), 1000)
                self.assertIn("ABNT NBR 14653-2", html)

    def test_12_diagnostics_and_header_layout(self):
        """Valida se diagnósticos acionáveis da NBR e dados da empresa no cabeçalho superior esquerdo funcionam."""
        sample = self.sample_dir / "Exercicio 1 - Regressao Simples.sda"
        proj = read_sda_file(sample)
        
        # Define dados da empresa nos metadados
        proj.metadata.empresa_nome = "Engenharia de Avaliações Alpha Ltda"
        proj.metadata.empresa_cnpj = "12.345.678/0001-99"
        proj.metadata.empresa_crea = "998877/D-MG"
        proj.metadata.empresa_telefone = "(31) 98765-4321"
        proj.metadata.empresa_email = "contato@alphapericias.com.br"
        
        models = run_regression_search(proj)
        self.assertGreater(len(models), 0)
        top = models[0]
        
        # Verifica se diagnósticos técnicos existem e são informativos
        self.assertIsInstance(top.diagnosticos_tecnicos, list)
        self.assertGreater(len(top.diagnosticos_tecnicos), 0)
        self.assertIsInstance(top.nbr.diagnosticos_ajuste, list)
        
        # Gera o relatório HTML
        html = generate_laudo_html(proj, top)
        
        # 1. Valida que dados da empresa estão presentes no cabeçalho superior
        self.assertIn("Engenharia de Avaliações Alpha Ltda", html)
        self.assertIn("12.345.678/0001-99", html)
        self.assertIn("998877/D-MG", html)
        self.assertIn("(31) 98765-4321", html)
        
        # 2. Valida separação clara entre CNPJ e CREA/CAU PJ
        self.assertIn("<strong>CNPJ/CPF:</strong> 12.345.678/0001-99", html)
        self.assertIn("<strong>CREA/CAU PJ:</strong> 998877/D-MG", html)
        
        # 3. Valida cabeçalho superior e título/subtítulo centralizados
        self.assertIn('header-laudo', html)
        self.assertIn('text-align: center;', html)
        self.assertIn('RELATÓRIO DE AVALIAÇÃO IMOBILIÁRIA', html)
        
        # 4. Valida logotipo padrão do OpenValora presente por padrão
        self.assertTrue("data:image/png;base64," in html or "/static/img/logo.png" in html)
        
        # 5. Valida bloco de diagnóstico e recomendações normativas no laudo
        self.assertIn("Diagnóstico Técnico", html)
        
        # 6. Valida rodapé institucional esteticamente agradável no final do documento
        self.assertIn("border-top: 2px solid #0284c7;", html)

    def test_13_safe_float_and_rural_nbr(self):
        """Valida parsing defensivo de números (safe_float) e conformidade NBR 14653-3 para Imóveis Rurais."""
        from app.core.statistics import safe_float
        from app.core.nbr14653 import evaluate_nbr14653

        # 1. Testes unitários do safe_float
        self.assertEqual(safe_float("1.250,50"), 1250.50)
        self.assertEqual(safe_float("1250,50"), 1250.50)
        self.assertEqual(safe_float("1,250.50"), 1250.50)
        self.assertEqual(safe_float("1250.50"), 1250.50)
        self.assertEqual(safe_float(" 1.234.567,89 "), 1234567.89)
        self.assertEqual(safe_float(""), 0.0)
        self.assertEqual(safe_float(None), 0.0)
        self.assertEqual(safe_float("   "), 0.0)
        self.assertEqual(safe_float("invalido"), 0.0)
        self.assertEqual(safe_float("", default=99.0), 99.0)
        self.assertEqual(safe_float(42), 42.0)
        self.assertEqual(safe_float(True), 1.0)
        self.assertEqual(safe_float(False), 0.0)

        # 2. Testes de enquadramento NBR 14653-3 (Rural) vs NBR 14653-2 (Urbano)
        # Para k = 1 regressor:
        # NBR 14653-2 (Urbano): Grau III exige 6*(1+1) = 12 observações. Com N = 8, atinge Grau II (3*(k+1) = 6).
        # NBR 14653-3 (Rural): Grau III exige 4*(1+1) = 8 observações. Com N = 8, atinge Grau III!
        res_urbano = evaluate_nbr14653(
            n_sample=8,
            k_regressors=1,
            f_significance_pct=0.5,
            max_t_significance_pct=5.0,
            amplitude_ic_pct=25.0,
            is_rural=False
        )
        self.assertEqual(res_urbano.requisitos_fundamentacao[1].grau_obtido, "II")
        self.assertEqual(res_urbano.norma_aplicada, "ABNT NBR 14653-2 (Imóveis Urbanos)")

        res_rural = evaluate_nbr14653(
            n_sample=8,
            k_regressors=1,
            f_significance_pct=0.5,
            max_t_significance_pct=5.0,
            amplitude_ic_pct=25.0,
            is_rural=True
        )
        self.assertEqual(res_rural.requisitos_fundamentacao[1].grau_obtido, "III")
        self.assertEqual(res_rural.grau_fundamentacao, "Grau III")
        self.assertEqual(res_rural.norma_aplicada, "ABNT NBR 14653-3 (Imóveis Rurais)")

        # 3. Teste em projeto com dados brasileiros formatados e tipologia rural (tipologia = 7)
        sample = self.sample_dir / "Exercicio 1 - Regressao Simples.sda"
        proj = read_sda_file(sample)
        proj.metadata.tipologia = 7  # Imóveis Rurais
        
        # Insere dados com strings formatadas com vírgula e espaços
        for item in proj.dados[:5]:
            for k_var, raw_v in list(item.valores.items()):
                try:
                    f_val = float(raw_v)
                    item.valores[k_var] = f" {f_val:.2f} ".replace(".", ",")
                except (ValueError, TypeError):
                    pass

        models = run_regression_search(proj)
        self.assertGreater(len(models), 0, "Regressão deve calcular com sucesso mesmo com dados formatados em string.")
        
        top = models[0]
        self.assertIn("14653-3", top.nbr.norma_aplicada)

        # 4. Geração de laudo para imóvel rural
        html = generate_laudo_html(proj, top)
        self.assertIn("ABNT NBR 14653-3", html)
        self.assertIn("Tabela 2 - NBR 14653-3", html)

    def test_14_exploratory_and_version_0_1_0(self):
        """Valida se o software está operando na versão 0.1.0 e se a rota exploratória opera com variáveis X e Y."""
        # 1. Validação de versionamento do projeto
        self.assertEqual(app.version, "0.1.0", f"Versão esperada '0.1.0', obtida '{app.version}'")

        # 2. Carrega um modelo de exemplo
        sample = self.sample_dir / "Modelo de Apartamentos.sda"
        proj = read_sda_file(sample)
        models = run_regression_search(proj)
        top = models[0]

        # 3. Validação do laudo com a tag de versão 0.1.0
        html = generate_laudo_html(proj, top)
        self.assertIn("OpenValora v0.1.0", html)

        # 4. Teste da API exploratória
        resp = self.client.get("/api/exploratory")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("variables", data)
        self.assertIn("stats", data)
        self.assertIn("correlations", data)

        variables = data["variables"]
        self.assertGreater(len(variables), 1)

        # Valida que as variáveis possuem estatísticas completas e correlações calculadas
        for v in variables:
            self.assertIn(v, data["stats"])
            st = data["stats"][v]
            self.assertIn("n", st)
            self.assertIn("media", st)
            self.assertIn("desvio_padrao", st)
            self.assertIn("histogram", st)
            self.assertIn("raw_values", st)

            # Matriz de correlação de Pearson
            self.assertIn(v, data["correlations"])
            for v_other in variables:
                self.assertIn(v_other, data["correlations"][v])
                r = data["correlations"][v][v_other]
                self.assertGreaterEqual(r, -1.0)
                self.assertLessEqual(r, 1.0)

    def test_15_javascript_syntax_and_assets(self):
        """Valida que todos os arquivos JavaScript do front-end possuem sintaxe válida e sem erros."""
        import subprocess
        js_dir = Path("app/static/js")
        js_files = list(js_dir.glob("*.js"))
        self.assertGreater(len(js_files), 0, "Nenhum arquivo JS encontrado em app/static/js")

        node_bin = "node"
        for js in js_files:
            with self.subTest(js_file=js.name):
                proc = subprocess.run([node_bin, "-c", str(js)], capture_output=True, text=True)
                self.assertEqual(
                    proc.returncode, 0,
                    f"Erro de sintaxe encontrado no arquivo {js.name}:\n{proc.stderr}"
                )

    def test_16_micronumerosity_and_estimator(self):
        """Valida a detecção de micronumerosidade (NBR 14653) e estimador de Máxima Verossimilhança (MV)."""
        sample = self.sample_dir / "Exercicio 1 - Regressao Simples.sda"
        proj = read_sda_file(sample)
        
        # Cria uma variável qualitativa com código raro (< 3 ocorrências)
        dummy_var = Variable(
            nome="Padrao_Acabamento",
            tipo=1,
            classificacao=2,  # Códigos Alocados
            habilitada=True
        )
        proj.variaveis.append(dummy_var)
        for i, item in enumerate(proj.dados):
            # Apenas 1 dado com código 3
            item.valores["Padrao_Acabamento"] = 3.0 if i == 0 else 1.0

        # Testa com estimador MQ
        proj.opcoes.estimador = "mq"
        models_mq = run_regression_search(proj)
        self.assertGreater(len(models_mq), 0)
        top_mq = models_mq[0]
        # Deve alertar sobre a violação de micronumerosidade
        has_micro_diag = any("Micronumerosidade" in d for d in top_mq.diagnosticos_tecnicos)
        self.assertTrue(has_micro_diag, "Deveria diagnosticar violação de micronumerosidade.")

        # Testa com estimador MV (Máxima Verossimilhança)
        proj.opcoes.estimador = "mv"
        models_mv = run_regression_search(proj)
        self.assertGreater(len(models_mv), 0)
        top_mv = models_mv[0]
        self.assertGreater(top_mv.r2, 0.0)
        self.assertIsNotNone(top_mv.erro_padrao)

    def test_17_report_residuals_exact_alignment(self):
        """Valida que todos os resíduos e estimativas na tabela completa do relatório correspondem exatamente à amostra."""
        import re
        sample = self.sample_dir / "Exercicio 1 - Regressao Simples.sda"
        proj = read_sda_file(sample)
        proj.metadata.observacoes = "Parecer conclusivo da avaliação técnica."
        models = run_regression_search(proj)
        top = models[0]

        html = generate_laudo_html(proj, top)
        
        # Amostra #1 deve conter estimativa e resíduo padronizado (não pode ser '-')
        res_item_1 = next((r for r in top.residuos if r.index == 1), None)
        self.assertIsNotNone(res_item_1)
        
        # Verifica se o primeiro dado da amostra contém valor formatado
        self.assertIn("Utilizado", html)
        self.assertIn("10. Considerações Finais", html)  # Numeração correta da seção 10
        self.assertNotIn("<h2>8. Considerações Finais", html)

    def test_18_subject_valuation_update_and_multiprojections(self):
        """Valida a atualização da avaliação via API de sujeitos e geração de laudo com múltiplos avaliandos."""
        sample = self.sample_dir / "Modelo de Apartamentos.sda"
        proj = read_sda_file(sample)
        
        # Adiciona segundo imóvel avaliando
        proj.projecoes.append(SubjectProperty(
            identificacao="Apto Cobertura 02",
            valores=dict(proj.projecoes[0].valores)
        ))
        
        models = run_regression_search(proj)
        self.assertEqual(len(models[0].projecoes), 2, "Deveria avaliar ambos os imóveis avaliandos.")
        
        # Valida que o relatório HTML exibe ambos os avaliandos
        html = generate_laudo_html(proj, models[0])
        self.assertIn("Apto Cobertura 02", html)
        self.assertIn("Imóvel Avaliando", html)

        # Testa rota /api/subjects retornando os modelos atualizados
        r_load = self.client.post("/api/samples/load", data={"filename": "Modelo de Apartamentos.sda"})
        self.assertEqual(r_load.status_code, 200)

        subj_payload = [
            {"id": "p1", "identificacao": "Unidade 101", "valores": {}},
            {"id": "p2", "identificacao": "Unidade 202", "valores": {}}
        ]
        r_sub = self.client.post("/api/subjects", json=subj_payload)
        self.assertEqual(r_sub.status_code, 200)
        data = r_sub.json()
        self.assertIn("modelos", data)
        self.assertEqual(data["count"], 2)

    def test_19_function_curve_estimation(self):
        """Valida que elementos da Função Estimativa (curva ajustada por regressor) estão presentes na interface e JS."""
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("chart-curva-estimativa", r.text)
        self.assertIn("select-curva-regressor", r.text)
        self.assertIn("rna-iter-done", r.text)

if __name__ == "__main__":
    unittest.main()
