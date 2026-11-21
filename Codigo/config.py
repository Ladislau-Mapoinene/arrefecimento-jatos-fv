"""Configuração única do projeto.

Todos os scripts leem daqui os caminhos e as constantes. Cada constante indica
a sua origem:  [MEDIDO]  valor registado nos ensaios;
               [DERIVADO] calculado a partir de valores medidos;
               [FICHA]   ficha técnica do fabricante;
               [HIPÓTESE] pressuposto de modelação (a discutir no texto).
"""
from pathlib import Path
import math

# --------------------------------------------------------------------------
# Caminhos (relativos à pasta do projeto; não é preciso alterar nada)
# --------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"
PROC = RAIZ / "dados" / "processados"
FIG = RAIZ / "resultados" / "figuras"
TAB = RAIZ / "resultados" / "tabelas"
for p in (PROC, FIG, TAB):
    p.mkdir(parents=True, exist_ok=True)

LAB_XLSX = BRUTOS / "Analise_geral_16.10.xlsx"
ARDUINO_P1 = BRUTOS / "DATA10.CSV"          # período 1: médias de 60 amostras
ARDUINO_P2 = BRUTOS / "DATA25.CSV"          # período 2: 1 Hz, relógio RTC
VICTRON_XLSX = BRUTOS / "Ensaio10_Victron.xlsx"

# --------------------------------------------------------------------------
# Ensaios laboratoriais
# --------------------------------------------------------------------------
FOLHAS_LAB = ["SP00_30", "SP40", "SP50", "CP00_30", "CP40", "CP50"]
SUPERFICIE = ["T11", "T12", "T13", "T21", "T22", "T23", "T31", "T32", "T33"]
TODOS_TERMOPARES = ["Tin", "Tout", "Tamb"] + SUPERFICIE
DT_AMOSTRA = 1.0          # s  [MEDIDO] intervalo de amostragem do registo laboratorial
JANELA = 300              # amostras (= 5 min) para médias de regime
N_ISOTERMICO = 120        # amostras iniciais do SP00 usadas na calibração in situ

TENSAO_RESIST = 61.35     # V  [MEDIDO] tensão aos terminais do conjunto de resistências
R_EQ = 10.8               # Ω  [MEDIDO] resistência equivalente
P_EL = TENSAO_RESIST ** 2 / R_EQ   # W [DERIVADO] ≈ 349 W

# Caudal pelo anemómetro (média de 12 pontos), folha RESUMO  [MEDIDO]
CAUDAL_M3H = {"SP30": 246.81024, "SP40": 323.9136, "SP50": 408.56832,
              "CP30": 215.645976, "CP40": 282.069792, "CP50": 355.630968}
# Diferença de pressão P1 (plenum, entrada) – P2 (topo, após a placa): média e desvio-padrão  [MEDIDO]
DP_PA = {"SP30": (2.674, 0.204), "SP40": (5.000, 0.583), "SP50": (8.226, 0.808),
         "CP30": (21.580, 0.185), "CP40": (38.770, 0.589), "CP50": (60.269, 0.826)}
# Potência elétrica do ventilador (wattímetro de tomada a montante do variador)  [MEDIDO em SP e em CP; valores iguais]
P_VENT = {"30": 155.0, "40": 240.0, "50": 415.0}

# Geometria  [MEDIDO / projeto]
D_ORIF = 0.006            # m
N_ORIF = 666
A_LIVRE = N_ORIF * math.pi * D_ORIF ** 2 / 4     # m² [DERIVADO] ≈ 0,0188
A_MODULO = 2.583          # m² [FICHA] 2278 × 1134 mm
FOLGA_H = 0.0165          # m  distância placa–módulo [MEDIDO 12/11/2026: 16,5 mm]

# Propriedades do ar a ~25 °C  [HIPÓTESE: constantes]
RHO_AR, CP_AR, NU_AR, K_AR = 1.18, 1006.0, 1.56e-5, 0.0262

# --------------------------------------------------------------------------
# Monitorização exterior e módulo
# --------------------------------------------------------------------------
P_STC = 545.0             # W   [FICHA] JA Solar JAM72S30-545/MR
GAMMA_FICHA = -0.0035     # 1/K [FICHA] coeficiente de temperatura de Pmax
G_MIN = 200.0             # W/m² limiar de filtragem
LAT, LON = 41.4525, -8.2895
INCLINACAO = 39.0         # °  [MEDIDO]
AZIMUTE = 150.0           # °  (180 = sul; 150 = 30° para leste)  [DERIVADO dos dados, ver script 03]

# --------------------------------------------------------------------------
# Modelo térmico exterior e economia  [HIPÓTESES]
# --------------------------------------------------------------------------
U0_FAIMAN, U1_FAIMAN = 25.0, 6.84   # W/m²K, W/m³sK — valores por omissão da literatura
ETA_SISTEMA = 0.95                  # perdas do regulador/cablagem
ALBEDO = 0.2

# --------------------------------------------------------------------------
# Termografia (FLIR E30, ficheiros radiométricos)
# --------------------------------------------------------------------------
TERMO = {"SP": BRUTOS / "termografia" / "SemPlaca", "CP": BRUTOS / "termografia" / "ComPlaca"}
# Correspondência bloco de imagens → ensaio (pela hora e pelas pausas entre fotografias)
TERMO_BLOCOS = {
    "SP00": ("SP", 752, 759), "SP30": ("SP", 760, 769), "SP40": ("SP", 770, 791),
    "SP50_antes": ("SP", 792, 800), "SP50": ("SP", 801, 830),
    "CP30": ("CP", 831, 846), "CP40": ("CP", 847, 862), "CP50": ("CP", 863, 880),
}
# Imagem de vista geral escolhida para cada ensaio (enquadramento do módulo inteiro)
# Critério: módulo inteiro, enquadramento semelhante e cursor da câmara sobre o vidro, entre resistências
TERMO_VISTA_GERAL = {"SP30": 761, "SP40": 771, "SP50": 803,
                     "CP30": 831, "CP40": 847, "CP50": 867}
TERMO_FIGURA = ["SP30", "CP30"]   # imagens usadas na Figura 4.9


# --------------------------------------------------------------------------
# Tipo de letra das figuras: NewsGotT (o do texto da dissertação)
# --------------------------------------------------------------------------
def aplicar_fonte():
    """Regista o NewsGotT (se existir) e define-o como tipo de letra de todas as figuras.
    O DejaVu Sans serve de recurso para os caracteres que o NewsGotT não tem (letras gregas)."""
    import os, glob
    import matplotlib as mpl
    from matplotlib import font_manager as fm
    pastas = [RAIZ / "fontes", Path.home() / ".fonts", Path.home() / ".local/share/fonts",
              Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts", Path("C:/Windows/Fonts"),
              Path.home() / "Library/Fonts"]
    for pasta in pastas:
        for f in glob.glob(str(pasta / "NewsGot*.ttf")) + glob.glob(str(pasta / "newsgot*.ttf")):
            try:
                fm.fontManager.addfont(f)
            except Exception:
                pass
    mpl.rcParams["font.family"] = ["NewsGotT", "DejaVu Sans"]
    mpl.rcParams["font.sans-serif"] = ["NewsGotT", "DejaVu Sans"]
    mpl.rcParams["axes.unicode_minus"] = True
    # vírgula decimal nos eixos (português)
    import matplotlib.ticker as mt
    if not getattr(mt.ScalarFormatter, "_virgula", False):
        original = mt.ScalarFormatter.__call__
        mt.ScalarFormatter.__call__ = lambda self, x, pos=None: original(self, x, pos).replace(".", ",")
        mt.ScalarFormatter._virgula = True


try:
    aplicar_fonte()
except ImportError:
    pass
