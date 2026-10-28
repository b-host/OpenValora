<p align="center">
  <img src="OpenValora.png" alt="OpenValora Logo" width="180" style="border-radius: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
</p>

<h1 align="center">OpenValora 🏢📊</h1>

<p align="center">
  <strong>Software Aberto de Inferência Estatística e Engenharia de Avaliações</strong><br>
  Ambiente moderno e 100% offline para Avaliação Imobiliária por Regressão Linear Múltipla e Redes Neurais Artificiais.<br>
  Executa como <strong>aplicativo desktop nativo</strong> ou como <strong>servidor local/Docker</strong>.<br>
  Desenvolvido em estrita conformidade com as normas <strong>ABNT NBR 14653</strong>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Versão-0.1.0-blue.svg" alt="Versão 0.1.0" />
  <img src="https://img.shields.io/badge/Licença-MIT%20(Open%20Source)-green.svg" alt="Licença MIT" />
  <img src="https://img.shields.io/badge/Formato%20Padrão-.valora%20(Open%20Source)-brightgreen.svg" alt="Formato Aberto" />
  <img src="https://img.shields.io/badge/Gerenciador-uv%20(Astral)-purple.svg" alt="uv package manager" />
  <img src="https://img.shields.io/badge/Interface-Janela%20Nativa%20(Desktop)-success.svg" alt="Native Window" />
  <img src="https://img.shields.io/badge/Docker-Pronto-2496ED.svg" alt="Docker Ready" />
  <img src="https://img.shields.io/badge/Norma-ABNT%20NBR%2014653--2-success.svg" alt="NBR 14653-2" />
  <img src="https://img.shields.io/badge/Plataformas-Linux%20(AppImage)%20%7C%20Windows%20%7C%20macOS-informational.svg" alt="Plataformas" />
</p>

---

## 📌 Sumário
1. [Visão Geral](#-visão-geral)
2. [Aplicação Nativa Desktop vs Servidor Local](#-aplicação-nativa-desktop-vs-servidor-local)
3. [Normas Brasileiras Utilizadas](#-normas-brasileiras-utilizadas)
4. [Como Executar](#-como-executar)
   - [Opção 1: Executável Nativo / AppImage (Sem instalação)](#opção-1-executável-nativo--appimage-recomendado)
   - [Opção 2: Ambiente Python com UV (Astral)](#opção-2-ambiente-python-local-com-ferramenta-uv)
   - [Opção 3: Executar via Docker / Docker Compose](#opção-3-executar-via-docker-ou-docker-compose)
5. [Guia de Uso Passo a Passo](#-guia-de-uso-passo-a-passo)
6. [Módulos de Avaliação](#-módulos-de-avaliação)
   - [Regressão Linear Múltipla (7 Transformações)](#1-regressão-linear-múltipla-com-linearização)
   - [Redes Neurais Artificiais (RNA / MLP)](#2-redes-neurais-artificiais-mlp)
   - [Enquadramento Automático NBR 14653-2](#3-enquadramento-normativo-automático-tabelas-1-e-2)
   - [Laudo Técnico Completo](#4-laudo-técnico-completo-de-avaliação)
7. [Formatos de Arquivos Suportados (.sda, .xlsx, .csv)](#-formatos-de-arquivos-suportados)
8. [Empacotamento e Distribuição](#-empacotamento-e-distribuição)
9. [Estrutura do Repositório](#-estrutura-do-repositório)

---

## 🧭 Visão Geral

O **OpenValora** é uma solução completa para engenheiros civis, arquitetos, agrônomos, peritos judiciais e avaliadores imobiliários. Ele oferece uma alternativa moderna, aberta e auditável a ferramentas proprietárias legadas de avaliação imobiliária:

- **Janela Nativa do Sistema:** Nos pacotes buildados (AppImage no Linux e `.exe` no Windows), o OpenValora abre diretamente como uma **janela desktop nativa** do sistema operacional, sem depender de janelas ou abas soltas no navegador web.
- **Privacidade e Modo 100% Offline:** Não requer conexão com a internet — nenhum dado amostral ou sigiloso sai do seu computador.
- **Compatibilidade Retroativa:** Lê e grava nativamente arquivos binários de avaliação (`.sda` BIFF8/OLE) com total fidelidade, além de importar e exportar planilhas Excel (`.xlsx`, `.xls`) e `.csv`.
- **Gerenciamento Moderno com UV:** Configurado com a ferramenta `uv` da Astral para resolução e instalação de dependências instantâneas.

---

## 🖥️ Aplicação Nativa Desktop vs Servidor Local

O OpenValora pode ser executado em dois modos:

1. **Modo Janela Nativa (Padrão para AppImage, Windows e Desktop):**
   - Utiliza WebView nativo acelerado por hardware (**WebKitGTK** no Linux sob Wayland/X11 e **Microsoft Edge WebView2** no Windows).
   - Não exibe barras de endereços, abas ou elementos de navegadores comuns.
   - Ao fechar a janela do programa, o aplicativo e seus processos em segundo plano são finalizados imediatamente.
2. **Modo Servidor Web / Docker (`--server`):**
   - Ideal para execução em servidores locais de rede, laboratórios de engenharia ou containers Docker (`docker compose up`).
   - Disponibiliza a interface em `http://localhost:8000` (ou IP de rede local) para qualquer dispositivo conectado.

---

## 📐 Normas Brasileiras Utilizadas

O OpenValora atende estritamente às normas técnicas da **ABNT (Associação Brasileira de Normas Técnicas)** e às diretrizes periciais do **IBAPE** e da **SOBREA**:

### 1. ABNT NBR 14653-1: Avaliação de bens — Procedimentos gerais
- **Classificação Metodológica:** Aplicação do **Método Comparativo Direto de Dados de Mercado (MCDDM)**.
- **Transparência e Ética Pericial:** Rastreabilidade dos cálculos matriciais, identificação de fontes de dados e fundamentação clara das premissas.
- **Nível de Significância:** Padrão regulamentar de 80% para intervalos de probabilidade e estimativas centrais.

### 2. ABNT NBR 14653-2: Avaliação de bens — Imóveis urbanos
Núcleo matemático do OpenValora:
- **Tabela 1 — Graus de Fundamentação no MCDDM:**
  - **Item 1 (Caracterização dos imóveis):** Identificação completa dos atributos físicos, de acabamento e de localização.
  - **Item 2 (Quantidade mínima de dados de mercado):**
    - Grau III: $N \ge 6(k + 1)$
    - Grau II: $N \ge 3(k + 1)$
    - Grau I: $N \ge 3(k + 1)$ (admitido inferior com justificativa).
  - **Item 3 (Identificação das fontes):** Dados amostrais auditáveis com endereços e características.
  - **Item 4 (Significância máxima dos regressores — Teste $t$ de Student bicaudal):**
    - Grau III: $\alpha \le 10\%$
    - Grau II: $\alpha \le 20\%$
    - Grau I: $\alpha \le 30\%$
  - **Item 5 (Significância global do modelo — Teste $F$ de Snedecor):**
    - Grau III: $\alpha_F \le 1\%$
    - Grau II: $\alpha_F \le 2\%$
    - Grau I: $\alpha_F \le 5\%$
  - **Item 6 (Extrapolação amostral):**
    - Grau III: Sem extrapolação nos atributos do avaliando.
    - Grau II: Extrapolação admitida para até 1 variável dentro dos limites normativos ($\le 100\%$ de margem).
    - Grau I: Extrapolação admitida para até 2 variáveis.
- **Tabela 2 — Graus de Precisão no MCDDM:**
  - Amplitude do Intervalo de Confiança a 80%:
    - **Grau III:** Amplitude $\le 30\%$
    - **Grau II:** Amplitude $\le 40\%$
    - **Grau I:** Amplitude $\le 50\%$
- **Salvaguardas e Requisitos Econômicos:**
  - **Rejeição por Inversão de Sinal:** Validação automática da derivada parcial $\frac{\partial \hat{y}}{\partial X_j}$ para garantir consistência física e econômica. Modelos com sinal invertido são rebaixados para **"Não Enquadrado"**.
  - **Campo de Arbítrio ($\pm 15\%$):** Aplicação regulamentar do intervalo de $\pm 15\%$ (item 8.2.1.6).
  - **Arredondamento Normativo (1%):** Arredondamento do valor final da avaliação dentro da margem de 1%.

### 3. ABNT NBR 14653-3: Imóveis rurais
- Suporte a variáveis de aptidão agrícola, terra nua (VTN), benfeitorias, pastagens e distâncias a polos de escoamento.

### 4. ABNT NBR 14653-4: Empreendimentos
- Variáveis de escala, absorção comercial e projeções analíticas de liquidação.

---

## ⚡ Como Executar

### Opção 1: Executável Nativo / AppImage (Recomendado)

Não requer instalação de Python nem dependências externas:

- **Linux (AppImage com Wayland e X11 nativo):**
  1. Baixe `OpenValora-Linux-x86_64.AppImage` da pasta `dist/` ou da aba Releases do GitHub.
  2. Conceda permissão e execute:
     ```bash
     chmod +x OpenValora-Linux-x86_64.AppImage
     ./OpenValora-Linux-x86_64.AppImage
     ```
  3. A janela nativa do OpenValora abrirá imediatamente no seu desktop!

- **Windows (10 / 11 64-bit Portátil):**
  1. Baixe `OpenValora-Windows-x64.zip`.
  2. Extraia os arquivos e execute `openvalora.exe`.

---

### Opção 2: Ambiente Python Local com Ferramenta UV

O OpenValora utiliza a ferramenta **`uv`** (da Astral) para gerenciamento de dependências ultrarrápido:

#### 1. Instalar o `uv` (caso ainda não possua):
```bash
# Linux / macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 2. Configurar o ambiente com `uv`:
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/OpenValora.git
cd OpenValora

# Crie o ambiente virtual
uv venv

# Instale as dependências via uv
uv pip install -r requirements.txt
```

#### 3. Executar o OpenValora:
```bash
# Modo Janela Nativa (Desktop):
uv run main.py
# ou simplesmente:
./run.sh

# Modo Servidor Local (para acessar via navegador ou rede):
uv run main.py --server --port 8000
```

---

### Opção 3: Executar via Docker ou Docker Compose

Se preferir rodar em um container isolado:

#### Usando Docker Compose:
```bash
docker compose up -d --build
```
Acesse no navegador em: **`http://localhost:8000`**

Para parar o container:
```bash
docker compose down
```

#### Usando Docker / Podman CLI:
```bash
# Construir a imagem com uv:
docker build -t openvalora .

# Executar o container:
docker run -d -p 8000:8000 --name openvalora openvalora
```

---

## 📖 Guia de Uso Passo a Passo

O fluxo de avaliação pericial segue uma sequência lógica em abas:

```
[1. Projeto] ➔ [2. Variáveis] ➔ [3. Amostra] ➔ [4. Exploratória] ➔ [5. Regressão / 6. RNA] ➔ [7. Avaliando] ➔ [8. Laudo NBR]
```

1. **Aba Projeto:** Preencha os dados do laudo, engenheiro responsável, finalidade e tipologia do imóvel.
2. **Aba Variáveis:** Configure as variáveis independentes e a dependente ($R\$/m^2$ ou $R\$$ total). Use o botão **"Catálogo ABNT"** para puxar mais de 340 variáveis padronizadas.
3. **Aba Dados da Amostra:** Preencha a tabela de imóveis comparáveis ou importe de arquivos `.sda`, `.xlsx` ou `.csv`. Habilite ou desabilite dados com 1 clique.
4. **Aba Análise Exploratória:** Examine a matriz de correlação de Pearson, estatísticas descritivas (média, mediana, desvio padrão, CV%), histogramas e gráficos de dispersão.
5. **Aba Regressão Linear:** Clique em **"Calcular Regressão"**. O OpenValora analisa todas as combinações de transformações, gera a tabela ANOVA, $t$-Student, $VIF$, Durbin-Watson e ordena os melhores modelos.
6. **Aba Redes Neurais (RNA):** Se desejar modelagem não-linear com inteligência artificial, treine a rede MLP com otimizador quasi-Newton (L-BFGS), acompanhando a curva de perda (Loss curve).
7. **Aba Imóvel Avaliando:** Insira as características do imóvel periciado e obtenha instantaneamente o valor unitário, valor total, intervalo de confiança a 80%, campo de arbítrio ($\pm 15\%$) e valor arredondado normativo.
8. **Aba Laudo NBR 14653:** Visualize o laudo pericial completo estruturado e clique em **"Imprimir / PDF"** para gerar o documento formal para assinatura.

---

## 🛠️ Módulos de Avaliação

### 1. Regressão Linear Múltipla com Linearização
- **7 Transformações Matemáticas:**
  1. Direta ($x$)
  2. Inversa ($1/x$)
  3. Logarítmica natural ($\ln x$)
  4. Quadrática ($x^2$)
  5. Inversa Quadrática ($1/x^2$)
  6. Raiz Quadrada ($\sqrt{x}$)
  7. Inversa da Raiz ($1/\sqrt{x}$)
- **Diagnóstico Completo de Resíduos:**
  - Resíduos Ordinários, Padronizados e Studentizados.
  - Distância de Cook ($D_i$) e Leverage ($h_{ii}$) para pontos de influência.
  - Teste de Homocedasticidade de Breusch-Pagan.
  - Testes de Normalidade de Kolmogorov-Smirnov e Shapiro-Wilk.
  - Estatística de Durbin-Watson ($DW$) para autocorrelação.

### 2. Redes Neurais Artificiais (MLP)
- Módulo Perceptron Multicamadas com otimizador L-BFGS (Quasi-Newton) e Adam.
- Funções de ativação: Logística (Sigmoide), ReLU e Tanh.
- Técnica de Bagging para redução de variância amostral.

### 3. Enquadramento Normativo Automático (Tabelas 1 e 2)
- Verificação contínua dos critérios dos Graus III, II e I de Fundamentação e Precisão.
- Rejeição e alerta imediato caso ocorra inversão física/econômica de sinal.

### 4. Laudo Técnico Completo de Avaliação
- Emissão instantânea do relatório pericial de avaliação em HTML/PDF pronto para impressão e assinatura digital.

---

## 💾 Formatos de Arquivos Suportados (Padrão Aberto & Legado)

O OpenValora prioriza **formatos de código aberto e interoperáveis por padrão**, mantendo total compatibilidade retroativa com softwares legados da área pericial:

| Formato | Extensão | Padrão | Leitura | Gravação | Descrição Técnica |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **OpenValora Nativo** | `.valora` | ⭐ Sim | ✅ | ✅ | **Padrão Aberto Open Source:** Baseado em JSON estruturado com codificação UTF-8. Salva 100% dos dados, variáveis, projeções, opções, modelos calculados e configurações de RNA de forma auditável e independente de fornecedor. |
| **Planilha de Avaliação Legada** | `.sda` | Não | ✅ | ✅ | **Compatibilidade Legada:** Formato binário clássico de planilha (BIFF8/OLE2), preservando a troca de arquivos com avaliadores que utilizam formatos legados de engenharia de avaliações. |
| **Excel Moderno** | `.xlsx` | Não | ✅ | ✅ | Planilhas Excel com abas estruturadas de Dados, Variáveis e Modelos Calculados. |
| **Excel 97-2003** | `.xls` | Não | ✅ | ✅ | Planilhas clássicas legadas. |
| **Arquivo CSV** | `.csv` | Não | ✅ | ❌ | Exportação e importação tabular com detecção automática de acentos (UTF-8 e Windows-1252/CP1252). |

---

## 📦 Empacotamento Multiplataforma e Builds Automáticos

O OpenValora atende aos três principais ecossistemas operacionais:

1. **Linux (AppImage Universal x86_64):**
   - Pacote portátil único sem instalação, com suporte nativo acelerado tanto para **Wayland** quanto para **X11**.
   - Executa em qualquer distribuição moderna (Ubuntu, Debian, Fedora, Arch Linux, Pop!_OS, openSUSE, etc.).
2. **Windows (Portátil 64-bit):**
   - Pacote `.zip` independente com executável nativo acelerado via Microsoft Edge WebView2.
3. **macOS (Universal Apple Silicon & Intel):**
   - Pacote `.zip` com bundle nativo do macOS (`OpenValora.app`) utilizando WebKit/Cocoa.

### 🤖 Builds Automatizados via GitHub Actions
A cada `git push` nas branches `master` ou `main` (ou na criação de tags de versão `v*`), o fluxo de CI/CD em [`.github/workflows/release.yml`](.github/workflows/release.yml) compila automaticamente os 3 executáveis:
- Compila o binário Linux e empacota o **AppImage Universal**.
- Compila o executável Windows e gera o **.zip Portátil**.
- Compila o bundle macOS e gera o **.zip Universal**.
- Disponibiliza os artefatos para download imediato na aba **Actions** e atualiza o release contínuo (`latest`).

Para compilar localmente:

```bash
# Compilar a versão final nativa para Linux (AppImage com Wayland e X11):
./build_appimage.sh

# Compilar para Windows (PowerShell/CMD):
pyinstaller --clean --noconfirm openvalora.spec

# Compilar para macOS (Terminal):
pyinstaller --clean --noconfirm openvalora.spec
```

---

## 🏗️ Estrutura do Repositório

```
OpenValora/
├── OpenValora.png                  # Logotipo e ícone oficial em alta resolução (1254x1254)
├── LICENSE                         # Licença MIT de Código Aberto
├── TODO.md                         # Lista de metas e melhorias do projeto
├── Dockerfile                      # Imagem Docker otimizada com a ferramenta uv
├── docker-compose.yml              # Orquestração de container pronta para uso
├── pyproject.toml                  # Configuração de projeto e dependências com uv
├── requirements.txt                # Dependências Python
├── main.py                         # Ponto de entrada (Janela Nativa ou Servidor Web)
├── run.sh                          # Script de inicialização rápida
├── build_appimage.sh               # Script de geração do AppImage nativo
├── openvalora.spec                 # Especificação PyInstaller para Linux, Windows e macOS
├── .github/workflows/release.yml   # Pipeline CI/CD com build automático em cada commit
├── test_suite.py                   # Suíte de testes automatizados (10/10 testes)
├── app/
│   ├── main.py                     # API FastAPI, rotas de cálculo e persistência do projeto
│   ├── core/                       # Núcleo de cálculo estatístico e conformidade NBR
│   │   ├── models.py               # Modelos Pydantic (.valora)
│   │   ├── io_sda.py               # Leitor/escritor .sda, .xlsx, .csv
│   │   ├── regression.py           # Motor de Regressão Linear Múltipla
│   │   ├── statistics.py           # DW, ANOVA, Cook, VIF, Breusch-Pagan, KS
│   │   ├── nbr14653.py             # Enquadramento automático ABNT NBR 14653-2
│   │   ├── valuation.py            # Avaliação de sujeitos, IC 80% e arredondamento
│   │   ├── neural_network.py       # Módulo de Redes Neurais (MLP Regressor)
│   │   ├── var_library.py          # Catálogo de variáveis padronizadas
│   │   ├── var_catalog.json        # 344+ variáveis ABNT
│   │   └── report_generator.py     # Gerador de Laudos de Avaliação
│   ├── static/                     # Assets estáticos 100% offline
│   │   ├── css/styles.css          # Estilização com Dark Mode
│   │   ├── js/app.js               # Controlador reativo da interface
│   │   ├── js/charts.js            # Gráficos interativos com Chart.js
│   │   ├── img/logo.png            # Logotipo oficial
│   │   └── favicon.png             # Ícone do navegador
│   └── templates/
│       └── index.html              # Interface do usuário com modal Sobre e formatos abertos
├── packaging/                      # Arquivos de empacotamento desktop
│   ├── AppRun                      # Wrapper com compatibilidade Wayland e X11
│   ├── openvalora.desktop          # Entrada FreeDesktop para o menu de apps
│   ├── OpenValora.png              # Ícone original do aplicativo
│   ├── openvalora.png              # Ícone redimensionado para Linux
│   ├── openvalora.ico              # Ícone multirresolução para o executável Windows
│   └── openvalora.icns             # Ícone Apple ICNS para macOS
└── sample_data/                    # Acervo com mais de 12 modelos reais de avaliação (.sda)
```

---

## 👥 Licença de Código Aberto (MIT)

O **OpenValora** é um software livre distribuído sob a licença [MIT](LICENSE).

Você tem total liberdade para:
- Usar o software para fins pessoais, acadêmicos, profissionais, periciais ou comerciais sem custos ou restrições.
- Modificar, auditar, estender e incorporar o código-fonte aos seus próprios fluxos de trabalho.
- Distribuir cópias sem restrições ou bloqueios por licenças de terceiros.
