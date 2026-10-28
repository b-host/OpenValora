"""
OpenValora - Servidor Local Moderno
Aplicação FastAPI para Engenharia de Avaliações, Inferência Estatística e Redes Neurais.
"""

import os
import io
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .core.models import (
    Project, ProjectMetadata, Variable, SampleItem, SubjectProperty,
    CalculationOptions, RegressionModelResult
)
from .core.io_sda import (
    read_sda_file, write_sda_file, import_excel_or_csv, export_to_excel
)
from .core.regression import run_regression_search
from .core.neural_network import train_rna
from .core.var_library import (
    search_variables, get_tipologias, get_default_variables_for_typology
)
from .core.report_generator import generate_laudo_html
from .core.statistics import safe_float

# Paths compatíveis com execução normal e empacotamento PyInstaller/AppImage
import sys

def get_root_dir() -> Path:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent

ROOT_DIR = get_root_dir()
BASE_DIR = ROOT_DIR / "app"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

def get_sample_data_dir() -> Path:
    p1 = ROOT_DIR / "sample_data"
    if p1.exists():
        return p1
    p2 = Path(__file__).parent.parent / "sample_data"
    if p2.exists():
        return p2
    return p1

SAMPLE_DATA_DIR = get_sample_data_dir()

__version__ = "0.1.0"

app = FastAPI(
    title="OpenValora",
    description="Software aberto, moderno e leve para Engenharia de Avaliações, Inferência Estatística e Redes Neurais (ABNT NBR 14653)",
    version=__version__
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import FileResponse
    fav = STATIC_DIR / "favicon.png"
    if fav.exists():
        return FileResponse(fav, media_type="image/png")
    raise HTTPException(status_code=404)

# ==================== GERENCIAMENTO DO PROJETO (PERSISTÊNCIA & RETOMADA) ====================

def get_openvalora_user_dir() -> Path:
    """Retorna o diretório de configuração do usuário para salvar dados do OpenValora."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        d = Path(base) / "OpenValora"
    else:
        d = Path(os.path.expanduser("~")) / ".config" / "openvalora"
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_last_project_file() -> Path:
    """Caminho do arquivo de persistência do último projeto."""
    p_new = get_openvalora_user_dir() / "last_project.json"
    if p_new.exists():
        return p_new
    # Fallback para diretório legado se existir
    legacy = (Path(os.environ.get("APPDATA") or os.path.expanduser("~")) / "ValoraOpen" / "last_project.json") if sys.platform.startswith("win") else (Path(os.path.expanduser("~")) / ".config" / "valoraopen" / "last_project.json")
    if legacy.exists():
        return legacy
    return p_new

def create_new_project(typology: str = "Apartamentos") -> Project:
    """Cria um novo projeto limpo e vazio com a tipologia especificada."""
    from datetime import datetime
    proj = Project()
    proj.metadata.nome = f"Novo Modelo - {typology}" if typology != "Apartamentos" else "Novo Modelo OpenValora"
    proj.metadata.autor = "Nome do Responsável"
    proj.metadata.titulo_relatorio = "RELATÓRIO DE AVALIAÇÃO IMOBILIÁRIA"
    proj.metadata.subtitulo_relatorio = "Em conformidade com a ABNT NBR 14653-2 (Imóveis Urbanos)"
    proj.metadata.descricao = ""
    proj.metadata.data_criacao = datetime.now().strftime("%Y-%m-%d")
    proj.variaveis = get_default_variables_for_typology(typology)
    proj.dados = []
    proj.projecoes = [SubjectProperty(identificacao="Imóvel Avaliando 1")]
    proj.modelos_calculados = []
    proj.modelo_selecionado_idx = 0
    return proj

def persist_current_project():
    """Salva o projeto atual em disco para retomada automática na próxima inicialização."""
    try:
        f = get_last_project_file()
        f.write_text(CURRENT_PROJECT.model_dump_json(indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[OpenValora] Aviso ao persistir último projeto: {e}")

def init_app_project():
    """
    Inicializa o aplicativo:
    1. Tenta abrir o último projeto trabalhado.
    2. Se não houver projeto salvo para retomar, cria e abre um novo projeto limpo.
    """
    global CURRENT_PROJECT
    last_file = get_last_project_file()
    if last_file.exists():
        try:
            content = last_file.read_text(encoding="utf-8")
            CURRENT_PROJECT = Project.model_validate_json(content)
            print(f"[OpenValora] Retomando último projeto: '{CURRENT_PROJECT.metadata.nome}'")
            return
        except Exception as e:
            print(f"[OpenValora] Aviso ao ler último projeto ({e}). Criando um novo.")

    # Caso não haja projeto para retomar, inicia com um novo projeto limpo
    CURRENT_PROJECT = create_new_project("Apartamentos")
    print("[OpenValora] Nenhum projeto anterior para retomar. Iniciando com novo projeto.")

# Estado global da sessão em memória
CURRENT_PROJECT: Project = Project()
init_app_project()

# ==================== ROTAS DE INTERFACE ====================

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>OpenValora</h1><p>Arquivo index.html não encontrado.</p>"

@app.get("/report", response_class=HTMLResponse)
async def get_report(model_idx: Optional[int] = None, autoprint: Optional[bool] = False):
    global CURRENT_PROJECT
    model = None
    if CURRENT_PROJECT.modelos_calculados:
        idx = model_idx if model_idx is not None else CURRENT_PROJECT.modelo_selecionado_idx
        idx = max(0, min(idx, len(CURRENT_PROJECT.modelos_calculados) - 1))
        model = CURRENT_PROJECT.modelos_calculados[idx]
    
    html = generate_laudo_html(CURRENT_PROJECT, model, autoprint=bool(autoprint))
    return HTMLResponse(content=html)

# ==================== ROTAS DA API ====================

@app.get("/api/project")
async def get_project():
    global CURRENT_PROJECT
    return CURRENT_PROJECT.model_dump()

@app.post("/api/project/metadata")
async def update_metadata(metadata: ProjectMetadata):
    global CURRENT_PROJECT
    CURRENT_PROJECT.metadata = metadata
    persist_current_project()
    return {"status": "ok", "metadata": CURRENT_PROJECT.metadata.model_dump()}

@app.post("/api/project/new")
async def new_project(typology: str = Form("Apartamentos")):
    global CURRENT_PROJECT
    CURRENT_PROJECT = create_new_project(typology)
    persist_current_project()
    return CURRENT_PROJECT.model_dump()

@app.get("/api/samples")
async def list_samples():
    """Lista os projetos de exemplo .sda disponíveis no servidor."""
    if not SAMPLE_DATA_DIR.exists():
        return []
    
    samples = []
    for f in sorted(SAMPLE_DATA_DIR.glob("*.sda")):
        samples.append({
            "filename": f.name,
            "size_bytes": f.stat().st_size
        })
    return samples

@app.post("/api/samples/load")
async def load_sample(filename: str = Form(...)):
    global CURRENT_PROJECT
    target = SAMPLE_DATA_DIR / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="Arquivo de exemplo não encontrado.")
    
    CURRENT_PROJECT = read_sda_file(target)
    # Tenta calcular regressão automaticamente
    try:
        models = run_regression_search(CURRENT_PROJECT)
        CURRENT_PROJECT.modelos_calculados = models
        CURRENT_PROJECT.modelo_selecionado_idx = 0
    except Exception as e:
        CURRENT_PROJECT.modelos_calculados = []
        CURRENT_PROJECT.modelo_selecionado_idx = 0
        
    persist_current_project()
    return CURRENT_PROJECT.model_dump()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    global CURRENT_PROJECT
    content = await file.read()
    fn = file.filename.lower()

    if fn.endswith((".valora", ".json")):
        try:
            CURRENT_PROJECT = Project.model_validate_json(content.decode("utf-8"))
            persist_current_project()
            return CURRENT_PROJECT.model_dump()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo de projeto aberto (.valora): {str(e)}")

    elif fn.endswith(".sda"):
        try:
            CURRENT_PROJECT = read_sda_file(content)
            try:
                models = run_regression_search(CURRENT_PROJECT)
                CURRENT_PROJECT.modelos_calculados = models
                CURRENT_PROJECT.modelo_selecionado_idx = 0
            except Exception:
                CURRENT_PROJECT.modelos_calculados = []
            persist_current_project()
            return CURRENT_PROJECT.model_dump()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo legado .sda: {str(e)}")
            
    elif fn.endswith((".xlsx", ".xls", ".csv")):
        try:
            vars_list, samples = import_excel_or_csv(content, file.filename)
            CURRENT_PROJECT = Project()
            CURRENT_PROJECT.metadata.nome = Path(file.filename).stem
            CURRENT_PROJECT.variaveis = vars_list
            CURRENT_PROJECT.dados = samples
            CURRENT_PROJECT.projecoes = [SubjectProperty(identificacao="Imóvel Avaliando")]
            persist_current_project()
            return CURRENT_PROJECT.model_dump()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao importar planilha: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Formato não suportado. Envie .valora, .sda, .xlsx, .xls ou .csv.")

@app.get("/api/export/valora")
async def export_valora():
    """Exporta o projeto no formato aberto nativo .valora (formato open source padrão do OpenValora)."""
    global CURRENT_PROJECT
    import unicodedata
    data = CURRENT_PROJECT.model_dump_json(indent=2).encode("utf-8")
    raw_name = CURRENT_PROJECT.metadata.nome.replace(" ", "_")
    safe_name = unicodedata.normalize('NFKD', raw_name).encode('ascii', 'ignore').decode('ascii') or "modelo"
    return Response(
        content=data,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.valora"'}
    )

@app.get("/api/export/sda")
async def export_sda():
    global CURRENT_PROJECT
    import unicodedata
    data = write_sda_file(CURRENT_PROJECT)
    raw_name = CURRENT_PROJECT.metadata.nome.replace(" ", "_")
    safe_name = unicodedata.normalize('NFKD', raw_name).encode('ascii', 'ignore').decode('ascii') or "modelo"
    return Response(
        content=data,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.sda"'}
    )

@app.get("/api/export/xlsx")
async def export_xlsx():
    global CURRENT_PROJECT
    import unicodedata
    data = export_to_excel(CURRENT_PROJECT)
    raw_name = CURRENT_PROJECT.metadata.nome.replace(" ", "_")
    safe_name = unicodedata.normalize('NFKD', raw_name).encode('ascii', 'ignore').decode('ascii') or "modelo"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.xlsx"'}
    )

@app.post("/api/variables")
async def update_variables(variables: List[Variable]):
    global CURRENT_PROJECT
    CURRENT_PROJECT.variaveis = variables
    # Limpa modelos anteriores caso as variáveis tenham mudado
    CURRENT_PROJECT.modelos_calculados = []
    persist_current_project()
    return {"status": "ok", "variaveis": [v.model_dump() for v in CURRENT_PROJECT.variaveis]}

@app.get("/api/variables/catalog")
async def get_var_catalog(q: str = "", area: str = "Avaliação", tipologia: Optional[int] = None):
    return search_variables(query=q, area=area, tipologia=tipologia)

@app.get("/api/variables/tipologias")
async def list_tipologias():
    return get_tipologias()

@app.post("/api/data")
async def update_data(dados: List[SampleItem]):
    global CURRENT_PROJECT
    CURRENT_PROJECT.dados = dados
    CURRENT_PROJECT.modelos_calculados = []
    persist_current_project()
    return {"status": "ok", "count": len(CURRENT_PROJECT.dados)}

@app.post("/api/subjects")
async def update_subjects(subjects: List[SubjectProperty]):
    global CURRENT_PROJECT
    CURRENT_PROJECT.projecoes = subjects
    # Se houver modelos calculados, reavalia
    if CURRENT_PROJECT.modelos_calculados:
        try:
            models = run_regression_search(CURRENT_PROJECT)
            CURRENT_PROJECT.modelos_calculados = models
        except Exception:
            pass
    persist_current_project()
    return {
        "status": "ok",
        "count": len(CURRENT_PROJECT.projecoes),
        "modelos": [m.model_dump() for m in CURRENT_PROJECT.modelos_calculados]
    }

@app.post("/api/options")
async def update_options(options: CalculationOptions):
    global CURRENT_PROJECT
    CURRENT_PROJECT.opcoes = options
    persist_current_project()
    return {"status": "ok", "opcoes": CURRENT_PROJECT.opcoes.model_dump()}

@app.post("/api/calculate")
async def calculate_regression():
    global CURRENT_PROJECT
    amostra_valida = [d for d in CURRENT_PROJECT.dados if d.habilitado]
    if len(amostra_valida) < 4:
        raise HTTPException(
            status_code=400,
            detail="A amostra precisa conter no mínimo 4 observações habilitadas para calcular a regressão."
        )
    try:
        models = run_regression_search(CURRENT_PROJECT)
        CURRENT_PROJECT.modelos_calculados = models
        CURRENT_PROJECT.modelo_selecionado_idx = 0
        persist_current_project()
        return {
            "status": "ok",
            "count": len(models),
            "modelos": [m.model_dump() for m in models]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/calculate/select_model")
async def select_model(idx: int = Form(...)):
    global CURRENT_PROJECT
    if 0 <= idx < len(CURRENT_PROJECT.modelos_calculados):
        CURRENT_PROJECT.modelo_selecionado_idx = idx
        persist_current_project()
        return {"status": "ok", "selected_idx": idx}
    raise HTTPException(status_code=400, detail="Índice de modelo inválido.")

@app.post("/api/rna/train")
async def train_rna(
    hidden_neurons: int = Form(8),
    activation: str = Form("logistic"),
    max_iter: int = Form(1500),
    learning_rate: float = Form(0.01),
    solver: str = Form("lbfgs"),
    bagging: bool = Form(False)
):
    global CURRENT_PROJECT
    try:
        res = train_rna(
            project=CURRENT_PROJECT,
            hidden_layer_sizes=(hidden_neurons,),
            activation=activation,
            max_iter=max_iter,
            learning_rate_init=learning_rate,
            solver=solver,
            bagging=bagging
        )
        CURRENT_PROJECT.rna_resultado = res
        CURRENT_PROJECT.rna_config = {
            "hidden_neurons": hidden_neurons,
            "activation": activation,
            "max_iter": max_iter,
            "learning_rate": learning_rate,
            "solver": solver,
            "bagging": bagging
        }
        persist_current_project()
        return {"status": "ok", "resultado": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/exploratory")
async def get_exploratory_data():
    """Calcula estatísticas descritivas, histogramas e correlações da amostra."""
    global CURRENT_PROJECT
    import numpy as np

    amostra = [item for item in CURRENT_PROJECT.dados if item.habilitado]
    if not amostra:
        return {"stats": {}, "correlations": {}, "variables": [], "sample_ids": []}

    sample_ids = [item.id for item in amostra]
    num_vars = [v for v in CURRENT_PROJECT.variaveis if v.tipo == 1 and v.habilitada]
    stats_data = {}
    matrix_data = []

    for v in num_vars:
        vals = np.array([safe_float(item.valores.get(v.nome, 0.0)) for item in amostra], dtype=float)
        n = len(vals)
        mean_val = float(np.mean(vals))
        median_val = float(np.median(vals))
        std_val = float(np.std(vals, ddof=1)) if n > 1 else 0.0
        cv_val = float((std_val / mean_val * 100.0) if mean_val != 0 else 0.0)
        min_val = float(np.min(vals))
        max_val = float(np.max(vals))

        # Histograma (10 bins)
        hist, bin_edges = np.histogram(vals, bins=min(10, max(4, n // 2)))
        hist_bins = []
        for i in range(len(hist)):
            hist_bins.append({
                "from": round(float(bin_edges[i]), 2),
                "to": round(float(bin_edges[i+1]), 2),
                "label": f"{bin_edges[i]:.1f} - {bin_edges[i+1]:.1f}",
                "count": int(hist[i])
            })

        stats_data[v.nome] = {
            "n": n,
            "media": round(mean_val, 2),
            "mediana": round(median_val, 2),
            "desvio_padrao": round(std_val, 2),
            "cv_pct": round(cv_val, 2),
            "minimo": round(min_val, 2),
            "maximo": round(max_val, 2),
            "histogram": hist_bins,
            "raw_values": [round(float(x), 2) for x in vals],
            "sample_ids": sample_ids
        }
        matrix_data.append(vals)

    # Matriz de correlação linear de Pearson
    correlations = {}
    if matrix_data:
        arr = np.array(matrix_data)
        if arr.shape[0] > 1:
            corr_mat = np.corrcoef(arr)
            for i, v1 in enumerate(num_vars):
                correlations[v1.nome] = {}
                for j, v2 in enumerate(num_vars):
                    val = float(corr_mat[i, j])
                    correlations[v1.nome][v2.nome] = 0.0 if np.isnan(val) else round(val, 4)
        else:
            correlations[num_vars[0].nome] = {num_vars[0].nome: 1.0}

    return {
        "variables": [v.nome for v in num_vars],
        "stats": stats_data,
        "correlations": correlations,
        "sample_ids": sample_ids
    }
