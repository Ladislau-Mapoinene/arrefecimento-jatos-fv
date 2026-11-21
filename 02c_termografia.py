"""02c — Termografia da face frontal (secção 4.2.2).

Correr (Jupyter, pasta codigo):  %run 02c_termografia.py
Lê:      dados/brutos/termografia/SemPlaca e ComPlaca (imagens FLIR radiométricas)
Escreve: resultados/figuras/fig_4_9_termografia.png
         resultados/tabelas/termografia_imagens.csv  (hora e temperaturas de cada imagem)

Requisito: o programa ExifTool (gratuito, exiftool.org). No Windows, descarregar a versão
"Windows Executable", mudar o nome para exiftool.exe e colocá-lo na pasta codigo.

A figura usa as imagens originais da câmara, sem alterações. A extração de temperaturas
(tabela) serve apenas para verificar a correspondência imagem–ensaio.

Como se obtém a temperatura (tabela)
  Cada imagem FLIR guarda, além da imagem colorida, o sinal bruto do sensor (160 × 120 pontos)
  e as constantes de calibração da câmara (R1, R2, B, F, O). A temperatura de cada ponto é
  obtida pela lei de Planck invertida, corrigida pela emissividade (0,95, a definida na câmara)
  e pela temperatura refletida. As serpentinas metálicas das resistências têm emissividade mais
  baixa do que o vidro, pelo que a sua temperatura é subestimada: só o vidro dá leituras fiáveis.
"""
import io
import json
import shutil
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import config as C

EXIFTOOL = shutil.which("exiftool") or str(Path(__file__).resolve().parent / "exiftool.exe")


def temperatura(ficheiro):
    """Devolve a matriz de temperaturas (°C) e a hora da imagem."""
    campos = ["-PlanckR1", "-PlanckR2", "-PlanckB", "-PlanckF", "-PlanckO", "-Emissivity",
              "-ReflectedApparentTemperature", "-DateTimeOriginal"]
    m = json.loads(subprocess.run([EXIFTOOL, "-j", "-n", *campos, str(ficheiro)],
                                  capture_output=True, text=True).stdout)[0]
    bruto = subprocess.run([EXIFTOOL, "-b", "-RawThermalImage", str(ficheiro)], capture_output=True).stdout
    S = np.array(Image.open(io.BytesIO(bruto))).astype(float)
    R1, R2, B, F, O, e = (m[k] for k in ("PlanckR1", "PlanckR2", "PlanckB", "PlanckF", "PlanckO", "Emissivity"))
    S_refl = R1 / (R2 * (np.exp(B / (m["ReflectedApparentTemperature"] + 273.15)) - F)) - O
    S_obj = (S - (1 - e) * S_refl) / e
    with np.errstate(invalid="ignore"):
        T = B / np.log(R1 / (R2 * (S_obj + O)) + F) - 273.15
    return T, str(m["DateTimeOriginal"])[11:19]


def ficheiro(cfg, numero):
    return C.TERMO[cfg] / f"IR_{numero:04d}.jpg"


# ---------------------------------------------------------------- tabela de todas as imagens
linhas = []
for ensaio, (cfg, a, b) in C.TERMO_BLOCOS.items():
    for n in range(a, b + 1):
        f = ficheiro(cfg, n)
        if not f.exists():
            continue
        T, hora = temperatura(f)
        linhas.append(dict(imagem=f.name, ensaio=ensaio, hora=hora,
                           T_mediana=np.nanmedian(T), T_p95=np.nanpercentile(T, 95)))
tab = pd.DataFrame(linhas)
tab.to_csv(C.TAB / "termografia_imagens.csv", index=False)
print(tab.groupby("ensaio", sort=False)[["hora"]].agg(["first", "last", "count"]).to_string())

# ---------------------------------------------------------------- figura: imagens ORIGINAIS da câmara
# As imagens são colocadas tal como a câmara as gravou (escala, data e hora incluídas), sem
# qualquer alteração de cor ou de píxeis. Cada imagem tem a sua própria escala de temperatura,
# definida automaticamente pela câmara: as cores não são comparáveis entre imagens.
plt.rcParams.update({"font.size": 8})
fig, ax = plt.subplots(1, 2, figsize=(16 / 2.54, 6.2 / 2.54), constrained_layout=True)
for k, ensaio in enumerate(C.TERMO_FIGURA):
    img = Image.open(ficheiro(ensaio[:2], C.TERMO_VISTA_GERAL[ensaio]))
    ax[k].imshow(img, interpolation="none")
    ax[k].set_title(f"({'ab'[k]}) {ensaio}", loc="left", fontsize=8)
    ax[k].axis("off")
fig.savefig(C.FIG / "fig_4_9_termografia.png", dpi=300, bbox_inches="tight")
print("Gravado: fig_4_9_termografia.png")
