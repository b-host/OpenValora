/**
 * OpenValora - Chart Visualizations Engine
 * Renderização de gráficos estatísticos com Chart.js
 */

const chartInstances = {};

function applyChartTheme() {
    if (!window.Chart) return;
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    Chart.defaults.color = isDark ? '#94a3b8' : '#64748b';
    Chart.defaults.borderColor = isDark ? '#334155' : '#e2e8f0';
    if (Chart.defaults.plugins && Chart.defaults.plugins.legend) {
        Chart.defaults.plugins.legend.labels.color = isDark ? '#f8fafc' : '#0f172a';
    }
}
applyChartTheme();

function destroyChart(id) {
    if (chartInstances[id]) {
        chartInstances[id].destroy();
        delete chartInstances[id];
    }
}

/**
 * 1. Gráfico de Aderência: Valores Observados vs Estimados
 */
function renderAderenciaChart(canvasId, residuosData) {
    destroyChart(canvasId);
    applyChartTheme();
    const canvas = document.getElementById(canvasId);
    if (!canvas || !residuosData || residuosData.length === 0) return;

    const points = residuosData.map(r => ({ x: r.estimado, y: r.observado, id: r.index, rel: r.residuo_relativo_pct }));
    const allVals = residuosData.map(r => r.observado).concat(residuosData.map(r => r.estimado));
    const minVal = Math.min(...allVals) * 0.9;
    const maxVal = Math.max(...allVals) * 1.1;

    const linePoints = [
        { x: minVal, y: minVal },
        { x: maxVal, y: maxVal }
    ];

    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Linha Ideal (45°)',
                    data: linePoints,
                    type: 'line',
                    borderColor: '#f59e0b',
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 0,
                    tension: 0
                },
                {
                    label: 'Dados Amostrais (Estimado x Observado)',
                    data: points,
                    backgroundColor: '#0284c7',
                    borderColor: '#0369a1',
                    pointRadius: 6,
                    pointHoverRadius: 8
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onHover: (event, elements) => {
                if (event.native && event.native.target) {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                }
            },
            onClick: (event, elements, chart) => {
                if (!elements || elements.length === 0) return;
                const el = elements[0];
                const dataset = chart.data.datasets[el.datasetIndex];
                const pt = dataset?.data?.[el.index];
                if (pt && pt.id && typeof window.navigateToDataRow === 'function') {
                    window.navigateToDataRow(pt.id);
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Valor Estimado (R$/m² ou R$)', font: { weight: 'bold' } },
                    min: minVal,
                    max: maxVal
                },
                y: {
                    title: { display: true, text: 'Preço Observado (R$/m² ou R$)', font: { weight: 'bold' } },
                    min: minVal,
                    max: maxVal
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const p = ctx.raw;
                            if (p.id) {
                                return `Dado #${p.id} | Est: ${p.x.toFixed(2)} | Obs: ${p.y.toFixed(2)} | Resíduo: ${p.rel.toFixed(1)}% (Clique para selecionar na tabela)`;
                            }
                            return '';
                        }
                    }
                }
            }
        }
    });
}

/**
 * 2. Gráfico de Resíduos vs Estimados (Homocedasticidade)
 */
function renderResiduosChart(canvasId, residuosData, se) {
    destroyChart(canvasId);
    applyChartTheme();
    const canvas = document.getElementById(canvasId);
    if (!canvas || !residuosData || residuosData.length === 0) return;

    const points = residuosData.map(r => ({ x: r.estimado, y: r.residuo_padronizado, id: r.index }));
    const estVals = residuosData.map(r => r.estimado);
    const minX = Math.min(...estVals) * 0.9;
    const maxX = Math.max(...estVals) * 1.1;

    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Resíduo Padronizado',
                    data: points,
                    backgroundColor: function(ctx) {
                        const val = ctx.raw?.y;
                        return (Math.abs(val) > 2) ? '#ef4444' : '#0284c7';
                    },
                    pointRadius: 6,
                    pointHoverRadius: 8
                },
                {
                    label: '+2 Desvios Padrão',
                    data: [{ x: minX, y: 2 }, { x: maxX, y: 2 }],
                    type: 'line',
                    borderColor: '#ef4444',
                    borderDash: [5, 5],
                    pointRadius: 0
                },
                {
                    label: 'Linha Zero',
                    data: [{ x: minX, y: 0 }, { x: maxX, y: 0 }],
                    type: 'line',
                    borderColor: '#94a3b8',
                    pointRadius: 0
                },
                {
                    label: '-2 Desvios Padrão',
                    data: [{ x: minX, y: -2 }, { x: maxX, y: -2 }],
                    type: 'line',
                    borderColor: '#ef4444',
                    borderDash: [5, 5],
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onHover: (event, elements) => {
                if (event.native && event.native.target) {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                }
            },
            onClick: (event, elements, chart) => {
                if (!elements || elements.length === 0) return;
                const el = elements[0];
                const dataset = chart.data.datasets[el.datasetIndex];
                const pt = dataset?.data?.[el.index];
                if (pt && pt.id && typeof window.navigateToDataRow === 'function') {
                    window.navigateToDataRow(pt.id);
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Valor Estimado', font: { weight: 'bold' } },
                    min: minX, max: maxX
                },
                y: {
                    title: { display: true, text: 'Resíduo Padronizado (e / s)', font: { weight: 'bold' } },
                    suggestedMin: -3, suggestedMax: 3
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const p = ctx.raw;
                            if (p && p.id) {
                                return `Dado #${p.id} | Est: ${p.x.toFixed(2)} | Res. Padronizado: ${p.y.toFixed(2)} (Clique para selecionar na tabela)`;
                            }
                            return ctx.dataset.label || '';
                        }
                    }
                }
            }
        }
    });
}

/**
 * 3. Gráfico de Distância de Cook (Identificação de Pontos Influenciantes)
 */
function renderCookChart(canvasId, residuosData) {
    destroyChart(canvasId);
    applyChartTheme();
    const canvas = document.getElementById(canvasId);
    if (!canvas || !residuosData || residuosData.length === 0) return;

    const labels = residuosData.map(r => `#${r.index}`);
    const values = residuosData.map(r => r.distancia_cook);

    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Distância de Cook',
                    data: values,
                    backgroundColor: values.map(v => v > 1.0 ? '#ef4444' : (v > 0.5 ? '#f59e0b' : '#38bdf8')),
                    borderColor: '#0284c7',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onHover: (event, elements) => {
                if (event.native && event.native.target) {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                }
            },
            onClick: (event, elements, chart) => {
                if (!elements || elements.length === 0) return;
                const el = elements[0];
                const label = chart.data.labels[el.index];
                if (label) {
                    const rowId = parseInt(label.replace('#', ''));
                    if (rowId && typeof window.navigateToDataRow === 'function') {
                        window.navigateToDataRow(rowId);
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Elemento Amostral' } },
                y: { title: { display: true, text: 'Distância de Cook (Di)' }, suggestedMax: 1.2 }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        afterLabel: function() {
                            return 'Clique para selecionar na tabela de dados';
                        }
                    }
                }
            }
        }
    });
}

/**
 * 4. Histograma dos Resíduos e Curva Normal
 */
function renderNormalidadeChart(canvasId, residuosData) {
    destroyChart(canvasId);
    applyChartTheme();
    const canvas = document.getElementById(canvasId);
    if (!canvas || !residuosData || residuosData.length === 0) return;

    const stdRes = residuosData.map(r => r.residuo_padronizado);
    const bins = [-3, -2, -1, 0, 1, 2, 3];
    const counts = [0, 0, 0, 0, 0, 0];
    const labels = ['<-2', '-2 a -1', '-1 a 0', '0 a 1', '1 a 2', '>2'];

    stdRes.forEach(r => {
        if (r < -2) counts[0]++;
        else if (r < -1) counts[1]++;
        else if (r < 0) counts[2]++;
        else if (r < 1) counts[3]++;
        else if (r < 2) counts[4]++;
        else counts[5]++;
    });

    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Frequência de Resíduos Padronizados',
                    data: counts,
                    backgroundColor: '#818cf8',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Frequência de Dados' } }
            }
        }
    });
}

/**
 * 5. Gráfico de Dispersão Exploratório
 */
function renderExploratoryScatter(canvasId, xVals, yVals, xName, yName, sampleIds) {
    destroyChart(canvasId);
    applyChartTheme();
    const canvas = document.getElementById(canvasId);
    if (!canvas || !xVals || !yVals) return;

    const points = xVals.map((x, i) => ({
        x: x,
        y: yVals[i],
        id: (sampleIds && sampleIds[i]) ? sampleIds[i] : (i + 1)
    }));
    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: `${yName} vs ${xName}`,
                data: points,
                backgroundColor: '#0284c7',
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onHover: (event, elements) => {
                if (event.native && event.native.target) {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                }
            },
            onClick: (event, elements, chart) => {
                if (!elements || elements.length === 0) return;
                const el = elements[0];
                const dataset = chart.data.datasets[el.datasetIndex];
                const pt = dataset?.data?.[el.index];
                if (pt && pt.id && typeof window.navigateToDataRow === 'function') {
                    window.navigateToDataRow(pt.id);
                }
            },
            scales: {
                x: { title: { display: true, text: xName } },
                y: { title: { display: true, text: yName } }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const p = ctx.raw;
                            return `Dado #${p.id} | ${xName}: ${p.x} | ${yName}: ${p.y} (Clique para selecionar na tabela)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 6. Histograma Exploratório
 */
function renderExploratoryHist(canvasId, bins, varName) {
    destroyChart(canvasId);
    applyChartTheme();
    const canvas = document.getElementById(canvasId);
    if (!canvas || !bins) return;

    const labels = bins.map(b => b.label);
    const counts = bins.map(b => b.count);

    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `Histograma de ${varName}`,
                data: counts,
                backgroundColor: '#3b82f6',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

/**
 * 7. Gráfico de Convergência da RNA (Loss Curve)
 */
function renderRnaLossChart(canvasId, lossCurve) {
    destroyChart(canvasId);
    applyChartTheme();
    const canvas = document.getElementById(canvasId);
    if (!canvas || !lossCurve || lossCurve.length === 0) return;

    const labels = lossCurve.map((_, i) => `${i + 1}`);

    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Erro de Treinamento (Loss)',
                data: lossCurve,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Épocas / Iterações' } },
                y: { title: { display: true, text: 'Perda (MSE)' } }
            }
        }
    });
}

/**
 * 8. Gráfico da Função Estimativa (Curva de Regressão por Variável)
 */
function renderCurvaEstimativaChart(canvasId, varName, depVarName, samplePoints, curvePoints, isInverted) {
    destroyChart(canvasId);
    applyChartTheme();
    const canvas = document.getElementById(canvasId);
    if (!canvas || !curvePoints) return;

    const curveColor = isInverted ? '#ef4444' : '#10b981';
    const curveLabel = isInverted ? `Curva Estimativa: ${depVarName} vs ${varName} (Inversão de Sinal)` : `Curva Estimativa: ${depVarName} vs ${varName}`;

    const datasets = [
        {
            label: curveLabel,
            data: curvePoints,
            type: 'line',
            borderColor: curveColor,
            borderWidth: 2.5,
            fill: false,
            pointRadius: 0,
            tension: 0.2
        }
    ];

    if (samplePoints && samplePoints.length > 0) {
        datasets.push({
            label: `Dados Amostrais (${varName} x ${depVarName})`,
            data: samplePoints,
            type: 'scatter',
            backgroundColor: '#0284c7',
            borderColor: '#0369a1',
            pointRadius: 5,
            pointHoverRadius: 8
        });
    }

    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'scatter',
        data: { datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            onHover: (event, elements) => {
                if (event.native && event.native.target) {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                }
            },
            onClick: (event, elements, chart) => {
                if (!elements || elements.length === 0) return;
                const el = elements[0];
                const dataset = chart.data.datasets[el.datasetIndex];
                const pt = dataset?.data?.[el.index];
                if (pt && pt.id && typeof window.navigateToDataRow === 'function') {
                    window.navigateToDataRow(pt.id);
                }
            },
            scales: {
                x: { title: { display: true, text: varName, font: { weight: 'bold' } } },
                y: { title: { display: true, text: depVarName, font: { weight: 'bold' } } }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const p = ctx.raw;
                            if (p && p.id) {
                                return `Dado #${p.id} | ${varName}: ${p.x.toFixed(2)} | ${depVarName}: ${p.y.toFixed(2)} (Clique para selecionar)`;
                            }
                            if (p && p.x !== undefined && p.y !== undefined) {
                                return `Estimativa: ${p.y.toFixed(2)} (${varName} = ${p.x.toFixed(2)})`;
                            }
                            return '';
                        }
                    }
                }
            }
        }
    });
}

// Exposição global das funções de gráficos
window.applyChartTheme = applyChartTheme;
window.destroyChart = destroyChart;
window.renderAderenciaChart = renderAderenciaChart;
window.renderResiduosChart = renderResiduosChart;
window.renderCookChart = renderCookChart;
window.renderNormalidadeChart = renderNormalidadeChart;
window.renderExploratoryHist = renderExploratoryHist;
window.renderExploratoryScatter = renderExploratoryScatter;
window.renderRnaLossChart = renderRnaLossChart;
window.renderCurvaEstimativaChart = renderCurvaEstimativaChart;
