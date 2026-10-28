"""
OpenValora - Data Models
Representação de projetos, variáveis, dados amostrais, opções de cálculo e laudos.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
import datetime

class Variable(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    nome: str
    descricao: str = ""
    tipo: int = 1  # 1: Numérica, 2: Texto, 3: Data, 4: Moeda, 5: Porcentagem
    crescimento: int = 0  # 0: Crescente (direta), 1: Decrescente (inversa), -1: Livre
    classificacao: int = 1  # 1: Quantitativa, 2: Qualitativa (Códigos Alocados), 3: Proxy, 4: Dicotômica, 7: Variável Dependente, 8: Texto geral
    continua: int = 1  # 1: Contínua, 0: Discreta
    decimais: int = 2
    habilitada: bool = True
    unitario: bool = False  # True para Valor Unitário (R$/m²)
    var_vinculada: int = -1  # Índice da variável de área correspondente (-1 se nenhuma)
    largura_coluna: float = 120.0
    transformacao_rl: int = 0  # 0 = todas permitidas

class SampleItem(BaseModel):
    id: int
    habilitado: bool = True
    outlier: bool = False
    valores: Dict[str, Any] = Field(default_factory=dict)

class SubjectProperty(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    identificacao: str = "Imóvel Avaliando"
    valores: Dict[str, Any] = Field(default_factory=dict)

class ProjectMetadata(BaseModel):
    nome: str = "Novo Modelo OpenValora"
    autor: str = "Nome do Responsável"
    data_criacao: str = Field(default_factory=lambda: datetime.date.today().strftime("%d/%m/%Y"))
    area_conhecimento: int = 1  # 1: Avaliação de Bens, 2: Economia, 3: Engenharia, 4: Medicina
    tipologia: int = 1  # 1: Apartamentos, 2: Casas, etc.
    descricao: str = ""
    senha: str = ""
    tipo_senha: int = 0  # 0: Sem senha, 1: Somente leitura, 2: Acesso completo
    # Campos de personalização do Relatório (NBR 14653)
    titulo_relatorio: str = "RELATÓRIO DE AVALIAÇÃO IMOBILIÁRIA"
    subtitulo_relatorio: str = "Em conformidade com a ABNT NBR 14653-2 (Imóveis Urbanos)"
    solicitante: str = ""
    finalidade: str = "Determinação de Valor de Mercado"
    registro_profissional: str = ""
    endereco_imovel: str = ""
    observacoes: str = ""
    logo_base64: str = ""
    incluir_tabela_dados: bool = True
    # Informações cadastrais e institucionais da Empresa / Profissional (Rodapé e Cabeçalho)
    empresa_nome: str = ""
    empresa_cnpj: str = ""
    empresa_crea: str = ""
    empresa_telefone: str = ""
    empresa_email: str = ""
    empresa_site: str = ""
    empresa_endereco: str = ""
    qualificacao_profissional: str = "Engenheiro Avaliador"
    ibape_registro: str = ""

class CalculationOptions(BaseModel):
    metodo: str = "todas"  # "todas" ou "simplificado"
    selecao_modelo: str = "estimativa"  # "estimativa" ou "regressao"
    estimador: str = "mq"  # "mq" (Mínimos Quadrados) ou "mv" (Máxima Verossimilhança)
    transformacoes: List[str] = ["x", "1/x", "ln(x)"]  # "x", "1/x", "ln(x)", "x2", "1/x2", "x(1/2)", "1/x(1/2)"
    nivel_confianca: float = 0.80  # 80% conforme NBR 14653
    campo_arbitrio_pct: float = 15.0  # 15% conforme NBR 14653
    arredondamento_pct: float = 1.0  # 1% conforme NBR 14653
    limite_modelos: int = 100

class RegressorResult(BaseModel):
    nome_original: str
    nome_exibicao: str
    transformacao_codigo: str  # "x", "1/x", "ln(x)", etc.
    expressao: str
    coeficiente: float
    erro_padrao: float
    t_calc: float
    p_valor: float
    significancia_pct: float
    elasticidade_media: float
    crescimento_esperado: int
    sinal_invertido: bool = False
    vif: float = 1.0

class AnovaTable(BaseModel):
    ss_reg: float
    ss_res: float
    ss_tot: float
    df_reg: int
    df_res: int
    df_tot: int
    ms_reg: float
    ms_res: float
    f_calc: float
    p_valor_f: float
    significancia_f_pct: float

class ResidualItem(BaseModel):
    index: int
    observado: float
    estimado: float
    residuo_ordinario: float
    residuo_padronizado: float
    residuo_studentizado: float
    residuo_relativo_pct: float
    distancia_cook: float
    leverage: float
    is_outlier: bool
    is_influente: bool

class NormalityResult(BaseModel):
    dentro_1_dp_pct: float
    dentro_2_dp_pct: float
    dentro_3_dp_pct: float
    referencia: List[float] = [68.0, 95.0, 99.0]
    ks_stat: float
    ks_pvalor: float
    shapiro_stat: Optional[float] = None
    shapiro_pvalor: Optional[float] = None
    atende_normalidade: bool

class NBRGradingItem(BaseModel):
    item: str
    descricao: str
    grau_obtido: str  # "III", "II", "I", ou "NÃO ENQUADRADO"
    justificativa: str
    grau_pontos: int = 0

class NBRClassification(BaseModel):
    grau_fundamentacao: str  # "Grau III", "Grau II", "Grau I", "Não Enquadrado"
    grau_precisao: str       # "Grau III", "Grau II", "Grau I", "Não Enquadrado"
    amplitude_ic_pct: float
    requisitos_fundamentacao: List[NBRGradingItem]
    requisitos_precisao: List[NBRGradingItem]
    resumo_analitico: str
    diagnosticos_ajuste: List[str] = Field(default_factory=list)
    norma_aplicada: str = "ABNT NBR 14653-2 (Imóveis Urbanos)"

class ValuationResult(BaseModel):
    sujeito_id: str
    identificacao: str
    valor_estimado_unitario: float
    valor_total_estimado: Optional[float] = None
    area_vinculada_valor: Optional[float] = None
    ic_inferior: float
    ic_superior: float
    amplitude_ic_pct: float
    campo_arbitrio_min: float
    campo_arbitrio_max: float
    valor_arredondado: float
    grau_precisao: str
    grau_fundamentacao: str

class RegressionModelResult(BaseModel):
    id: int
    equacao_texto: str
    transformacao_dep: str
    var_dep_nome: str
    regressores: List[RegressorResult]
    intercepto: float
    r: float
    r2: float
    r2_ajustado: float
    r2_original: float
    r_original: float
    erro_padrao: float
    erro_padrao_original: float
    durbin_watson: float
    durbin_watson_status: str
    anova: AnovaTable
    residuos: List[ResidualItem]
    normalidade: NormalityResult
    breusch_pagan_pvalor: Optional[float] = None
    homocedastico: bool = True
    inversao_detectada: bool = False
    nbr: Optional[NBRClassification] = None
    projecoes: List[ValuationResult] = Field(default_factory=list)
    diagnosticos_tecnicos: List[str] = Field(default_factory=list)

class Project(BaseModel):
    metadata: ProjectMetadata = Field(default_factory=ProjectMetadata)
    variaveis: List[Variable] = Field(default_factory=list)
    dados: List[SampleItem] = Field(default_factory=list)
    projecoes: List[SubjectProperty] = Field(default_factory=list)
    opcoes: CalculationOptions = Field(default_factory=CalculationOptions)
    modelos_calculados: List[RegressionModelResult] = Field(default_factory=list)
    modelo_selecionado_idx: int = 0
    rna_config: Dict[str, Any] = Field(default_factory=dict)
    rna_resultado: Dict[str, Any] = Field(default_factory=dict)
