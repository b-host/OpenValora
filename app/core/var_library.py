"""
OpenValora - Variable Library
Catálogo de variáveis padronizadas da ABNT NBR 14653 e modelos pré-configurados.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import Variable

def get_catalog_path() -> Path:
    candidates = []
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = Path(sys._MEIPASS)
        candidates.extend([
            base / "app" / "core" / "var_catalog.json",
            base / "var_catalog.json"
        ])
    here = Path(__file__).parent
    candidates.extend([
        here / "var_catalog.json",
        here.parent.parent / "var_catalog.json",
        Path.cwd() / "var_catalog.json"
    ])
    for p in candidates:
        if p.exists():
            return p
    return here / "var_catalog.json"

CATALOG_PATH = get_catalog_path()

def get_catalog() -> Dict[str, Any]:
    if CATALOG_PATH.exists():
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"Avaliação": [], "Tipologias": []}

def search_variables(query: str = "", area: str = "Avaliação", tipologia: Optional[int] = None) -> List[Dict[str, Any]]:
    cat = get_catalog()
    items = cat.get(area, [])
    results = []
    q = query.lower().strip()
    
    for item in items:
        if tipologia is not None and item.get("tipologia") != tipologia and item.get("tipologia") != 1:
            continue
        if not q or q in item.get("nome", "").lower() or q in item.get("descricao", "").lower():
            results.append(item)
    return results

def get_tipologias() -> List[Dict[str, Any]]:
    cat = get_catalog()
    return cat.get("Tipologias", [])

def get_default_variables_for_typology(typology_name: str = "Apartamentos") -> List[Variable]:
    """Retorna conjunto inicial recomendado de variáveis para uma dada tipologia."""
    tip = typology_name.lower()
    
    # Defaults para Apartamentos
    if "aparto" in tip or "apartamento" in tip:
        return [
            Variable(nome="Endereço", descricao="Logradouro e número", tipo=2, classificacao=8, continua=0, decimais=0, habilitada=True),
            Variable(nome="Bairro", descricao="Bairro de localização", tipo=2, classificacao=8, continua=0, decimais=0, habilitada=True),
            Variable(nome="Setor Urbano", descricao="Atratividade da localização (códigos alocados)", tipo=1, classificacao=2, continua=0, decimais=0, habilitada=True, crescimento=0),
            Variable(nome="Dormitórios", descricao="Quantidade de dormitórios", tipo=1, classificacao=1, continua=0, decimais=0, habilitada=True, crescimento=0),
            Variable(nome="Área Privativa", descricao="Área privativa em m²", tipo=1, classificacao=1, continua=1, decimais=2, habilitada=True, crescimento=1),
            Variable(nome="Padrão Construtivo", descricao="Padrão de acabamento (1=Baixo, 2=Normal, 3=Alto)", tipo=1, classificacao=2, continua=0, decimais=0, habilitada=True, crescimento=0),
            Variable(nome="Vagas Garagem", descricao="Número de vagas de garagem", tipo=1, classificacao=1, continua=0, decimais=0, habilitada=True, crescimento=0),
            Variable(nome="Valor Unitário", descricao="Valor em R$/m²", tipo=1, classificacao=7, continua=1, decimais=2, habilitada=True, unitario=True, var_vinculada=4)
        ]
    # Defaults para Casas
    elif "casa" in tip:
        return [
            Variable(nome="Endereço", descricao="Logradouro", tipo=2, classificacao=8, continua=0, decimais=0, habilitada=True),
            Variable(nome="Bairro", descricao="Bairro", tipo=2, classificacao=8, continua=0, decimais=0, habilitada=True),
            Variable(nome="Área Construída", descricao="Área construída em m²", tipo=1, classificacao=1, continua=1, decimais=2, habilitada=True, crescimento=1),
            Variable(nome="Área Terreno", descricao="Área do terreno em m²", tipo=1, classificacao=1, continua=1, decimais=2, habilitada=True, crescimento=0),
            Variable(nome="Idade Aparente", descricao="Idade aparente em anos", tipo=1, classificacao=1, continua=1, decimais=0, habilitada=True, crescimento=1),
            Variable(nome="Padrão Construtivo", descricao="Padrão construtivo (1=Baixo, 2=Normal, 3=Alto)", tipo=1, classificacao=2, continua=0, decimais=0, habilitada=True, crescimento=0),
            Variable(nome="Valor Unitário", descricao="Valor por m² de construção (R$/m²)", tipo=1, classificacao=7, continua=1, decimais=2, habilitada=True, unitario=True, var_vinculada=2)
        ]
    # Defaults para Terrenos / Lotes
    elif "lote" in tip or "terreno" in tip:
        return [
            Variable(nome="Identificação", descricao="Identificação do lote", tipo=2, classificacao=8, continua=0, decimais=0, habilitada=True),
            Variable(nome="Bairro", descricao="Bairro", tipo=2, classificacao=8, continua=0, decimais=0, habilitada=True),
            Variable(nome="Área do Terreno", descricao="Área total em m²", tipo=1, classificacao=1, continua=1, decimais=2, habilitada=True, crescimento=1),
            Variable(nome="Testada Principal", descricao="Frente para via pública em metros", tipo=1, classificacao=1, continua=1, decimais=2, habilitada=True, crescimento=0),
            Variable(nome="Topografia", descricao="1=Aclive/Declive acentuado, 2=Leve, 3=Plano", tipo=1, classificacao=2, continua=0, decimais=0, habilitada=True, crescimento=0),
            Variable(nome="Valor Unitário", descricao="Valor por m² (R$/m²)", tipo=1, classificacao=7, continua=1, decimais=2, habilitada=True, unitario=True, var_vinculada=2)
        ]
    # Padrão geral
    return [
        Variable(nome="Identificação", descricao="Identificação do dado", tipo=2, classificacao=8, continua=0, decimais=0, habilitada=True),
        Variable(nome="Área", descricao="Área principal em m²", tipo=1, classificacao=1, continua=1, decimais=2, habilitada=True, crescimento=1),
        Variable(nome="Padrão", descricao="Padrão construtivo ou qualidade", tipo=1, classificacao=2, continua=0, decimais=0, habilitada=True, crescimento=0),
        Variable(nome="Valor Unitário", descricao="Valor Unitário (R$/m²)", tipo=1, classificacao=7, continua=1, decimais=2, habilitada=True, unitario=True, var_vinculada=1)
    ]
