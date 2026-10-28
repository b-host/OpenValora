/**
 * OpenValora - Frontend Application Controller
 * Gerencia o estado reativo da aplicação, tabelas de dados, chamadas de API e abas.
 */

const state = {
    project: null,
    activeTab: 'regressao',
    selectedModelIdx: 0,
    exploratoryData: null,
    selectedExpX: null,
    selectedExpY: null,
    catalogQuery: '',
    catalogResults: [],
    // Flags de cache e controle de desempenho para alternância instantânea de abas
    exploratoryDirty: true,
    regressionDirty: true,
    laudoDirty: true,
    lastRenderedModelIdx: -1,
    lastLaudoModelIdx: -1,
    // Monitoramento de alterações pendentes de salvamento por aba
    unsavedChanges: {
        projeto: false,
        variaveis: false,
        dados: false,
        avaliandos: false
    }
};

// ==================== ARMAZENAMENTO SEGURO ====================
// Tolerante a sandboxes de desktop (ex.: WebKitGTK / WebView2 com restrições de storage)
const safeStorage = {
    _mem: {},
    getItem(key) {
        try {
            if (typeof window !== 'undefined' && 'localStorage' in window && window.localStorage) {
                return window.localStorage.getItem(key);
            }
        } catch (e) {
            console.warn('[OpenValora] safeStorage.getItem:', e);
        }
        return this._mem[key] || null;
    },
    setItem(key, value) {
        try {
            if (typeof window !== 'undefined' && 'localStorage' in window && window.localStorage) {
                window.localStorage.setItem(key, String(value));
                return;
            }
        } catch (e) {
            console.warn('[OpenValora] safeStorage.setItem:', e);
        }
        this._mem[key] = String(value);
    }
};

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', async () => {
    try {
        initTheme();
    } catch (e) {
        console.error('Erro ao inicializar tema:', e);
    }

    try {
        setupEventListeners();
    } catch (e) {
        console.error('Erro ao registrar listeners de eventos:', e);
    }

    try {
        await loadProject();
    } catch (e) {
        console.error('Erro ao carregar projeto:', e);
    }

    try {
        if (window.lucide) {
            lucide.createIcons();
        }
    } catch (e) {
        console.error('Erro ao criar ícones lucide:', e);
    }
});

function initTheme() {
    const saved = safeStorage.getItem('openvalora_theme') || safeStorage.getItem('valoraopen_theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    if (typeof window.applyChartTheme === 'function') {
        window.applyChartTheme();
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    safeStorage.setItem('openvalora_theme', next);

    if (typeof window.applyChartTheme === 'function') {
        window.applyChartTheme();
    }

    // Re-renderiza gráficos e matriz de correlação para atualizar cores dos eixos
    if (state.project && state.project.modelos_calculados && state.project.modelos_calculados[state.selectedModelIdx]) {
        const m = state.project.modelos_calculados[state.selectedModelIdx];
        if (typeof window.renderAderenciaChart === 'function') renderAderenciaChart('chart-aderencia', m.residuos);
        if (typeof window.renderResiduosChart === 'function') renderResiduosChart('chart-residuos', m.residuos, m.erro_padrao);
        if (typeof window.renderCookChart === 'function') renderCookChart('chart-cook', m.residuos);
        if (typeof window.renderNormalidadeChart === 'function') renderNormalidadeChart('chart-normalidade', m.residuos);
    }
    if (state.exploratoryData) {
        renderCorrelationMatrix();
    }
}

/**
 * Redirecionamento e Destaque Interativo: ao clicar em um ponto no gráfico,
 * navega para a aba de dados e destaca a linha correspondente para fácil inspeção ou exclusão.
 */
function navigateToDataRow(rowId) {
    if (!rowId) return;

    // 1. Alterna visualmente para a aba de Dados Amostrais
    switchTab('dados');

    // 2. Aguarda a montagem do DOM e localiza a linha
    setTimeout(() => {
        const tbody = document.getElementById('tbody-dados');
        if (!tbody) return;

        // Limpa destaques anteriores
        tbody.querySelectorAll('.row-selected-highlight').forEach(el => el.classList.remove('row-selected-highlight'));

        let targetRow = tbody.querySelector(`tr[data-id="${rowId}"]`);
        if (!targetRow) {
            const rows = tbody.querySelectorAll('tr');
            if (rows[rowId - 1]) targetRow = rows[rowId - 1];
        }

        if (targetRow) {
            targetRow.classList.add('row-selected-highlight');
            targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
            showToast(`Amostra #${rowId} selecionada a partir do gráfico. Você pode alternar seu status, marcá-la como outlier ou editar seus valores.`, 4000);
        }
    }, 150);
}
window.navigateToDataRow = navigateToDataRow;

function setupEventListeners() {
    // Abas de navegação
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            switchTab(tabName);
        });
    });

    // Tema
    const themeBtn = document.getElementById('btn-toggle-theme');
    if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

    // Botões de ação globais
    document.getElementById('btn-novo-modelo')?.addEventListener('click', openNewModelModal);
    document.getElementById('btn-abrir-amostras')?.addEventListener('click', openSamplesModal);
    document.getElementById('btn-upload-file')?.addEventListener('click', () => document.getElementById('input-file-upload').click());
    document.getElementById('input-file-upload')?.addEventListener('change', handleFileUpload);
    
    // Exportações (Padrão Aberto .valora e Legados)
    document.getElementById('btn-export-valora')?.addEventListener('click', () => {
        const raw = state.project?.metadata?.nome || 'modelo_openvalora';
        const safe = raw.replace(/\s+/g, '_') + '.valora';
        downloadFile('/api/export/valora', safe);
    });
    document.getElementById('btn-export-sda')?.addEventListener('click', () => {
        const raw = state.project?.metadata?.nome || 'modelo_openvalora';
        const safe = raw.replace(/\s+/g, '_') + '.sda';
        downloadFile('/api/export/sda', safe);
    });
    document.getElementById('btn-export-xlsx')?.addEventListener('click', () => {
        const raw = state.project?.metadata?.nome || 'dados_openvalora';
        const safe = raw.replace(/\s+/g, '_') + '.xlsx';
        downloadFile('/api/export/xlsx', safe);
    });

    document.getElementById('btn-calcular-reg')?.addEventListener('click', calculateRegression);
    document.getElementById('btn-treinar-rna')?.addEventListener('click', trainRNA);
    document.getElementById('btn-laudo-externo')?.addEventListener('click', () => window.open(`/report?model_idx=${state.selectedModelIdx}`, '_blank'));
    document.getElementById('btn-info-projeto')?.addEventListener('click', openAboutModal);

    // Controles do Relatório (Personalização, Impressão e PDF)
    document.getElementById('btn-personalizar-relatorio')?.addEventListener('click', openReportCustomizer);
    document.getElementById('btn-baixar-pdf')?.addEventListener('click', downloadReportPDF);
    document.getElementById('btn-imprimir-relatorio')?.addEventListener('click', printReport);
    document.getElementById('select-relatorio-modelo')?.addEventListener('change', (e) => {
        state.selectedModelIdx = parseInt(e.target.value) || 0;
        renderLaudoPreview();
    });
    document.getElementById('input-report-logo')?.addEventListener('change', handleReportLogoSelect);

    // Monitoramento de alterações em campos de projeto / metadados
    ['meta-nome', 'meta-autor', 'meta-data', 'meta-descricao', 'meta-area', 'meta-tipologia'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', () => { if (state.unsavedChanges) state.unsavedChanges.projeto = true; });
            el.addEventListener('change', () => { if (state.unsavedChanges) state.unsavedChanges.projeto = true; });
        }
    });

    window.addEventListener('beforeunload', (e) => {
        if (state.unsavedChanges && Object.values(state.unsavedChanges).some(Boolean)) {
            e.preventDefault();
            e.returnValue = 'Existem alterações não salvas no projeto. Deseja realmente sair?';
            return e.returnValue;
        }
    });

    window.addEventListener('message', (e) => {
        if (e.data && e.data.type === 'OPEN_REPORT_CUSTOMIZER') {
            openReportCustomizer();
        }
    });
}

async function downloadFile(url, defaultFilename) {
    showToast('Preparando download do arquivo...');
    try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const blob = await resp.blob();
        let filename = defaultFilename;
        const disp = resp.headers.get('Content-Disposition');
        if (disp && disp.includes('filename=')) {
            const match = disp.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (match && match[1]) {
                filename = match[1].replace(/['"]/g, '');
            }
        }
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            window.URL.revokeObjectURL(blobUrl);
            a.remove();
        }, 1500);
        showToast(`Arquivo "${filename}" baixado com sucesso!`);
    } catch (err) {
        console.warn('Download via Blob falhou, navegando para URL:', err);
        window.location.href = url;
    }
}

// ==================== CONTROLE DE ABAS ====================
function switchTab(tabName) {
    if (state.activeTab === tabName && document.getElementById(`tab-${tabName}`)?.style.display === 'block') {
        return;
    }

    // Valida se a aba atual possui alterações não salvas antes de permitir a troca
    const prevTab = state.activeTab;
    if (state.unsavedChanges && state.unsavedChanges[prevTab]) {
        const tabLabels = {
            projeto: 'Projeto & Metadados',
            variaveis: 'Variáveis',
            dados: 'Dados da Amostra',
            avaliandos: 'Imóveis Avaliandos'
        };
        const nomeAba = tabLabels[prevTab] || prevTab;
        const confirmMsg = `Atenção: Você possui alterações não salvas na aba "${nomeAba}".\n\nDeseja realmente sair sem salvar?`;
        if (!confirm(confirmMsg)) {
            return;
        }
        // Se o usuário confirmou que deseja sair, limpa a flag daquela aba
        state.unsavedChanges[prevTab] = false;
    }

    state.activeTab = tabName;

    // Alternância rápida de botões ativos
    document.querySelectorAll('.nav-tab-btn').forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-tab') === tabName);
    });

    // Alternância imediata da visibilidade dos painéis (0ms)
    document.querySelectorAll('.tab-panel').forEach(p => {
        p.style.display = p.id === `tab-${tabName}` ? 'block' : 'none';
    });

    // Caching e renderização sob demanda: renderiza apenas se houver alterações pendentes
    if (tabName === 'exploratoria') {
        if (!state.exploratoryData || state.exploratoryDirty) {
            loadExploratoryData();
        } else if (window.chartInstances) {
            if (window.chartInstances['chart-exp-hist']) window.chartInstances['chart-exp-hist'].resize();
            if (window.chartInstances['chart-exp-scatter']) window.chartInstances['chart-exp-scatter'].resize();
        }
    } else if (tabName === 'regressao') {
        if (state.regressionDirty || state.lastRenderedModelIdx !== state.selectedModelIdx) {
            renderRegressionView();
        } else if (window.chartInstances) {
            ['chart-aderencia', 'chart-residuos', 'chart-cook', 'chart-normalidade'].forEach(id => {
                if (window.chartInstances[id]) window.chartInstances[id].resize();
            });
        }
    } else if (tabName === 'laudo') {
        if (state.laudoDirty || state.lastLaudoModelIdx !== state.selectedModelIdx) {
            renderLaudoPreview();
        }
    } else if (tabName === 'rna') {
        if (window.chartInstances && window.chartInstances['chart-rna-loss']) {
            window.chartInstances['chart-rna-loss'].resize();
        }
    }
}

// ==================== CARREGAMENTO DE DADOS ====================
async function loadProject() {
    try {
        const resp = await fetch('/api/project');
        state.project = await resp.json();
        state.exploratoryDirty = true;
        state.regressionDirty = true;
        state.laudoDirty = true;
        state.lastRenderedModelIdx = -1;
        state.lastLaudoModelIdx = -1;
        state.unsavedChanges = { projeto: false, variaveis: false, dados: false, avaliandos: false };
        renderAll();
        // Se houver modelos calculados, abre na aba de regressão; caso seja um novo modelo ou sem cálculos, abre em dados
        if (state.project && state.project.modelos_calculados && state.project.modelos_calculados.length > 0) {
            switchTab('regressao');
        } else {
            switchTab('dados');
        }
    } catch (err) {
        console.error('Erro ao carregar projeto:', err);
    }
}

function renderAll() {
    renderProjectMetadata();
    renderVariablesTable();
    renderDataTable();
    renderSubjectTable();
    renderRegressionView();
    if (window.lucide) lucide.createIcons();
}

// ==================== ABA 1: PROJETO / PROPRIEDADES ====================
function renderProjectMetadata() {
    if (!state.project) return;
    const m = state.project.metadata;
    document.getElementById('meta-nome').value = m.nome || '';
    document.getElementById('meta-autor').value = m.autor || 'Nome do Responsável';
    document.getElementById('meta-data').value = m.data_criacao || '';
    document.getElementById('meta-descricao').value = m.descricao || '';
    document.getElementById('meta-area').value = m.area_conhecimento || 1;
    document.getElementById('meta-tipologia').value = m.tipologia || 1;
    document.getElementById('header-project-name').innerText = m.nome || 'Projeto OpenValora';
}

async function saveMetadata() {
    const payload = {
        ...(state.project?.metadata || {}),
        nome: document.getElementById('meta-nome').value,
        autor: document.getElementById('meta-autor').value,
        data_criacao: document.getElementById('meta-data').value,
        descricao: document.getElementById('meta-descricao').value,
        area_conhecimento: parseInt(document.getElementById('meta-area').value),
        tipologia: parseInt(document.getElementById('meta-tipologia').value)
    };
    await fetch('/api/project/metadata', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    state.project.metadata = payload;
    if (state.unsavedChanges) state.unsavedChanges.projeto = false;
    document.getElementById('header-project-name').innerText = payload.nome;
    showToast('Propriedades salvas com sucesso!');
}

// ==================== ABA 2: VARIÁVEIS ====================
function renderVariablesTable() {
    const tbody = document.getElementById('tbody-variaveis');
    if (!tbody || !state.project) return;
    tbody.innerHTML = '';

    const vars = state.project.variaveis || [];
    vars.forEach((v, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="text-align: center; font-weight: bold; width: 40px;">${idx + 1}</td>
            <td><input type="text" class="table-input" value="${v.nome}" onchange="updateVarField(${idx}, 'nome', this.value)"></td>
            <td>
                <select class="table-input" onchange="updateVarField(${idx}, 'tipo', parseInt(this.value))">
                    <option value="1" ${v.tipo === 1 ? 'selected' : ''}>Numérica</option>
                    <option value="2" ${v.tipo === 2 ? 'selected' : ''}>Texto</option>
                </select>
            </td>
            <td>
                <select class="table-input" onchange="updateVarField(${idx}, 'classificacao', parseInt(this.value))">
                    <option value="1" ${v.classificacao === 1 ? 'selected' : ''}>1 - Quantitativa</option>
                    <option value="2" ${v.classificacao === 2 ? 'selected' : ''}>2 - Códigos Alocados</option>
                    <option value="3" ${v.classificacao === 3 ? 'selected' : ''}>3 - Proxy</option>
                    <option value="4" ${v.classificacao === 4 ? 'selected' : ''}>4 - Dicotômica</option>
                    <option value="7" ${v.classificacao === 7 ? 'selected' : ''} style="font-weight: bold; color: #0284c7;">7 - Variável Dependente</option>
                    <option value="8" ${v.classificacao === 8 ? 'selected' : ''}>8 - Texto geral</option>
                </select>
            </td>
            <td>
                <select class="table-input" onchange="updateVarField(${idx}, 'crescimento', parseInt(this.value))">
                    <option value="0" ${v.crescimento === 0 ? 'selected' : ''}>Crescente (Direta)</option>
                    <option value="1" ${v.crescimento === 1 ? 'selected' : ''}>Decrescente (Inversa)</option>
                    <option value="-1" ${v.crescimento === -1 ? 'selected' : ''}>Livre</option>
                </select>
            </td>
            <td style="text-align: center;">
                <input type="checkbox" ${v.unitario ? 'checked' : ''} onchange="updateVarField(${idx}, 'unitario', this.checked)">
            </td>
            <td style="text-align: center;">
                <input type="checkbox" ${v.habilitada ? 'checked' : ''} onchange="updateVarField(${idx}, 'habilitada', this.checked)">
            </td>
            <td style="text-align: center;">
                <button class="btn btn-danger btn-sm" onclick="deleteVariable(${idx})"><i data-lucide="trash-2" style="width:14px;height:14px;"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    if (window.lucide) lucide.createIcons();
}

function updateVarField(idx, field, val) {
    if (state.unsavedChanges) state.unsavedChanges.variaveis = true;
    if (field === 'nome') {
        const oldName = state.project.variaveis[idx].nome;
        const newName = String(val).trim();
        if (oldName !== newName && newName !== '') {
            // Migra as chaves correspondentes nos dados da amostra
            (state.project.dados || []).forEach(item => {
                if (item.valores && item.valores[oldName] !== undefined) {
                    item.valores[newName] = item.valores[oldName];
                    delete item.valores[oldName];
                }
            });
            // Migra as chaves nos imóveis avaliandos
            (state.project.projecoes || []).forEach(p => {
                if (p.valores && p.valores[oldName] !== undefined) {
                    p.valores[newName] = p.valores[oldName];
                    delete p.valores[oldName];
                }
            });
        }
    }
    state.project.variaveis[idx][field] = val;
    // Se marcou como dependente, desmarca outras
    if (field === 'classificacao' && val === 7) {
        state.project.variaveis.forEach((v, i) => {
            if (i !== idx && v.classificacao === 7) v.classificacao = 1;
        });
        renderVariablesTable();
    }
}

async function saveVariables() {
    state.exploratoryDirty = true;
    state.regressionDirty = true;
    state.laudoDirty = true;
    await fetch('/api/variables', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state.project.variaveis)
    });
    // Sincroniza dados e sujeitos caso chaves tenham mudado
    await fetch('/api/data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state.project.dados || [])
    });
    await fetch('/api/subjects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state.project.projecoes || [])
    });
    if (state.unsavedChanges) state.unsavedChanges.variaveis = false;
    showToast('Variáveis e mapeamento de dados salvos!');
    renderDataTable();
    renderSubjectTable();
}

function addCustomVariable() {
    state.exploratoryDirty = true;
    state.regressionDirty = true;
    state.laudoDirty = true;
    if (state.unsavedChanges) state.unsavedChanges.variaveis = true;
    const newVar = {
        id: Math.random().toString(36).substring(2, 10),
        nome: `Nova_Var_${state.project.variaveis.length + 1}`,
        descricao: '',
        tipo: 1,
        classificacao: 1,
        continua: 1,
        decimais: 2,
        habilitada: true,
        crescimento: 0,
        unitario: false,
        var_vinculada: -1
    };
    state.project.variaveis.push(newVar);
    renderVariablesTable();
    renderDataTable();
    renderSubjectTable();
}

function deleteVariable(idx) {
    const varName = state.project.variaveis[idx].nome;
    if (confirm(`Excluir a variável "${varName}"?`)) {
        state.exploratoryDirty = true;
        state.regressionDirty = true;
        state.laudoDirty = true;
        if (state.unsavedChanges) state.unsavedChanges.variaveis = true;
        state.project.variaveis.splice(idx, 1);
        (state.project.dados || []).forEach(item => {
            if (item.valores && item.valores[varName] !== undefined) {
                delete item.valores[varName];
            }
        });
        (state.project.projecoes || []).forEach(p => {
            if (p.valores && p.valores[varName] !== undefined) {
                delete p.valores[varName];
            }
        });
        renderVariablesTable();
        renderDataTable();
        renderSubjectTable();
    }
}

// ==================== ABA 3: DADOS DA AMOSTRA ====================
let filterOnlyActiveVars = false;

function toggleFilterActiveVars(checked) {
    filterOnlyActiveVars = checked;
    renderDataTable();
}

function renderDataTable() {
    const thead = document.getElementById('thead-dados');
    const tbody = document.getElementById('tbody-dados');
    if (!thead || !tbody || !state.project) return;

    let vars = state.project.variaveis || [];
    if (filterOnlyActiveVars) {
        vars = vars.filter(v => v.habilitada);
    }

    // Header
    thead.innerHTML = `
        <tr>
            <th style="width: 38px; text-align: center;" title="Número identificador da amostra">#</th>
            <th style="width: 44px; text-align: center;" title="Habilitar ou desabilitar esta linha do cálculo">Ativo</th>
            <th style="width: 48px; text-align: center;" title="Marcar como dado atípico (outlier)">Outlier</th>
            ${vars.map(v => `<th style="${v.classificacao === 7 ? 'color: #0284c7; font-weight: bold;' : ''}" title="Variável ${v.nome}: ${v.descricao || (v.classificacao === 7 ? 'Variável Dependente (Preço)' : 'Regressor Independente')}">${v.nome}</th>`).join('')}
            <th style="width: 40px; text-align: center;" title="Excluir dado amostral">Ação</th>
        </tr>
    `;

    // Body
    tbody.innerHTML = '';
    const dados = state.project.dados || [];

    dados.forEach((row, rIdx) => {
        const tr = document.createElement('tr');
        const rowIdVal = row.id || (rIdx + 1);
        tr.id = `dados-row-${rowIdVal}`;
        tr.dataset.id = String(rowIdVal);

        if (!row.habilitado) tr.classList.add('row-disabled');
        if (row.outlier) tr.classList.add('row-outlier');

        let colsHtml = `
            <td style="text-align: center; font-weight: 600; width: 38px;" title="Amostra #${rowIdVal}">${rowIdVal}</td>
            <td style="text-align: center; width: 44px;">
                <input type="checkbox" ${row.habilitado ? 'checked' : ''} onchange="toggleRowEnabled(${rIdx}, this.checked)" title="Habilitar ou desabilitar esta observação no cálculo da regressão">
            </td>
            <td style="text-align: center; width: 48px;">
                <input type="checkbox" ${row.outlier ? 'checked' : ''} onchange="toggleRowOutlier(${rIdx}, this.checked)" title="Sinalizar dado como outlier">
            </td>
        `;

        vars.forEach(v => {
            const val = row.valores[v.nome] !== undefined ? row.valores[v.nome] : '';
            colsHtml += `
                <td>
                    <input type="${v.tipo === 1 ? 'number' : 'text'}" step="any" class="table-input" value="${val}"
                           title="Valor de ${v.nome} na amostra #${rowIdVal}"
                           onchange="updateDataCell(${rIdx}, '${v.nome}', this.value, ${v.tipo})">
                </td>
            `;
        });

        colsHtml += `
            <td style="text-align: center; width: 40px;">
                <button class="btn btn-danger btn-sm" onclick="deleteDataRow(${rIdx})" title="Excluir amostra #${rowIdVal}" style="padding: 2px 6px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
                </button>
            </td>
        `;

        tr.innerHTML = colsHtml;
        tbody.appendChild(tr);
    });

    document.getElementById('lbl-amostra-count').innerText = `${dados.filter(d => d.habilitado).length} de ${dados.length} dados ativos`;
    const chkFilter = document.getElementById('chk-apenas-ativas');
    if (chkFilter) chkFilter.checked = filterOnlyActiveVars;
}

function updateDataCell(rIdx, varName, val, varType) {
    state.project.dados[rIdx].valores[varName] = varType === 1 ? (parseFloat(val) || 0.0) : val;
    state.exploratoryDirty = true;
    state.regressionDirty = true;
    state.laudoDirty = true;
    if (state.unsavedChanges) state.unsavedChanges.dados = true;
}

function toggleRowEnabled(rIdx, checked) {
    state.project.dados[rIdx].habilitado = checked;
    state.exploratoryDirty = true;
    state.regressionDirty = true;
    state.laudoDirty = true;
    if (state.unsavedChanges) state.unsavedChanges.dados = true;
    renderDataTable();
}

function toggleRowOutlier(rIdx, checked) {
    state.project.dados[rIdx].outlier = checked;
    state.exploratoryDirty = true;
    state.regressionDirty = true;
    state.laudoDirty = true;
    if (state.unsavedChanges) state.unsavedChanges.dados = true;
    renderDataTable();
}

function addDataRow() {
    state.exploratoryDirty = true;
    state.regressionDirty = true;
    state.laudoDirty = true;
    if (state.unsavedChanges) state.unsavedChanges.dados = true;
    const newRow = {
        id: state.project.dados.length + 1,
        habilitado: true,
        outlier: false,
        valores: {}
    };
    state.project.variaveis.forEach(v => {
        newRow.valores[v.nome] = v.tipo === 1 ? 0.0 : '';
    });
    state.project.dados.push(newRow);
    renderDataTable();
}

function deleteDataRow(rIdx) {
    state.exploratoryDirty = true;
    state.regressionDirty = true;
    state.laudoDirty = true;
    if (state.unsavedChanges) state.unsavedChanges.dados = true;
    state.project.dados.splice(rIdx, 1);
    state.project.dados.forEach((d, i) => d.id = i + 1);
    renderDataTable();
}

async function saveData() {
    state.exploratoryDirty = true;
    state.regressionDirty = true;
    state.laudoDirty = true;
    await fetch('/api/data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state.project.dados)
    });
    if (state.unsavedChanges) state.unsavedChanges.dados = false;
    showToast('Dados amostrais salvos com sucesso!');
}

// ==================== ABA 4: ANÁLISE EXPLORATÓRIA ====================
async function loadExploratoryData() {
    try {
        const resp = await fetch('/api/exploratory');
        state.exploratoryData = await resp.json();
        state.exploratoryDirty = false;
        renderExploratoryView();
    } catch (err) {
        console.error('Erro ao carregar dados exploratórios:', err);
    }
}

function renderExploratoryView() {
    if (!state.exploratoryData) return;

    const vars = state.exploratoryData.variables || [];
    const selX = document.getElementById('select-exp-indep');
    const selY = document.getElementById('select-exp-dep');

    if (vars.length === 0) {
        if (selX) selX.innerHTML = '<option value="">(Nenhuma variável)</option>';
        if (selY) selY.innerHTML = '<option value="">(Nenhuma variável)</option>';
        return;
    }

    // Identifica qual variável é dependente por padrão (classificacao === 7)
    const depVarObj = (state.project?.variaveis || []).find(v => v.classificacao === 7 && vars.includes(v.nome));
    const defaultDepName = depVarObj ? depVarObj.nome : vars[0];

    // Identifica qual variável independente exibir primeiro
    const indepVarObj = (state.project?.variaveis || []).find(v => v.classificacao !== 7 && vars.includes(v.nome));
    const defaultIndepName = indepVarObj ? indepVarObj.nome : (vars.length > 1 ? vars[1] : vars[0]);

    if (!state.selectedExpY || !vars.includes(state.selectedExpY)) {
        state.selectedExpY = defaultDepName;
    }
    if (!state.selectedExpX || !vars.includes(state.selectedExpX)) {
        state.selectedExpX = (state.selectedExpY === defaultIndepName && vars.length > 1)
            ? (vars.find(v => v !== state.selectedExpY) || defaultIndepName)
            : defaultIndepName;
    }

    if (selX) {
        selX.innerHTML = vars.map(v => `<option value="${v}" ${v === state.selectedExpX ? 'selected' : ''}>${v}</option>`).join('');
        selX.value = state.selectedExpX;
    }

    if (selY) {
        selY.innerHTML = vars.map(v => `<option value="${v}" ${v === state.selectedExpY ? 'selected' : ''}>${v}</option>`).join('');
        selY.value = state.selectedExpY;
    }

    updateExploratoryCharts();
    renderCorrelationHeatmap();
}

function updateExploratoryX(varName) {
    state.selectedExpX = varName;
    updateExploratoryCharts();
}

function updateExploratoryY(varName) {
    state.selectedExpY = varName;
    updateExploratoryCharts();
}

function updateExploratoryCharts() {
    if (!state.exploratoryData || !state.selectedExpX || !state.selectedExpY) return;

    const varX = state.selectedExpX;
    const varY = state.selectedExpY;
    const statsX = state.exploratoryData.stats?.[varX];
    const statsY = state.exploratoryData.stats?.[varY];
    if (!statsX) return;

    // Estatísticas descritivas da variável X
    const elN = document.getElementById('exp-n');
    if (elN) elN.innerText = statsX.n;
    const elMedia = document.getElementById('exp-media');
    if (elMedia) elMedia.innerText = statsX.media.toLocaleString();
    const elMediana = document.getElementById('exp-mediana');
    if (elMediana) elMediana.innerText = statsX.mediana.toLocaleString();
    const elDesvio = document.getElementById('exp-desvio');
    if (elDesvio) elDesvio.innerText = statsX.desvio_padrao.toLocaleString();
    const elCv = document.getElementById('exp-cv');
    if (elCv) elCv.innerText = `${statsX.cv_pct}%`;
    const elMin = document.getElementById('exp-min');
    if (elMin) elMin.innerText = statsX.minimo.toLocaleString();
    const elMax = document.getElementById('exp-max');
    if (elMax) elMax.innerText = statsX.maximo.toLocaleString();

    // Histograma da variável X
    const lblHist = document.getElementById('lbl-hist-var');
    if (lblHist) lblHist.innerText = varX;
    if (typeof renderExploratoryHist === 'function') {
        renderExploratoryHist('chart-exp-hist', statsX.histogram, varX);
    }

    // Gráfico de dispersão X vs Y e correlação linear de Pearson
    const lblScatterTitle = document.getElementById('lbl-scatter-title');
    if (lblScatterTitle) {
        lblScatterTitle.innerText = `Dispersão: ${varY} vs ${varX}`;
    }

    const corrVal = state.exploratoryData.correlations?.[varX]?.[varY] ??
                   state.exploratoryData.correlations?.[varY]?.[varX] ?? 0.0;
    const lblScatterCorr = document.getElementById('lbl-scatter-corr');
    if (lblScatterCorr) {
        lblScatterCorr.innerText = `r = ${corrVal >= 0 ? '+' : ''}${corrVal.toFixed(4)}`;
        const absVal = Math.abs(corrVal);
        if (absVal >= 0.7) {
            lblScatterCorr.className = 'badge badge-g3';
            lblScatterCorr.title = `Forte correlação (|r| >= 0.70): ${corrVal.toFixed(4)}`;
        } else if (absVal >= 0.4) {
            lblScatterCorr.className = 'badge badge-g2';
            lblScatterCorr.title = `Correlação moderada (0.40 <= |r| < 0.70): ${corrVal.toFixed(4)}`;
        } else {
            lblScatterCorr.className = 'badge badge-g1';
            lblScatterCorr.title = `Correlação fraca (|r| < 0.40): ${corrVal.toFixed(4)}`;
        }
    }

    if (statsY && typeof renderExploratoryScatter === 'function') {
        const sampleIds = statsX.sample_ids || state.exploratoryData?.sample_ids;
        renderExploratoryScatter('chart-exp-scatter', statsX.raw_values, statsY.raw_values, varX, varY, sampleIds);
    }
}

function renderCorrelationHeatmap() {
    const container = document.getElementById('correlation-matrix-container');
    if (!container || !state.exploratoryData) return;

    const corrs = state.exploratoryData.correlations;
    const vars = state.exploratoryData.variables;
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    let tableHtml = '<table class="data-table" style="font-size:12px;"><thead><tr><th title="Variável de referência">Variável</th>';
    vars.forEach(v => tableHtml += `<th title="Correlação com ${v}">${v}</th>`);
    tableHtml += '</tr></thead><tbody>';

    vars.forEach(v1 => {
        tableHtml += `<tr><td style="font-weight:bold;">${v1}</td>`;
        vars.forEach(v2 => {
            const val = corrs[v1]?.[v2] || 0.0;
            const absVal = Math.abs(val);
            let bg = 'transparent';
            let textColor = 'inherit';
            if (v1 === v2) {
                bg = isDark ? '#334155' : '#f1f5f9';
                textColor = isDark ? '#f8fafc' : '#0f172a';
            } else if (absVal >= 0.8) {
                bg = isDark ? 'rgba(239, 68, 68, 0.35)' : '#fee2e2';
                textColor = isDark ? '#fca5a5' : '#b91c1c';
            } else if (absVal >= 0.5) {
                bg = isDark ? 'rgba(245, 158, 11, 0.35)' : '#fef3c7';
                textColor = isDark ? '#fcd34d' : '#b45309';
            } else {
                bg = isDark ? 'rgba(34, 197, 94, 0.2)' : '#f0fdf4';
                textColor = isDark ? '#86efac' : '#15803d';
            }
            const tip = `Correlação linear entre ${v1} e ${v2}: ${val.toFixed(4)}${absVal >= 0.8 ? ' (Forte correlação - risco de multicolinearidade)' : ''}`;
            tableHtml += `<td style="background-color:${bg}; color:${textColor}; text-align:center; font-weight:${absVal >= 0.7 ? 'bold' : 'normal'};" title="${tip}">${val.toFixed(3)}</td>`;
        });
        tableHtml += '</tr>';
    });
    tableHtml += '</tbody></table>';
    container.innerHTML = tableHtml;
}
window.renderCorrelationMatrix = renderCorrelationHeatmap;

// ==================== ABA 5: REGRESSÃO LINEAR ====================
async function calculateRegression() {
    showToast('Executando busca de modelos de regressão...');
    try {
        const resp = await fetch('/api/calculate', { method: 'POST' });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Erro no cálculo');
        }
        const data = await resp.json();
        state.project.modelos_calculados = data.modelos;
        state.selectedModelIdx = 0;
        state.regressionDirty = true;
        state.laudoDirty = true;
        state.lastRenderedModelIdx = -1;
        state.lastLaudoModelIdx = -1;
        renderRegressionView();
        showToast(`${data.count} modelos calculados com sucesso!`);
    } catch (e) {
        alert('Erro ao calcular: ' + e.message);
    }
}

function renderRegressionView() {
    const models = state.project.modelos_calculados || [];
    const containerRank = document.getElementById('tbody-modelos-ranking');
    if (!containerRank) return;

    state.lastRenderedModelIdx = state.selectedModelIdx;
    state.regressionDirty = false;

    // Tabela de ranking dos modelos
    containerRank.innerHTML = '';

    if (models.length === 0) {
        containerRank.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 28px 16px; color: var(--text-muted); font-size: 13px;">Nenhum modelo calculado ainda. Insira os dados da amostra e clique em <strong>"Calcular Regressão"</strong> ou carregue um exemplo em <strong>"Exemplos .sda"</strong>.</td></tr>`;
        const eqDisplay = document.getElementById('eq-display');
        if (eqDisplay) eqDisplay.innerText = 'Aguardando dados amostrais e cálculo da regressão...';
        ['stat-r', 'stat-r2', 'stat-r2-orig', 'stat-f', 'stat-sig-f', 'stat-se', 'stat-dw'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerText = '-';
        });
        const badgeFund = document.getElementById('badge-fundamentacao');
        if (badgeFund) { badgeFund.innerText = '-'; badgeFund.className = 'badge'; }
        const badgePrec = document.getElementById('badge-precisao');
        if (badgePrec) { badgePrec.innerText = '-'; badgePrec.className = 'badge'; }
        const nbrResumo = document.getElementById('nbr-resumo-texto');
        if (nbrResumo) nbrResumo.innerText = 'Aguardando cálculo para avaliação dos Graus de Fundamentação e Precisão (NBR 14653).';
        const tbodyReg = document.getElementById('tbody-regressores');
        if (tbodyReg) tbodyReg.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:16px;">Nenhum regressor calculado</td></tr>';
        const tbodyRes = document.getElementById('tbody-residuos');
        if (tbodyRes) tbodyRes.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding:16px;">Nenhum resíduo calculado</td></tr>';
        return;
    }

    let rowsHtml = '';
    models.forEach((m, idx) => {
        const isSelected = idx === state.selectedModelIdx;
        const rowStyle = isSelected ? 'background-color: var(--primary-light); font-weight: bold;' : '';
        const invBadge = m.inversao_detectada 
            ? '<span class="badge badge-danger" title="Inversão de sinal detectada: regressores com coeficientes incoerentes com o mercado">Invertido</span>' 
            : '<span class="badge badge-g3" title="Sinais físicos e econômicos dos regressores corretos">OK</span>';
        
        let fundClass = 'badge-g1';
        if (m.nbr) {
            if (m.nbr.grau_fundamentacao === 'Grau III') fundClass = 'badge-g3';
            else if (m.nbr.grau_fundamentacao === 'Grau II') fundClass = 'badge-g2';
            else if (m.nbr.grau_fundamentacao === 'Não Enquadrado') fundClass = 'badge-danger';
        }
        const fundBadge = m.nbr ? `<span class="badge ${fundClass}" title="Enquadramento NBR 14653-2: ${m.nbr.resumo_analitico}">${m.nbr.grau_fundamentacao}</span>` : '';

        rowsHtml += `
            <tr style="cursor: pointer; ${rowStyle}" onclick="selectModel(${idx})">
                <td style="text-align:center;">${m.id}</td>
                <td style="text-align:right;">${m.r.toFixed(4)}</td>
                <td style="text-align:right; font-weight:bold; color:var(--primary);">${(m.r2 * 100).toFixed(2)}%</td>
                <td style="text-align:right;">${(m.r2_original * 100).toFixed(2)}%</td>
                <td style="text-align:right;">${m.anova.f_calc.toFixed(2)}</td>
                <td style="text-align:right;">${m.erro_padrao.toFixed(4)}</td>
                <td style="text-align:center;">${m.durbin_watson.toFixed(2)}</td>
                <td style="text-align:center;">${invBadge}</td>
                <td style="text-align:center;">${fundBadge}</td>
            </tr>
        `;
    });
    containerRank.innerHTML = rowsHtml;

    if (models.length > 0) {
        renderModelDetails(models[state.selectedModelIdx]);
    }
}

function selectModel(idx) {
    if (state.selectedModelIdx === idx && state.lastRenderedModelIdx === idx) return;
    state.selectedModelIdx = idx;
    state.lastRenderedModelIdx = idx;
    state.laudoDirty = true;

    const containerRank = document.getElementById('tbody-modelos-ranking');
    if (containerRank) {
        const rows = containerRank.querySelectorAll('tr');
        rows.forEach((r, i) => {
            if (i === idx) {
                r.style.backgroundColor = 'var(--primary-light)';
                r.style.fontWeight = 'bold';
            } else {
                r.style.backgroundColor = '';
                r.style.fontWeight = 'normal';
            }
        });
    }

    const models = state.project.modelos_calculados || [];
    if (models[idx]) {
        renderModelDetails(models[idx]);
    }
}

function renderModelDetails(model) {
    if (!model) return;

    // Equação
    document.getElementById('eq-display').innerText = model.equacao_texto;

    // Estatísticas principais
    document.getElementById('stat-r').innerText = model.r.toFixed(4);
    document.getElementById('stat-r2').innerText = `${(model.r2 * 100).toFixed(2)}%`;
    document.getElementById('stat-r2-orig').innerText = `${(model.r2_original * 100).toFixed(2)}%`;
    document.getElementById('stat-f').innerText = model.anova.f_calc.toFixed(2);
    document.getElementById('stat-sig-f').innerText = `${model.anova.significancia_f_pct.toFixed(4)}%`;
    document.getElementById('stat-se').innerText = model.erro_padrao.toFixed(4);
    document.getElementById('stat-dw').innerText = `${model.durbin_watson.toFixed(2)} (${model.durbin_watson_status})`;

    // NBR 14653 Badges
    if (model.nbr) {
        document.getElementById('badge-fundamentacao').innerText = model.nbr.grau_fundamentacao;
        document.getElementById('badge-fundamentacao').className = `badge ${model.nbr.grau_fundamentacao === 'Grau III' ? 'badge-g3' : (model.nbr.grau_fundamentacao === 'Grau II' ? 'badge-g2' : (model.nbr.grau_fundamentacao === 'Grau I' ? 'badge-g1' : 'badge-danger'))}`;
        document.getElementById('badge-precisao').innerText = `${model.nbr.grau_precisao} (${model.nbr.amplitude_ic_pct}%)`;
        document.getElementById('badge-precisao').className = `badge ${model.nbr.grau_precisao === 'Grau III' ? 'badge-g3' : (model.nbr.grau_precisao === 'Grau II' ? 'badge-g2' : (model.nbr.grau_precisao === 'Grau I' ? 'badge-g1' : 'badge-danger'))}`;
        document.getElementById('nbr-resumo-texto').innerText = model.nbr.resumo_analitico;
    }

    // Diagnósticos Técnicos & Sugestões de Ajuste (NBR 14653)
    const diagContainer = document.getElementById('card-diagnosticos-container');
    const diagList = document.getElementById('box-diagnosticos-list');
    const diagBadge = document.getElementById('diagnosticos-count-badge');
    const diags = model.diagnosticos_tecnicos || (model.nbr ? model.nbr.diagnosticos_ajuste : []) || [];

    if (diagContainer && diagList) {
        if (diags.length > 0) {
            diagContainer.style.display = 'block';
            if (diagBadge) diagBadge.innerText = `${diags.length} Orientação${diags.length > 1 ? 'ões' : ''}`;
            
            let htmlList = '';
            diags.forEach(d => {
                let cardType = 'info';
                let iconName = 'info';
                if (d.includes('❌')) {
                    cardType = 'danger';
                    iconName = 'alert-circle';
                } else if (d.includes('⚠️')) {
                    cardType = 'warning';
                    iconName = 'alert-triangle';
                } else if (d.includes('✅')) {
                    cardType = 'success';
                    iconName = 'check-circle-2';
                }
                
                const cleanText = d.replace(/^[❌⚠️✅ℹ️]\s*/, '');
                htmlList += `
                    <div class="insight-card ${cardType}">
                        <i data-lucide="${iconName}" style="width: 18px; height: 18px; flex-shrink: 0; margin-top: 2px;"></i>
                        <div style="flex: 1;">${cleanText}</div>
                    </div>
                `;
            });
            diagList.innerHTML = htmlList;
            if (window.lucide) lucide.createIcons({ root: diagList });
        } else {
            diagContainer.style.display = 'none';
        }
    }

    // Regressores Table
    const tbodyReg = document.getElementById('tbody-regressores');
    if (tbodyReg) {
        let regHtml = '';
        model.regressores.forEach(r => {
            const invStyle = r.sinal_invertido ? 'color: red; font-weight: bold;' : '';
            const vifTip = r.vif > 10 ? 'title="Multicolinearidade severa (VIF > 10). Sugestão: remova esta variável redundante."' : (r.vif > 5 ? 'title="Multicolinearidade moderada (VIF > 5)."' : 'title="Fator de Inflação da Variância adequado."');
            const tTip = r.significancia_pct > 30 ? 'title="Significância fraca (> 30%). Não atende aos requisitos mínimos da NBR 14653."' : `title="Significância t: ${r.significancia_pct.toFixed(2)}%"`;
            const coefTip = r.sinal_invertido ? 'title="Inversão de Sinal detectada: sinal algébrico oposto à lógica de mercado esperada."' : 'title="Coeficiente estimado com sinal físico-econômico coerente"';

            regHtml += `
                <tr>
                    <td><strong>${r.nome_exibicao}</strong></td>
                    <td style="text-align:center;">${r.transformacao_codigo}</td>
                    <td style="text-align:right; font-family:monospace; ${invStyle}" ${coefTip}>${r.coeficiente.toFixed(6)}</td>
                    <td style="text-align:right;">${r.erro_padrao.toFixed(6)}</td>
                    <td style="text-align:right; font-weight:bold;">${r.t_calc.toFixed(3)}</td>
                    <td style="text-align:right; ${invStyle}" ${tTip}>${r.significancia_pct.toFixed(2)}%</td>
                    <td style="text-align:right;">${r.elasticidade_media.toFixed(4)}</td>
                    <td style="text-align:right;" ${vifTip}>${r.vif.toFixed(2)}</td>
                </tr>
            `;
        });
        tbodyReg.innerHTML = regHtml;
    }

    // Gráficos
    renderAderenciaChart('chart-aderencia', model.residuos);
    renderResiduosChart('chart-residuos', model.residuos, model.erro_padrao);
    renderCookChart('chart-cook', model.residuos);
    renderNormalidadeChart('chart-normalidade', model.residuos);

    // Gráfico da Função Estimativa (Curva de Regressão por Variável)
    const selCurva = document.getElementById('select-curva-regressor');
    if (selCurva && model.regressores) {
        const curVal = selCurva.value;
        selCurva.innerHTML = '';
        model.regressores.forEach((r, rIdx) => {
            const opt = document.createElement('option');
            opt.value = rIdx;
            opt.textContent = `${r.nome_exibicao} (${r.transformacao_codigo})`;
            selCurva.appendChild(opt);
        });
        if (curVal !== '' && parseInt(curVal) < model.regressores.length) {
            selCurva.value = curVal;
        }
        updateCurvaChart();
    }

    // Tabela de Resíduos
    const tbodyRes = document.getElementById('tbody-residuos');
    if (tbodyRes) {
        let resHtml = '';
        model.residuos.forEach(r => {
            const outlierClass = r.is_outlier ? 'class="row-outlier"' : '';
            resHtml += `
                <tr ${outlierClass} style="cursor: pointer;" title="Clique para localizar a amostra #${r.index} na tabela de dados" onclick="window.navigateToDataRow(${r.index})">
                    <td style="text-align:center;">#${r.index}</td>
                    <td style="text-align:right;">${r.observado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td style="text-align:right; font-weight:bold;">${r.estimado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td style="text-align:right;">${r.residuo_ordinario.toFixed(2)}</td>
                    <td style="text-align:right; ${r.residuo_relativo_pct > 40 ? 'color:red;font-weight:bold;' : ''}">${r.residuo_relativo_pct.toFixed(1)}%</td>
                    <td style="text-align:right; ${Math.abs(r.residuo_studentizado) > 2 ? 'color:red;font-weight:bold;' : ''}">${r.residuo_studentizado.toFixed(2)}</td>
                    <td style="text-align:right; ${r.distancia_cook > 1 ? 'color:red;font-weight:bold;' : ''}">${r.distancia_cook.toFixed(4)}</td>
                </tr>
            `;
        });
        tbodyRes.innerHTML = resHtml;
    }
}

function updateCurvaChart() {
    const models = state.project?.modelos_calculados || [];
    const model = models[state.selectedModelIdx];
    if (!model || !model.regressores || model.regressores.length === 0) return;

    const selCurva = document.getElementById('select-curva-regressor');
    const regIdx = selCurva ? parseInt(selCurva.value || 0) : 0;
    const reg = model.regressores[regIdx] || model.regressores[0];
    if (!reg) return;

    const varName = reg.nome_original;
    const depVarName = model.var_dep_nome;
    const depTransf = model.transformacao_dep || 'x';

    const amostra = (state.project.dados || []).filter(d => d.habilitado);
    if (amostra.length === 0) return;

    const samplePoints = amostra.map(d => ({
        x: parseFloat(d.valores[varName]) || 0.0,
        y: parseFloat(d.valores[depVarName]) || 0.0,
        id: d.id
    })).filter(p => !isNaN(p.x) && !isNaN(p.y));

    if (samplePoints.length === 0) return;

    const regMeans = {};
    model.regressores.forEach(r => {
        const vals = amostra.map(d => parseFloat(d.valores[r.nome_original]) || 0.0);
        regMeans[r.nome_original] = vals.reduce((a, b) => a + b, 0) / vals.length;
    });

    function applyT(tCode, v) {
        if (tCode === '1/x') return 1.0 / (v === 0 ? 1e-6 : v);
        if (tCode === 'ln(x)') return Math.log(Math.max(1e-6, v));
        if (tCode === 'x2') return v * v;
        if (tCode === '1/x2') return 1.0 / Math.max(1e-12, v * v);
        if (tCode === 'x(1/2)') return Math.sqrt(Math.max(0, v));
        if (tCode === '1/x(1/2)') return 1.0 / Math.sqrt(Math.max(1e-6, v));
        return v;
    }

    function applyInvDep(tCode, v) {
        if (tCode === '1/x') return 1.0 / (v === 0 ? 1e-6 : v);
        if (tCode === 'ln(x)') return Math.exp(Math.min(50, Math.max(-50, v)));
        if (tCode === 'x2') return Math.sqrt(Math.max(0, v));
        if (tCode === '1/x2') return 1.0 / Math.sqrt(Math.max(1e-12, v));
        if (tCode === 'x(1/2)') return v * v;
        if (tCode === '1/x(1/2)') return 1.0 / Math.max(1e-12, v * v);
        return v;
    }

    let otherSum = model.intercepto;
    model.regressores.forEach((r, idx) => {
        if (idx !== regIdx) {
            const meanX = regMeans[r.nome_original] || 0.0;
            otherSum += r.coeficiente * applyT(r.transformacao_codigo, meanX);
        }
    });

    const xObs = samplePoints.map(p => p.x);
    let minX = Math.min(...xObs);
    let maxX = Math.max(...xObs);
    if (minX === maxX) { minX *= 0.8; maxX *= 1.2; }
    const span = maxX - minX;
    const xStep = span / 60;

    const curvePoints = [];
    for (let i = 0; i <= 60; i++) {
        const xVal = minX + i * xStep;
        const xTransf = applyT(reg.transformacao_codigo, xVal);
        const yTransfPred = otherSum + reg.coeficiente * xTransf;
        const yOrigPred = Math.max(0.01, applyInvDep(depTransf, yTransfPred));
        curvePoints.push({ x: xVal, y: yOrigPred });
    }

    if (typeof window.renderCurvaEstimativaChart === 'function') {
        window.renderCurvaEstimativaChart('chart-curva-estimativa', varName, depVarName, samplePoints, curvePoints, reg.sinal_invertido);
    }

    const badge = document.getElementById('curva-status-badge');
    if (badge) {
        if (reg.sinal_invertido) {
            badge.innerHTML = '<span class="badge badge-danger">Inversão de Sinal Físico-Econômico</span>';
        } else {
            badge.innerHTML = '<span class="badge badge-g3">Sinal Coerente</span>';
        }
    }
}
window.updateCurvaChart = updateCurvaChart;

// ==================== ABA 6: REDES NEURAIS (RNA) ====================
async function trainRNA() {
    showToast('Treinando Rede Neural Artificial...');
    const formData = new FormData();
    formData.append('hidden_neurons', document.getElementById('rna-neurons').value);
    formData.append('activation', document.getElementById('rna-activation').value);
    formData.append('max_iter', document.getElementById('rna-iter').value);
    formData.append('learning_rate', document.getElementById('rna-lr').value);
    formData.append('solver', document.getElementById('rna-solver').value);
    formData.append('bagging', document.getElementById('rna-bagging').checked);

    try {
        const resp = await fetch('/api/rna/train', { method: 'POST', body: formData });
        const res = await resp.json();
        if (res.status === 'ok') {
            const data = res.resultado;
            document.getElementById('rna-r2').innerText = `${(data.r2 * 100).toFixed(2)}%`;
            document.getElementById('rna-r').innerText = data.r.toFixed(4);
            document.getElementById('rna-rmse').innerText = data.rmse.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            document.getElementById('rna-mape').innerText = `${data.mape_pct}%`;
            const elIter = document.getElementById('rna-iter-done');
            if (elIter) elIter.innerText = data.n_iter;

            renderRnaLossChart('chart-rna-loss', data.loss_curve);
            showToast('Rede Neural treinada com sucesso!');
        }
    } catch (e) {
        alert('Erro ao treinar RNA: ' + e.message);
    }
}

// ==================== ABA 7: PROJEÇÃO / IMÓVEL AVALIANDO ====================
function renderSubjectTable() {
    const thead = document.getElementById('thead-sujeito');
    const tbody = document.getElementById('tbody-sujeito');
    if (!tbody || !state.project) return;

    const projs = state.project.projecoes || [];
    const vars = state.project.variaveis || [];

    if (thead) {
        thead.innerHTML = `
            <tr>
                <th style="width: 150px;">Identificação do Avaliando</th>
                ${vars.map(v => `<th style="${v.classificacao === 7 ? 'color: #0284c7; font-weight: bold;' : ''}">${v.nome}</th>`).join('')}
                <th style="width: 40px; text-align: center;">Ação</th>
            </tr>
        `;
    }

    tbody.innerHTML = '';
    projs.forEach((p, pIdx) => {
        let cols = `<td style="width: 150px;"><input type="text" class="table-input" value="${p.identificacao}" onchange="updateSubjectIdent(${pIdx}, this.value)"></td>`;
        vars.forEach(v => {
            const val = p.valores[v.nome] !== undefined ? p.valores[v.nome] : '';
            cols += `<td><input type="${v.tipo === 1 ? 'number' : 'text'}" step="any" class="table-input" value="${val}" onchange="updateSubjectCell(${pIdx}, '${v.nome}', this.value, ${v.tipo})"></td>`;
        });
        cols += `
            <td style="text-align: center; width: 40px;">
                <button class="btn btn-danger btn-sm" onclick="deleteSubjectRow(${pIdx})"><i data-lucide="trash-2" style="width:13px;height:13px;"></i></button>
            </td>
        `;
        tbody.innerHTML += `<tr>${cols}</tr>`;
    });

    // Se houver modelo selecionado e projeções calculadas
    const models = state.project.modelos_calculados || [];
    const depVar = vars.find(v => v.classificacao === 7) || vars.filter(v => v.tipo === 1).slice(-1)[0];
    const unitSuffix = (depVar && depVar.unitario) ? '/m²' : '';

    if (models.length > 0 && models[state.selectedModelIdx]?.projecoes?.length > 0) {
        const valRes = models[state.selectedModelIdx].projecoes[0];
        document.getElementById('val-unitario-est').innerText = `R$ ${valRes.valor_estimado_unitario.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}${unitSuffix}`;
        document.getElementById('val-unitario-arred').innerText = `R$ ${valRes.valor_arredondado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}${unitSuffix}`;
        document.getElementById('val-ic-faixa').innerText = `[R$ ${valRes.ic_inferior.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} a R$ ${valRes.ic_superior.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}]`;
        document.getElementById('val-ic-amp').innerText = `${valRes.amplitude_ic_pct.toFixed(2)}% (${valRes.grau_precisao})`;
        document.getElementById('val-arbitrio').innerText = `[R$ ${valRes.campo_arbitrio_min.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} a R$ ${valRes.campo_arbitrio_max.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}]`;

        if (valRes.valor_total_estimado) {
            document.getElementById('val-total-box').style.display = 'block';
            document.getElementById('val-total-num').innerText = `R$ ${valRes.valor_total_estimado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        } else {
            document.getElementById('val-total-box').style.display = 'none';
        }
    } else {
        document.getElementById('val-unitario-est').innerText = '-';
        document.getElementById('val-unitario-arred').innerText = '-';
        document.getElementById('val-ic-faixa').innerText = '-';
        document.getElementById('val-ic-amp').innerText = '-';
        document.getElementById('val-arbitrio').innerText = '-';
        document.getElementById('val-total-box').style.display = 'none';
    }
    if (window.lucide) lucide.createIcons();
}

function addSubjectRow() {
    if (state.unsavedChanges) state.unsavedChanges.avaliandos = true;
    const newProj = {
        id: `proj_${(state.project.projecoes || []).length + 1}`,
        identificacao: `Imóvel Avaliando ${(state.project.projecoes || []).length + 1}`,
        valores: {}
    };
    state.project.variaveis.forEach(v => {
        newProj.valores[v.nome] = v.tipo === 1 ? 0.0 : '';
    });
    if (!state.project.projecoes) state.project.projecoes = [];
    state.project.projecoes.push(newProj);
    renderSubjectTable();
}

function deleteSubjectRow(pIdx) {
    if (state.project.projecoes && state.project.projecoes.length > 1) {
        if (state.unsavedChanges) state.unsavedChanges.avaliandos = true;
        state.project.projecoes.splice(pIdx, 1);
        renderSubjectTable();
    } else {
        showToast('Mantenha ao menos um imóvel avaliando.');
    }
}

// Opções de cálculo
function toggleCalculationOptions() {
    const panel = document.getElementById('panel-calculation-options');
    const icon = document.getElementById('opt-toggle-icon');
    if (!panel) return;
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        if (icon) icon.innerText = 'Ocultar ▲';
        loadCalculationOptions();
    } else {
        panel.style.display = 'none';
        if (icon) icon.innerText = 'Configurar ▼';
    }
    if (window.lucide) lucide.createIcons();
}

function loadCalculationOptions() {
    if (!state.project || !state.project.opcoes) return;
    const opt = state.project.opcoes;
    const elMetodo = document.getElementById('opt-metodo');
    if (elMetodo) elMetodo.value = opt.metodo || 'todas';
    const elSelecao = document.getElementById('opt-selecao');
    if (elSelecao) elSelecao.value = opt.selecao_modelo || 'estimativa';
    const elEstimador = document.getElementById('opt-estimador');
    if (elEstimador) elEstimador.value = opt.estimador || 'mq';
    const elConf = document.getElementById('opt-conf-level');
    if (elConf) elConf.value = (opt.nivel_confianca || 0.80).toString();
    const elLimite = document.getElementById('opt-limite');
    if (elLimite) elLimite.value = opt.limite_modelos || 100;

    const transf = new Set(opt.transformacoes || ['x', '1/x', 'ln(x)']);
    if (document.getElementById('transf-x')) document.getElementById('transf-x').checked = transf.has('x');
    if (document.getElementById('transf-inv')) document.getElementById('transf-inv').checked = transf.has('1/x');
    if (document.getElementById('transf-ln')) document.getElementById('transf-ln').checked = transf.has('ln(x)');
    if (document.getElementById('transf-x2')) document.getElementById('transf-x2').checked = transf.has('x2');
    if (document.getElementById('transf-inv2')) document.getElementById('transf-inv2').checked = transf.has('1/x2');
    if (document.getElementById('transf-sqrt')) document.getElementById('transf-sqrt').checked = transf.has('x(1/2)');
    if (document.getElementById('transf-invsqrt')) document.getElementById('transf-invsqrt').checked = transf.has('1/x(1/2)');
}

async function saveCalculationOptions() {
    const transf = [];
    if (document.getElementById('transf-x')?.checked) transf.push('x');
    if (document.getElementById('transf-inv')?.checked) transf.push('1/x');
    if (document.getElementById('transf-ln')?.checked) transf.push('ln(x)');
    if (document.getElementById('transf-x2')?.checked) transf.push('x2');
    if (document.getElementById('transf-inv2')?.checked) transf.push('1/x2');
    if (document.getElementById('transf-sqrt')?.checked) transf.push('x(1/2)');
    if (document.getElementById('transf-invsqrt')?.checked) transf.push('1/x(1/2)');

    if (transf.length === 0) transf.push('x');

    const payload = {
        metodo: document.getElementById('opt-metodo')?.value || 'todas',
        selecao_modelo: document.getElementById('opt-selecao')?.value || 'estimativa',
        estimador: document.getElementById('opt-estimador')?.value || 'mq',
        transformacoes: transf,
        nivel_confianca: parseFloat(document.getElementById('opt-conf-level')?.value || '0.80'),
        campo_arbitrio_pct: 15.0,
        arredondamento_pct: 1.0,
        limite_modelos: parseInt(document.getElementById('opt-limite')?.value) || 100
    };

    await fetch('/api/options', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    state.project.opcoes = payload;
    showToast('Opções salvas! Recalculando...');
    await calculateRegression();
}

function updateSubjectIdent(pIdx, val) {
    if (state.unsavedChanges) state.unsavedChanges.avaliandos = true;
    state.project.projecoes[pIdx].identificacao = val;
}

function updateSubjectCell(pIdx, varName, val, varType) {
    if (state.unsavedChanges) state.unsavedChanges.avaliandos = true;
    state.project.projecoes[pIdx].valores[varName] = varType === 1 ? (parseFloat(val) || 0.0) : val;
}

async function saveSubjects() {
    try {
        const resp = await fetch('/api/subjects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state.project.projecoes)
        });
        if (resp.ok) {
            const data = await resp.json();
            if (data.modelos) {
                state.project.modelos_calculados = data.modelos;
                state.laudoDirty = true;
            }
        }
        if (state.unsavedChanges) state.unsavedChanges.avaliandos = false;
        showToast('Imóvel avaliando salvo e avaliado!');
        renderSubjectTable();
    } catch (err) {
        showToast('Imóvel avaliando salvo!');
        renderSubjectTable();
    }
}

// ==================== ABA 8: RELATÓRIO NBR 14653 PREVIEW & PERSONALIZAÇÃO ====================
let tempReportLogo = null;

async function renderLaudoPreview() {
    const iframe = document.getElementById('iframe-laudo');
    const selectModel = document.getElementById('select-relatorio-modelo');

    if (selectModel && state.project?.modelos_calculados && state.project.modelos_calculados.length > 0) {
        selectModel.innerHTML = '';
        state.project.modelos_calculados.forEach((m, idx) => {
            const opt = document.createElement('option');
            opt.value = idx;
            const r2Txt = (m.r2 * 100).toFixed(2);
            opt.textContent = `Modelo #${m.id} (${m.var_dep_nome} - R² = ${r2Txt}%)`;
            if (idx === state.selectedModelIdx) opt.selected = true;
            selectModel.appendChild(opt);
        });
    }

    state.lastLaudoModelIdx = state.selectedModelIdx;
    state.laudoDirty = false;

    if (iframe) {
        iframe.src = `/report?model_idx=${state.selectedModelIdx}&_t=${Date.now()}`;
    }
}

function openReportCustomizer() {
    const m = state.project?.metadata || {};
    document.getElementById('rep-titulo').value = m.titulo_relatorio || 'RELATÓRIO DE AVALIAÇÃO IMOBILIÁRIA';
    document.getElementById('rep-subtitulo').value = m.subtitulo_relatorio || 'Em conformidade com a ABNT NBR 14653-2 (Imóveis Urbanos)';
    document.getElementById('rep-solicitante').value = m.solicitante || '';
    document.getElementById('rep-finalidade').value = m.finalidade || 'Determinação de Valor de Mercado';
    document.getElementById('rep-endereco').value = m.endereco_imovel || '';

    // Responsável Técnico
    document.getElementById('rep-autor').value = m.autor || 'Nome do Responsável';
    document.getElementById('rep-qualificacao').value = m.qualificacao_profissional || 'Engenheiro Avaliador';
    document.getElementById('rep-registro').value = m.registro_profissional || '';
    document.getElementById('rep-ibape').value = m.ibape_registro || '';

    // Empresa / Escritório (para Rodapé Institucional)
    document.getElementById('rep-empresa-nome').value = m.empresa_nome || '';
    document.getElementById('rep-empresa-cnpj').value = m.empresa_cnpj || '';
    document.getElementById('rep-empresa-crea').value = m.empresa_crea || '';
    document.getElementById('rep-empresa-telefone').value = m.empresa_telefone || '';
    document.getElementById('rep-empresa-email').value = m.empresa_email || '';
    document.getElementById('rep-empresa-site').value = m.empresa_site || '';
    document.getElementById('rep-empresa-endereco').value = m.empresa_endereco || '';

    document.getElementById('rep-observacoes').value = m.observacoes || '';

    tempReportLogo = m.logo_base64 || '';
    updateReportLogoPreview(tempReportLogo);

    openModal('modal-report-customizer');
}

function updateReportLogoPreview(logoBase64) {
    const previewImg = document.getElementById('report-logo-img');
    const placeholder = document.getElementById('report-logo-placeholder');
    const btnRemove = document.getElementById('btn-remover-logo');

    if (logoBase64 && logoBase64.trim()) {
        previewImg.src = logoBase64;
        previewImg.style.display = 'block';
        if (placeholder) placeholder.style.display = 'none';
        if (btnRemove) btnRemove.style.display = 'inline-flex';
    } else {
        // Padrão: Logotipo oficial do OpenValora
        previewImg.src = '/static/img/logo.png';
        previewImg.style.display = 'block';
        if (placeholder) placeholder.style.display = 'none';
        if (btnRemove) btnRemove.style.display = 'none';
    }
}

function removeReportLogo() {
    tempReportLogo = '';
    updateReportLogoPreview('');
}

function handleReportLogoSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
        showToast('A imagem da logomarca deve ter no máximo 2MB.', 'warning');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(evt) {
        tempReportLogo = evt.target.result;
        updateReportLogoPreview(tempReportLogo);
    };
    reader.readAsDataURL(file);
}

async function saveReportCustomizer() {
    if (!state.project) return;
    showToast('Salvando configurações do relatório...');

    const m = state.project.metadata || {};
    const payload = {
        ...m,
        titulo_relatorio: document.getElementById('rep-titulo').value.trim() || 'RELATÓRIO DE AVALIAÇÃO IMOBILIÁRIA',
        subtitulo_relatorio: document.getElementById('rep-subtitulo').value.trim() || 'Em conformidade com a ABNT NBR 14653-2 (Imóveis Urbanos)',
        solicitante: document.getElementById('rep-solicitante').value.trim(),
        finalidade: document.getElementById('rep-finalidade').value.trim() || 'Determinação de Valor de Mercado',
        endereco_imovel: document.getElementById('rep-endereco').value.trim(),
        autor: document.getElementById('rep-autor').value.trim() || m.autor || 'Nome do Responsável',
        qualificacao_profissional: document.getElementById('rep-qualificacao').value.trim() || 'Engenheiro Avaliador',
        registro_profissional: document.getElementById('rep-registro').value.trim(),
        ibape_registro: document.getElementById('rep-ibape').value.trim(),
        empresa_nome: document.getElementById('rep-empresa-nome').value.trim(),
        empresa_cnpj: document.getElementById('rep-empresa-cnpj').value.trim(),
        empresa_crea: document.getElementById('rep-empresa-crea').value.trim(),
        empresa_telefone: document.getElementById('rep-empresa-telefone').value.trim(),
        empresa_email: document.getElementById('rep-empresa-email').value.trim(),
        empresa_site: document.getElementById('rep-empresa-site').value.trim(),
        empresa_endereco: document.getElementById('rep-empresa-endereco').value.trim(),
        observacoes: document.getElementById('rep-observacoes').value.trim(),
        logo_base64: tempReportLogo !== null ? tempReportLogo : (m.logo_base64 || '')
    };

    try {
        const resp = await fetch('/api/project/metadata', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        state.project.metadata = payload;
        closeModal('modal-report-customizer');
        showToast('Relatório atualizado com sucesso!');
        renderLaudoPreview();
    } catch (err) {
        console.error('Erro ao salvar personalização:', err);
        showToast('Erro ao salvar personalização do relatório.', 'error');
    }
}

async function downloadReportPDF() {
    const iframe = document.getElementById('iframe-laudo');
    if (!iframe || !iframe.contentDocument) {
        showToast('Aguarde o carregamento do relatório...', 'warning');
        return;
    }

    const reportEl = iframe.contentDocument.getElementById('report-content');
    if (!reportEl) {
        showToast('Nenhum relatório pronto para exportação.', 'warning');
        return;
    }

    showToast('Compilando e gerando PDF formatado em A4...', 'info');

    const projName = (state.project?.metadata?.nome || 'Modelo').replace(/\s+/g, '_');
    const opt = {
        margin: [10, 8, 12, 8],
        filename: `Relatorio_OpenValora_${projName}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    const pdfLib = window.html2pdf || iframe.contentWindow?.html2pdf;
    if (pdfLib) {
        pdfLib().set(opt).from(reportEl).save().then(() => {
            showToast('Arquivo PDF baixado com sucesso!');
        }).catch(err => {
            console.error('Erro na compilação do PDF:', err);
            showToast('Falha na geração do PDF. Acionando diálogo de impressão...', 'warning');
            printReport();
        });
    } else {
        printReport();
    }
}

function printReport() {
    const iframe = document.getElementById('iframe-laudo');
    if (!iframe) return;

    try {
        if (iframe.contentWindow) {
            iframe.contentWindow.focus();
            iframe.contentWindow.print();
            return;
        }
    } catch (e) {
        console.warn('Impressão direta via iframe falhou:', e);
    }

    // Fallback universal: abre em nova janela/aba com gatilho de impressão automático
    const url = `/report?model_idx=${state.selectedModelIdx}&autoprint=1`;
    window.open(url, '_blank');
}

// ==================== MODAIS & UTILITÁRIOS ====================
async function openSamplesModal() {
    const resp = await fetch('/api/samples');
    const samples = await resp.json();
    const list = document.getElementById('modal-samples-list');
    list.innerHTML = '';

    samples.forEach(s => {
        const item = document.createElement('div');
        item.className = 'card';
        item.style.padding = '12px';
        item.style.cursor = 'pointer';
        item.style.display = 'flex';
        item.style.justifyContent = 'space-between';
        item.style.alignItems = 'center';
        item.innerHTML = `
            <div>
                <strong style="color:var(--primary); font-size:14px;">${s.filename}</strong>
                <div style="font-size:11px; color:var(--text-muted);">${(s.size_bytes / 1024).toFixed(1)} KB</div>
            </div>
            <button class="btn btn-primary btn-sm">Carregar</button>
        `;
        item.onclick = async () => {
            closeModal('modal-samples');
            showToast(`Carregando ${s.filename}...`);
            const formData = new FormData();
            formData.append('filename', s.filename);
            const r = await fetch('/api/samples/load', { method: 'POST', body: formData });
            state.project = await r.json();
            renderAll();
            showToast('Modelo carregado com sucesso!');
        };
        list.appendChild(item);
    });

    document.getElementById('modal-samples').style.display = 'flex';
}

function openNewModelModal() {
    document.getElementById('modal-new').style.display = 'flex';
}

async function createNewModelFromModal() {
    const tip = document.getElementById('new-model-tipologia').value;
    const formData = new FormData();
    formData.append('typology', tip);
    const resp = await fetch('/api/project/new', { method: 'POST', body: formData });
    state.project = await resp.json();
    closeModal('modal-new');
    renderAll();
    switchTab('variaveis');
    showToast(`Novo projeto "${tip}" criado!`);
}

async function openCatalogModal() {
    document.getElementById('modal-catalog').style.display = 'flex';
    searchCatalog();
}

async function searchCatalog() {
    const q = document.getElementById('catalog-search-input').value;
    const resp = await fetch(`/api/variables/catalog?q=${encodeURIComponent(q)}`);
    const results = await resp.json();
    const container = document.getElementById('catalog-results-list');
    container.innerHTML = '';

    results.slice(0, 50).forEach(v => {
        const div = document.createElement('div');
        div.className = 'card';
        div.style.padding = '10px';
        div.style.marginBottom = '8px';
        div.style.display = 'flex';
        div.style.justifyContent = 'space-between';
        div.style.alignItems = 'center';
        div.innerHTML = `
            <div>
                <div style="font-weight:bold; color:var(--text-main); font-size:13px;">${v.nome}</div>
                <div style="font-size:11px; color:var(--text-muted);">${v.descricao || 'Sem descrição'}</div>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="addFromCatalog('${v.nome.replace(/'/g, "\\'")}', '${(v.descricao||'').replace(/'/g, "\\'")}', ${v.tipo}, ${v.classificacao})">Adicionar</button>
        `;
        container.appendChild(div);
    });
}

function addFromCatalog(nome, desc, tipo, classif) {
    state.project.variaveis.push({
        id: Math.random().toString(36).substring(2, 10),
        nome: nome,
        descricao: desc,
        tipo: tipo,
        classificacao: classif,
        continua: 1,
        decimais: 2,
        habilitada: true,
        crescimento: 0,
        unitario: false,
        var_vinculada: -1
    });
    renderVariablesTable();
    renderDataTable();
    renderSubjectTable();
    showToast(`Variável "${nome}" adicionada!`);
}

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    showToast(`Importando ${file.name}...`);
    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/api/upload', { method: 'POST', body: formData });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail);
        }
        state.project = await resp.json();
        renderAll();
        showToast('Arquivo importado com sucesso!');
    } catch (err) {
        alert('Erro no upload: ' + err.message);
    }
    e.target.value = '';
}

function openModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.style.display = 'flex';
        if (window.lucide) lucide.createIcons();
    }
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
}

function openAboutModal() {
    const modal = document.getElementById('modal-about');
    if (modal) {
        modal.style.display = 'flex';
        if (window.lucide) lucide.createIcons();
    }
}

function showToast(msg) {
    const toast = document.createElement('div');
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.backgroundColor = '#0f172a';
    toast.style.color = '#ffffff';
    toast.style.padding = '10px 18px';
    toast.style.borderRadius = '8px';
    toast.style.fontSize = '13px';
    toast.style.fontWeight = '500';
    toast.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.2)';
    toast.style.zIndex = '9999';
    toast.style.transition = 'opacity 0.3s';
    toast.innerText = msg;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== EXPOSIÇÃO GLOBAL ====================
// Garante resolução de escopo para todos os manipuladores inline (onclick, onchange, etc.)
window.state = state;
window.safeStorage = safeStorage;
window.initTheme = initTheme;
window.toggleTheme = toggleTheme;
window.setupEventListeners = setupEventListeners;
window.downloadFile = downloadFile;
window.switchTab = switchTab;
window.loadProject = loadProject;
window.renderAll = renderAll;
window.renderProjectMetadata = renderProjectMetadata;
window.saveMetadata = saveMetadata;
window.renderVariablesTable = renderVariablesTable;
window.updateVarField = updateVarField;
window.saveVariables = saveVariables;
window.addCustomVariable = addCustomVariable;
window.deleteVariable = deleteVariable;
window.renderDataTable = renderDataTable;
window.toggleFilterActiveVars = toggleFilterActiveVars;
window.updateDataCell = updateDataCell;
window.toggleRowEnabled = toggleRowEnabled;
window.toggleRowOutlier = toggleRowOutlier;
window.addDataRow = addDataRow;
window.deleteDataRow = deleteDataRow;
window.saveData = saveData;
window.loadExploratoryData = loadExploratoryData;
window.renderExploratoryView = renderExploratoryView;
window.updateExploratoryX = updateExploratoryX;
window.updateExploratoryY = updateExploratoryY;
window.updateExploratoryCharts = updateExploratoryCharts;
window.updateExploratoryVariable = updateExploratoryX;
window.renderCorrelationHeatmap = renderCorrelationHeatmap;
window.calculateRegression = calculateRegression;
window.renderRegressionView = renderRegressionView;
window.selectModel = selectModel;
window.renderModelDetails = renderModelDetails;
window.trainRNA = trainRNA;
window.renderSubjectTable = renderSubjectTable;
window.addSubjectRow = addSubjectRow;
window.deleteSubjectRow = deleteSubjectRow;
window.toggleCalculationOptions = toggleCalculationOptions;
window.loadCalculationOptions = loadCalculationOptions;
window.saveCalculationOptions = saveCalculationOptions;
window.updateSubjectIdent = updateSubjectIdent;
window.updateSubjectCell = updateSubjectCell;
window.saveSubjects = saveSubjects;
window.renderLaudoPreview = renderLaudoPreview;
window.openReportCustomizer = openReportCustomizer;
window.saveReportCustomizer = saveReportCustomizer;
window.removeReportLogo = removeReportLogo;
window.handleReportLogoSelect = handleReportLogoSelect;
window.downloadReportPDF = downloadReportPDF;
window.printReport = printReport;
window.openSamplesModal = openSamplesModal;
window.openNewModelModal = openNewModelModal;
window.createNewModelFromModal = createNewModelFromModal;
window.openCatalogModal = openCatalogModal;
window.searchCatalog = searchCatalog;
window.addFromCatalog = addFromCatalog;
window.handleFileUpload = handleFileUpload;
window.openModal = openModal;
window.closeModal = closeModal;
window.openAboutModal = openAboutModal;
window.showToast = showToast;

// Global Error Catching
window.onerror = function (msg, url, lineNo, columnNo, error) {
    console.error('[OpenValora Error]', msg, 'at', url, ':', lineNo, ':', columnNo, error);
    return false;
};
window.addEventListener('unhandledrejection', function (event) {
    console.error('[OpenValora Unhandled Rejection]', event.reason);
});
