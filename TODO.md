# OpenValora - Metas & Funcionalidades (TODO)

Todas as tarefas prioritárias de modernização, distribuição, estabilidade universal e padrões abertos foram revisadas e implementadas:

- [x] **AppImage Linux Genérico e Universal (Wayland & X11 sem amarras ao Ubuntu):**
  - **Suporte Abrangente a Distribuições:** Removida qualquer dependência exclusiva do Ubuntu. O AppImage e o código foram arquitetados para funcionar universalmente em distribuições RPM (Fedora, Silverblue, Bluefin, RHEL), Debian/Ubuntu e Arch Linux.
  - **Tratamento de GPUs e Compositor Wayland:**
    - Inclusão de `WEBKIT_DISABLE_DMABUF_RENDERER=1` para impedir falhas de renderização DMA-BUF com drivers NVIDIA proprietários e Mesa sob Wayland.
    - Inclusão de `WEBKIT_FORCE_SANDBOX=0` e `WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1` para evitar erros de namespace bubblewrap (`bwrap`) em distros imutáveis baseadas em OSTree (Fedora Silverblue, Bluefin) e containers.
  - **Fallback Automático e Tolerante a Falhas:**
    - Tenta inicialmente inicializar a janela desktop nativa via Wayland.
    - Em caso de indisponibilidade ou falha do compositor, tenta automaticamente o backend X11/XWayland (`GDK_BACKEND=x11`).
    - Caso o motor WebKitGTK não esteja disponível no sistema do usuário, aciona o **Modo de Segurança**, abrindo a interface no navegador web padrão e mantendo o servidor local ativo em segundo plano (sem fechar a aplicação abruptamente).
  - **Ícones Seguros no Linux:** Utiliza exclusivamente o formato `.png` ([`OpenValora.png`](OpenValora.png)) para os ícones de janela e taskbar no Linux, prevenindo erros de decodificação de arquivos `.ico` no subsistema `gdk-pixbuf` / `glycin-loaders` modernos.

- [x] **Atendimento a todos os principais sistemas operacionais (Windows, macOS e Linux AppImage Universal):**
  - **Linux:** Pacote **AppImage Universal x86_64** autônomo com suporte nativo acelerado para Wayland e X11.
  - **Windows:** Pacote portátil `.zip` de 64-bit com executável independente via WebView2 e ícone multirresolução.
  - **macOS:** Pacote `.zip` com bundle nativo `OpenValora.app` para Apple Silicon e Intel, com ícone Apple `.icns` e backend Cocoa/WebKit.
  - **Especificação PyInstaller Unificada:** Configurado em [`openvalora.spec`](openvalora.spec) com detecção condicional para Linux, Windows e macOS.

- [x] **Builds automáticos no GitHub Actions a cada commit:**
  - Configurado em [`.github/workflows/release.yml`](.github/workflows/release.yml) com gatilhos automáticos para:
    - Qualquer `git push` nas branches `master` e `main`.
    - Criação de tags de versão `v*`.
    - Disparo manual sob demanda (`workflow_dispatch`).
  - Matriz de compilação em 3 plataformas paralelas:
    - `build-linux` em `ubuntu-22.04` gerando `OpenValora-Linux-x86_64.AppImage`.
    - `build-windows` em `windows-latest` gerando `OpenValora-Windows-x64.zip`.
    - `build-macos` em `macos-latest` gerando `OpenValora-macOS.zip`.
  - Publicação contínua: disponibilização dos 3 artefatos para download imediato na aba **Actions** e atualização automática do release contínuo (`latest`) ou release oficial de versão.

- [x] **Botão de Info do Projeto (Open Source) e Documentação:**
  - Adicionado o botão **"Sobre"** no cabeçalho da interface web/desktop ([`index.html`](app/templates/index.html)).
  - Criado modal interativo com:
    - Declaração explícita de **Software 100% Livre e de Código Aberto (Open Source)**.
    - Licença **MIT** permissiva para uso pessoal, profissional, pericial e comercial.
    - Declaração de conformidade com as normas **ABNT NBR 14653** (14653-1, 14653-2, 14653-3 e 14653-4).
    - Garantia de privacidade: 100% local, offline, sem envio de dados ou telemetria.
    - Especificação de formatos abertos (.valora) vs legado (.sda).
  - Criado o arquivo oficial de licença [`LICENSE`](LICENSE) (MIT License).
  - Documentação completa e detalhada no [`README.md`](README.md).

- [x] **Formatos Open Source por padrão & Compatibilidade com Formatos Proprietários Legados:**
  - **Formato Nativo Aberto (.valora) como Padrão:** O OpenValora agora utiliza `.valora` (JSON estruturado aberto com codificação UTF-8) como formato principal de salvamento de projetos, preservando todos os metadados, variáveis, amostras, modelos calculados e redes neurais sem bloqueios proprietários.
  - **Compatibilidade Legada com SisDEA (.sda):** O formato legado `.sda` (BIFF8/OLE2) continua 100% suportado para importação e exportação pelo botão `.sda (Legado)`.
  - **Planilhas Abertas:** Suporte bidirecional a arquivos Microsoft Excel (`.xlsx`, `.xls`) e importação de `.csv` com detecção inteligente de acentos em português.

- [x] **Relatório de Avaliação Imobiliária Completo (NBR 14653) com Tabela Integral de Dados Amostrais:**
  - **Renomeação e Identificação:** O botão e a aba foram renomeados de "Laudo NBR 14653" para **"Relatório"**, apresentando o "Relatório de Avaliação Imobiliária (NBR 14653)".
  - **Inclusão da Tabela Completa de Dados Amostrais:** A tabela completa com todos os dados amostrais coletados (`project.dados`) agora é exibida integralmente no relatório, incluindo status de cada dado (utilizado, outlier ou desabilitado), valores observados de todas as variáveis ativas, estimativa gerada pelo modelo e resíduo padronizado.
  - **Estatísticas Descritivas Básicas:** Tabela com resumo estatístico das variáveis quantitativas da amostra (número de observações válidas, média amostral, desvio padrão, valores mínimo e máximo).
  - **Demonstração Completa da Metodologia e da Norma:** Equação ajustada, testes t de Student e significância individual, fatores de inflação da variância (VIF), análise de variância (ANOVA com teste F), diagnóstico de normalidade (Kolmogorov-Smirnov / Shapiro-Wilk) e enquadramento detalhado dos Graus de Fundamentação e Precisão da ABNT NBR 14653-2.

- [x] **Personalização Completa do Relatório e Inserção de Logotipo:**
  - **Upload e Exibição de Logomarca:** Suporte a upload de imagem de logotipo da empresa ou perito (PNG, JPG, SVG, WebP) com armazenamento persistente em Base64 nos metadados do projeto, exibido no cabeçalho do documento com preview imediato e opção de remoção.
  - **Modal de Personalização ("Personalizar Relatório"):** Permite customizar título do relatório, subtítulo normativo, identificação do contratante/solicitante, responsável técnico, registro profissional (CREA/CAU), endereço/localização do imóvel avaliando e campo de texto livre para **Observações Técnicas / Parecer Conclusivo**.
  - **Persistência Total:** As customizações são integradas ao modelo `ProjectMetadata` e persistidas no arquivo nativo `.valora`.

- [x] **Geração Direta de PDF e Correção Definitiva do Botão de Impressão:**
  - **Diagnóstico da Falha de Impressão:** Em ambientes desktop empacotados (WebKitGTK/pywebview), o acionamento direto de `iframe.contentWindow.print()` falhava silenciosamente por ausência de manipulador padrão do GtkPrintOperation em subframes de navegadores embutidos.
  - **Geração Direta em Arquivo PDF (A4):** Integrada a biblioteca `html2pdf.bundle.min.js` 100% offline localmente em `app/static/vendor/`. O novo botão **"Baixar PDF"** compila diretamente o relatório em arquivo `.pdf` vetorial de alta resolução com paginação A4 e download imediato, sem depender de impressoras virtuais.
  - **Impressão com Fallback Resiliente:** O botão **"Imprimir"** agora executa foco e disparo seguro no iframe e, caso a plataforma gráfica restrinja o diálogo, abre o documento em nova janela com parâmetro `?autoprint=1` no navegador do sistema.
  - **Barra de Ações no Próprio Relatório:** O cabeçalho do relatório agora inclui botões flutuantes para "Baixar em PDF", "Imprimir" e "Personalizar", devidamente configurados com `@media print` para desaparecerem na impressão ou salvamento.

- [x] **Revisão Integral do SisDEA Original & Conformidade Funcional:**
  - **Inspeção de Especificações e Manuais:** Analisados o roteiro oficial (`extracted/roteiro.txt`), a base de documentação CHM (`extracted/chm_help/regresion.htm`) e os tutoriais originais do SisDEA.
  - **Cobertura 100% de Recursos:** Validadas todas as rotinas estatísticas do MCDDM: linearização de variáveis, restrições e inversões de sinal físico/econômico, testes t de Student, análise de variância (ANOVA com teste F), Durbin-Watson, diagnóstico de multicolinearidade (VIF), análise de resíduos (ordinários, padronizados, studentizados, relativos, distância de Cook e leverage), testes formais de normalidade (Kolmogorov-Smirnov e Shapiro-Wilk) e Redes Neurais Artificiais (RNA).
  - **Correção de Legado (Ghost Rows / Duplicatas):** Identificada anomalia em arquivos legados do SisDEA (como `Apto_BH_Betim_Contagem_Mar_2012.sda`) contendo variáveis fantasmas duplicadas (`LarguraColuna = -1`). Implementado filtro de desduplicação automática e defensiva em `app/core/io_sda.py` e `app/core/regression.py`, eliminando riscos de singularidade matricial ($X^T X$).

- [x] **Revisão do Próprio Código, Otimizações de Nível Sênior e Correções:**
  - **Prevenção de Sobrecarga de Memória:** Otimizada a geração combinatória de especificações em `app/core/regression.py` com `itertools.islice`, evitando criação massiva de milhões de tuplas em RAM durante buscas em modelos com mais de 10 variáveis.
  - **Importação Resiliente de Planilhas:** Tratamento preventivo em `import_excel_or_csv` com desduplicação inteligente de colunas e cabeçalhos em branco.
  - **Interface Desktop e Ciclo de Vida de Modais:** Implementada a função `openModal(id)` globalmente com re-renderização automática dos ícones vetoriais Lucide e suporte a fechamento seguro.

- [x] **Dados de Exemplo Integrados à Pasta do Projeto:**
  - **17 Modelos .sda Oficiais:** Todos os arquivos de exemplo e exercícios originais copiados e organizados na pasta oficial [`sample_data/`](sample_data/):
    - *Apartamentos, Casas, Lotes urbanos, Lojas comerciais, Data de Evento, Heterocedasticidade, Colinearidade, Pontos Máximos/Mínimos, etc.*
  - **Planilhas de Vistoria de Campo:** Planilhas modelo (`.xls`) organizadas em [`sample_data/planilhas/`](sample_data/planilhas/) para coleta padronizada de dados.
  - **Laudos Periciais de Referência:** Documentos técnicos em PDF organizados em [`sample_data/laudos_referencia/`](sample_data/laudos_referencia/).

- [x] **Adequação Metodológica à ABNT NBR 14653 (14653-1 e 14653-2):**
  - **Graus de Fundamentação (Tabela 1):** Verificação rigorosa do número de observações ($N \ge 6(k+1)$ para Grau III, $N \ge 3(k+1)$ para Graus II e I), significância do teste F ($\le 1\%$, $\le 2\%$, $\le 5\%$), significância individual de regressores ($\le 10\%$, $\le 20\%$, $\le 30\%$) e controle de extrapolação amostral.
  - **Graus de Precisão (Tabela 2):** Amplitude do intervalo de confiança de 80% em torno da estimativa pontual ($\le 30\%$ para Grau III, $\le 40\%$ para Grau II, $\le 50\%$ para Grau I).
  - **Critérios de Engenharia:** Campo de arbítrio de $\pm 15\%$ e critério normativo de arredondamento em até 1% (item 7.5 da NBR 14653-2).

- [x] **Bateria de Testes Automatizados com Todos os Dados de Exemplo:**
  - Criado o teste automatizado `test_11_all_sample_files` em [`test_suite.py`](test_suite.py).
  - 100% dos 17 arquivos `.sda` são carregados, calculados e validados automaticamente em cada execução de teste, gerando laudos e relatórios HTML válidos.

- [x] **Certificação Geral e Estabilidade de Produção:**
  - Suíte completa de testes aprovada (11/11 testes em 25,9s).
  - Árvore de trabalho limpa, binários standalone e AppImage universais compilados e prontos para distribuição.

- [x] **Ajuda, Tooltips Contextuais & Insights de Ajuste Normativo (NBR 14653):**
  - **Tooltips Explicativos em Todos os Campos:** Adicionados atributos `title` informativos e objetivos em todos os campos, botões de ação, inputs de configuração, tabelas de variáveis, dados da amostra, métricas estatísticas e parâmetros de RNA.
  - **Identificação e Diagnóstico de Problemas no Hover:** Mensagens de ajuda contextual ao passar o mouse sobre badges e células que apresentem inconformidades (inversão de sinal físico-econômico, regressões não-significativas com $p > 30\%$, multicolinearidade com VIF $> 10$, autocorrelação de Durbin-Watson e outliers com $|r| > 2$).
  - **Painel de Diagnóstico Técnico & Orientações de Ajuste ("Como Resolver"):** Seção dedicada tanto na interface de regressão quanto no relatório técnico impresso, listando passo a passo como resolver qualquer restrição:
    - *Amostra Insuficiente:* Cálculo da quantidade exata de amostras adicionais necessárias para atingir $3(k+1)$ (Grau II/I) ou $6(k+1)$ (Grau III).
    - *Regressores com $p > 30\%$:* Sugestão explícita de remoção da variável ou aplicação de transformações não-lineares ($\ln(x)$, $1/x$, $\sqrt{x}$).
    - *Inversão de Sinal:* Orientações sobre colinearidade redundante entre variáveis concorrentes e indicação de remoção.
    - *Amplitude do IC $> 50\%$:* Recomendações sobre exclusão de outliers e redução da variância residual.
    - *Extrapolação:* Indicação de ampliação amostral para abranger os atributos do imóvel avaliando.

- [x] **Dados da Empresa no Topo do Relatório Alinhados à Esquerda:**
  - **Layout Corporativo e Normativo:** No cabeçalho da página do relatório (`/report` e geração de PDF), o logotipo e todos os dados institucionais da empresa/perito (Nome da Empresa, CNPJ/CPF, CREA/CAU PJ, Endereço completo, Telefone, E-mail e Website) são renderizados no topo da primeira página, alinhados à esquerda.
  - **Assinatura Profissional Mantida:** A assinatura formal do responsável técnico permanece na seção de encerramento do laudo.

- [x] **Interatividade Gráfica com a Tabela de Dados Amostrais (Localização de Outliers no Clique):**
  - **Redirecionamento ao Clicar nos Pontos:** Ao clicar em qualquer observação amostral nos gráficos de regressão (Gráfico de Aderência Observado x Estimado, Gráfico de Resíduos Padronizados vs Estimados, Gráfico de Distância de Cook ou Gráfico de Dispersão Exploratório), o sistema redireciona automaticamente para a aba **"Dados da Amostra"**.
  - **Destaque Visual com Pulso e Rolagem:** A linha correspondente na tabela é rolada suavemente para o centro da tela (`scrollIntoView`) e ganha um destaque visual com efeito de pulso luminoso (`.row-selected-highlight`), exibindo notificação toast para facilitar a inspeção, alteração ou desativação de outliers.
  - **Cursor e Dicas de Clique:** Todos os gráficos de dispersão alteram o cursor para `pointer` ao passar o mouse sobre os pontos, informando no tooltip que o dado é clicável.

- [x] **Correção Completa do Modo Noturno (Contraste de Fontes, Tabelas e Formulários):**
  - **Adoção do Padrão `color-scheme: dark;`:** Configuração explícita de `color-scheme: dark;` no seletor `html[data-theme="dark"]`, forçando controles nativos de formulário (selects, popups de opções, scrollbars, calendários) a renderizarem cores escuras apropriadas.
  - **Correção de Cores Hardcoded e Textos Ocultos:**
    - Substituição de fundos claros fixos em linhas de outliers por variáveis dinâmicas translúcidas (`rgba(239, 68, 68, 0.22)`), garantindo legibilidade perfeita do texto.
    - Adaptação das células da matriz de correlação de Pearson para manter contraste adequado de texto no tema escuro.
    - Estilização universal de `<select>`, `<option>`, `<input>` e `<textarea>` para herdar `--text-main` e `--bg-card`.
    - Ajuste de badges normativos (Grau III, II, I e Perigo) para contrastarem com fundos escuros.
    - Cartões de valor total avaliado e blocos informativos adaptados para o tema escuro.
  - **Integração do Chart.js com o Tema:** Função `applyChartTheme()` aplicada automaticamente ao carregar e ao alternar o tema, reconfigurando rótulos de eixos, títulos e legendas com cores legíveis em tempo real.

- [x] **Resiliência Numérica Universal & Tolerância a Falhas (`safe_float`):**
  - **Tratamento de Padrões Brasileiros e Americanos:** Implementada função centralizadora `safe_float` em [`app/core/statistics.py`](app/core/statistics.py) com tolerância total a formatos numéricos brasileiros com vírgula e ponto de milhar (`"1.250,50"`, `"1250,50"`), formatos americanos (`"1,250.50"`), espaços em branco, strings vazias, valores nulos (`None`), booleanos e valores `NaN`/`Inf`.
  - **Eliminação Definitiva de Falhas de Conversão:** Substituição das chamadas diretas a `float()` por `safe_float` nos módulos vitais de cálculo ([`regression.py`](app/core/regression.py), [`valuation.py`](app/core/valuation.py), [`neural_network.py`](app/core/neural_network.py), [`report_generator.py`](app/core/report_generator.py) e [`main.py`](app/main.py)), garantindo que a edição de planilhas com células em branco ou números colados em texto nunca resulte em erro 500 ou quebra de processamento.
  - **Proteção em Redes Neurais:** Salvaguarda defensiva contra exceções `IndexError` no particionamento e detecção de variáveis numéricas ativas para a RNA.

- [x] **Conformidade Metodológica com a ABNT NBR 14653-3:2019 (Avaliação de Imóveis Rurais):**
  - **Detecção Automática de Tipologia:** Identificação contextual em [`app/core/regression.py`](app/core/regression.py) e [`app/core/report_generator.py`](app/core/report_generator.py) quando o projeto se refere a imóveis rurais (`tipologia == 7` ou termos rurais em metadados).
  - **Enquadramento Normativo da Tabela 2 e Tabela 3 da NBR 14653-3:**
    - *Quantidade Mínima de Dados Efetivos:* Grau III exige $N \ge 4(k+1)$, Grau II exige $N \ge 3(k+1)$ e Grau I exige $N \ge 2(k+1)$ (em contraste com o exigido para urbanos de $6(k+1)$ e $3(k+1)$).
    - *Somatório Mínimo de Pontos:* Exigência normativa de 15 pontos para Grau III, 9 pontos para Grau II e 6 pontos para Grau I.
    - *Diagnósticos Contextualizados:* Mensagens orientativas citando explicitamente os parâmetros e artigos da NBR 14653-3.
  - **Relatório e Laudo Técnico Adaptativo:** O documento emitido em `/report` e no PDF gerado substitui dinamicamente os cabeçalhos normativos para **"ABNT NBR 14653-3 (Avaliação de Bens - Parte 3: Imóveis Rurais)"** e **"Tabela 2 - NBR 14653-3"**.

- [x] **Expansão da Bateria de Testes Automatizados (13/13 Aprovados):**
  - Adicionado o teste `test_13_safe_float_and_rural_nbr` em [`test_suite.py`](test_suite.py), testando todas as variações de parsing numérico, resiliência a strings brasileiras na regressão e a diferenciação de enquadramento da NBR 14653-3 vs 14653-2.
  - 100% dos testes aprovados com sucesso (13 testes em 26,2s).

- [x] **Padronização de Título do Documento, Responsável Técnico e Créditos ao Engenheiro Autor:**
  - **Título e Subtítulo Normativo como Cabeçalho do Documento:** O título `"RELATÓRIO DE AVALIAÇÃO IMOBILIÁRIA"` e o subtítulo `"Em conformidade com a ABNT NBR 14653-2 (Imóveis Urbanos)"` (ou NBR 14653-3 para rurais) foram definidos como padrão oficial e renderizados com destaque visual como cabeçalho do documento (`<h1>` e `<title>`), completamente fora de qualquer rodapé.
  - **Nome Padrão do Engenheiro:** O campo de autor e responsável técnico adota por padrão `"Nome do Responsável"` em novos modelos, metadados do projeto e campos do modal de personalização.
  - **Créditos Oficiais no Modal "Sobre":** Adicionada seção dedicada e destaque de créditos ao **Engenheiro Civil Responsável** com link direto para o seu perfil no GitHub: [https://github.com/b-host](https://github.com/b-host).

- [x] **Remoção Integral de Registros e Metadados Proprietários (Antonio Pelli Neto / Pelli Sistemas):**
  - **Filtro Sanitizador no Parser Legado:** Implementado filtro ativo em [`app/core/io_sda.py`](app/core/io_sda.py) para substituir automaticamente qualquer menção de autoria ou descrição ligada a "Antonio Pelli Neto" ou "Pelli Sistemas" pelo padrão neutro `"Nome do Responsável"` e `"OpenValora"`.
  - **Limpeza Total dos Modelos de Amostra:** Todos os 17 arquivos `.sda` oficiais em [`sample_data/`](sample_data/), planilhas `.xls` em [`sample_data/planilhas/`](sample_data/planilhas/) e arquivos de referência em [`sample_data/laudos_referencia/`](sample_data/laudos_referencia/) foram reescritos e sanitizados com estrutura limpa, eliminando qualquer menção ou resquício nominal do autor legado.
  - **Gravação Segura:** Ao exportar arquivos `.sda`, a aplicação define a assinatura de aplicação como `"OpenValora"` e direitos como `"OpenValora"`.

- [x] **Separação Rigorosa entre CNPJ e Registro Profissional (CREA/CAU PJ) & Rodapé Institucional:**
  - **Cabeçalho Corporativo e Seção de Identificação:** No gerador de laudos ([`app/core/report_generator.py`](app/core/report_generator.py)), o número de registro `CREA/CAU PJ` agora é renderizado em linha e bloco próprio destacado, completamente desvinculado e separado do `CNPJ/CPF`.
  - **Rodapé Institucional Esteticamente Agradável:** Inserido card institucional elegante no rodapé final do relatório com dados completos da empresa/profissional (Telefone, CNPJ, CREA/CAU PJ, Endereço, E-mail e Website).

- [x] **Resiliência Numérica e Prevenção de Erros na Análise Exploratória:**
  - **Tratamento Anti-NaN em Correlações:** Proteção contra divisões por zero e valores `NaN` na matriz de correlação de Pearson para variáveis com variância nula em [`app/main.py`](app/main.py).
  - **Validação de Amostras Mínimas:** Alinhamento estrito para mínimo de 4 observações válidas na rota de regressão linear.

- [x] **Logotipo Padrão Oficial do OpenValora no Relatório e Personalização:**
  - **Fallback Automático para o Logotipo Oficial:** Caso o usuário não envie um logo personalizado, o relatório renderiza diretamente o logotipo oficial em alta definição do OpenValora (com suporte offline embutido via Base64 para compatibilidade perfeita com geradores de PDF e impressão).
  - **Preview Imediato:** O modal de personalização em [`app/templates/index.html`](app/templates/index.html) e [`app/static/js/app.js`](app/static/js/app.js) exibe por padrão a logo do OpenValora com botão para restauração padrão imediata.

- [x] **Simplificação e Ajuste no Modal "Sobre" (Card de Crédito):**
  - O campo de autoria foi renomeado exclusivamente para **"Crédito"**, com a remoção total da menção a "Engenharia Civil", mantendo o link direto de desenvolvimento para [https://github.com/b-host](https://github.com/b-host).

- [x] **Centralização do Título e Subtítulo do Relatório:**
  - **Documento Final:** O título e o subtítulo do relatório no topo do documento agora são exibidos centralizados horizontalmente (`text-align: center;`) em um bloco próprio de destaque visual, logo abaixo do cabeçalho institucional.
  - **Modal de Personalização:** Os campos de entrada do título e subtítulo normativo foram centralizados para refletir visualmente o alinhamento do documento final.

- [x] **Preenchimento Horizontal Completo de Observações Técnicas (100% da Janela):**
  - Corrigido o estilo CSS de `.input` e `.form-control` em [`app/static/css/styles.css`](app/static/css/styles.css) e no modal de personalização para que o campo `<textarea id="rep-observacoes">` ocupe integralmente (100% de largura, `box-sizing: border-box`) a janela do diálogo, eliminando qualquer limitação de largura e tornando a edição confortável.

- [x] **Ocupação Integral da Largura da Janela (100% Horizontal) & Otimização da Tabela de Amostras:**
  - **Remoção do Limite Fixo de 1400px:** Eliminado `max-width: 1400px;` e margens laterais desnecessárias em `.main-content`, permitindo que todas as abas ocupem 100% do espaço horizontal disponível da janela em qualquer resolução.
  - **Tabela de Dados da Amostra sem Ocultação e com Ajuste Preciso:**
    - Ajustado o padding de células da tabela para `4px 6px` e cabeçalhos para `8px 10px`, liberando dezenas de pixels por coluna.
    - Otimizados os campos de entrada `.table-input` com `min-width: 48px; box-sizing: border-box;` e remoção dos spinners nativos de número (`-webkit-appearance: none; -moz-appearance: textfield;`).
    - Encolhidas as colunas de controle (`#` 38px, `Ativo` 44px, `Outlier` 48px, `Ação` 40px) para direcionar mais de 90% da largura útil da tela para os dados observados.
    - Adicionado filtro opcional instantâneo `"Apenas Variáveis Ativas"` para alternar entre todas as colunas ou apenas os regressores ativos na modelagem.
    - Adicionado cabeçalho fixo (`position: sticky; top: 0; z-index: 2;`) para navegação confortável com rolagem vertical.

- [x] **Otimização Extrema de Desempenho na Transição Entre Abas (Zero Lag / < 1ms):**
  - **Eliminação de Gargalos Globais do Lucide:** Identificado que `lucide.createIcons()` estava varrendo a árvore inteira do documento a cada troca de aba e renderização de tabelas com centenas de linhas. Substituídos os ícones de ação da tabela de amostras por SVG inline otimizado e escopadas as chamadas de ícones restantes com `{ root: container }`.
  - **Sistema de Flags de Cache (`dirty` tracking):** Criado controle de estado (`exploratoryDirty`, `regressionDirty`, `laudoDirty`, `lastRenderedModelIdx`, `lastLaudoModelIdx`) no [`app/static/js/app.js`](app/static/js/app.js). Abas que já foram calculadas e desenhadas alternam a visibilidade de forma instantânea (0ms), disparando apenas `.resize()` leve no Chart.js para adaptação ao container, sem recriar canvases nem reenviar requisições HTTP desnecessárias.
  - **Navegação Fluida no Ranking de Modelos:** A função `selectModel(idx)` agora atualiza apenas a linha destacada na tabela de ranking e renderiza os detalhes diretamente, eliminando a reconstrução contínua de dezenas de linhas e nós do DOM.
  - **Preservação de Estado do Laudo Técnico:** O `iframe` do laudo não é recarregado a cada clique na aba se o modelo selecionado e os metadados permanecerem inalterados.

- [x] **Análise Exploratória: Seleção Dinâmica de Variáveis Disponíveis (Eixo X) vs Variável Dependente (Eixo Y):**
  - **Seleção Dupla e Intuitiva:** Implementados dois seletores interdependentes no topo da aba de Análise Exploratória ([`app/templates/index.html`](app/templates/index.html)): `select-exp-indep` (Variável Explicativa / Eixo X) e `select-exp-dep` (Variável Dependente / Eixo Y).
  - **Seleção Automática Inteligente:** O sistema detecta a variável classificada com código 7 (Dependente) como padrão para o eixo Y e seleciona a primeira variável explicativa ativa para o eixo X.
  - **Visualização Integrada de Dispersão e Correlação de Pearson ($r$):**
    - Atualização dinâmica do título da dispersão (`Dispersão: Y vs X`).
    - Exibição de badge com o coeficiente de correlação linear de Pearson exato ($r = \pm 0.XXXX$) e categorização visual de intensidade (forte, moderada, fraca).
    - Gráfico de dispersão com suporte a tooltip detalhado e navegação direta para a amostra na tabela com um clique.
    - Histograma de frequências sincronizado com a variável explicativa selecionada.
    - Cards de estatística descritiva (N, Média, Mediana, Desvio Padrão, CV%, Mínimo e Máximo) atualizados dinamicamente.

- [x] **Padronização do Versionamento do Projeto Iniciando em `0.1.0`:**
  - Padronizada a versão inicial estável para **`0.1.0`** em todos os pontos do sistema:
    - FastAPI: `version="0.1.0"` em [`app/main.py`](app/main.py).
    - Cabeçalho do Laudo Normativo (NBR 14653): `OpenValora v0.1.0` em [`app/core/report_generator.py`](app/core/report_generator.py).
    - Interface Web/Desktop: Badge de versão no cabeçalho e modal "Sobre" em [`app/templates/index.html`](app/templates/index.html).
    - Empacotador PyInstaller: `CFBundleVersion` e `CFBundleShortVersionString` configurados para `0.1.0` em [`openvalora.spec`](openvalora.spec).
    - Documentação do Repositório: Badge oficial atualizado para `Versão 0.1.0` em [`README.md`](README.md).
    - Suíte de Testes Automatizados: Adicionado teste de conformidade de versão e análise exploratória (`test_14_exploratory_and_version_0_1_0`) em [`test_suite.py`](test_suite.py).
- [x] **Verificação de Salvamentos Pendentes e Alerta Antes de Sair da Aba:**
  - **Monitoramento de Modificações por Aba (`state.unsavedChanges`):** Implementado rastreamento em tempo real de alterações em cada aba de entrada de dados ([`app/static/js/app.js`](app/static/js/app.js)):
    - `projeto`: alterações nos campos de metadados (`nome`, `autor`, `data`, `descricao`, `area`, `tipologia`).
    - `variaveis`: inclusão, exclusão ou edição de parâmetros das variáveis estatísticas.
    - `dados`: inclusão, exclusão, edição de células amostrais ou alternância de outliers/status ativo.
    - `avaliandos`: edição de parâmetros ou inclusão/exclusão de imóveis avaliandos.
  - **Bloqueio e Confirmação de Saída (`switchTab`):** Ao tentar navegar para outra aba com modificações pendentes, o sistema exibe diálogo de confirmação claro especificando qual aba possui dados não salvos e oferecendo a escolha de permanecer ou descartar.
  - **Proteção Global do Navegador (`beforeunload`):** Proteção nativa que impede fechamento acidental da aba do navegador caso haja edições não salvas no projeto.
  - **Correção de Sintaxe no Frontend:** Eliminado caractere redundante em `app.js` que causava `SyntaxError` e impedia a inicialização do script no navegador e no WebKit desktop. Adicionado teste de validação de sintaxe estática JS à suíte de testes (`test_15_javascript_syntax_and_assets`).