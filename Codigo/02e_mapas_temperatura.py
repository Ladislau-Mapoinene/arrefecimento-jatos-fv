"""02e — Mapas do excesso térmico nos nove termopares (secção 4.2.2).

Correr (Jupyter, pasta codigo, depois do 01):  %run 02e_mapas_temperatura.py
Lê:      dados/processados/lab_series.pkl
Escreve: resultados/figuras/fig_4_7b_mapas_theta.png
         resultados/tabelas/lab_mapas_theta.csv      (θ de cada termopar, últimos 300 s)
         resultados/tabelas/lab_mapas_reducao.csv    (redução local de θ face ao ensaio sem ventilação)

Cada célula é um termopar, desenhado na sua posição na grelha 3 × 3 (linha 1 = junto à entrada do ar).
Não há interpolação entre pontos: só se mostra o que foi medido.
θ_i = T_i − T_in, com os termopares corrigidos pela calibração in situ (script 01).
Todos os mapas usam a mesma escala de cor, para poderem ser comparados.
CONFIRMAR: posição física das colunas 1, 2, 3 (de que lado fica a coluna 1, visto de trás do módulo).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import config as C

S = pd.read_pickle(C.PROC / "lab_series.pkl")
DIST = [300, 1140, 1979]           # mm desde a entrada do ar


def mapa(bloco):
    return bloco[C.SUPERFICIE].sub(bloco["Tin"], axis=0).mean().values.reshape(3, 3)


mapas = {}
for cfg in ("SP", "CP"):
    d = S[cfg + "00_30"]
    mapas[cfg + "00"] = mapa(d[d["t_s"] < 0].iloc[-C.JANELA:])
    for f, folha in (("30", cfg + "00_30"), ("40", cfg + "40"), ("50", cfg + "50")):
        mapas[cfg + f] = mapa(S[folha].iloc[-C.JANELA:])

# tabelas
linhas, red = [], []
for k, m in mapas.items():
    linhas.append(dict(ensaio=k, **{t: v for t, v in zip(C.SUPERFICIE, m.ravel())},
                       desvio_padrao=m.std(), amplitude_transversal=(m.max(1) - m.min(1)).mean(),
                       media_coluna1=m[:, 0].mean(), media_coluna2=m[:, 1].mean(), media_coluna3=m[:, 2].mean()))
    if not k.endswith("00"):
        r = 100 * (mapas[k[:2] + "00"] - m) / mapas[k[:2] + "00"]
        red.append(dict(ensaio=k, **{t: v for t, v in zip(C.SUPERFICIE, r.ravel())},
                        minimo=r.min(), maximo=r.max(), desvio_padrao=r.std()))
tab = pd.DataFrame(linhas).set_index("ensaio"); tab.to_csv(C.TAB / "lab_mapas_theta.csv")
tred = pd.DataFrame(red).set_index("ensaio"); tred.to_csv(C.TAB / "lab_mapas_reducao.csv")
pd.set_option("display.width", 200)
print(tab.round(1).to_string()); print(); print(tred.round(0).to_string())

# figura
plt.rcParams.update({"font.size": 8})
fig, ax = plt.subplots(2, 4, figsize=(16 / 2.54, 9.5 / 2.54), constrained_layout=True)
vmin, vmax = 8, 32
for i, cfg in enumerate(("SP", "CP")):
    for j, f in enumerate(("00", "30", "40", "50")):
        a, m = ax[i, j], mapas[cfg + f]
        im = a.imshow(m, origin="lower", cmap="YlOrRd", vmin=vmin, vmax=vmax, aspect="auto")
        for (r, c), v in np.ndenumerate(m):
            a.text(c, r, f"{v:.1f}".replace(".", ","), ha="center", va="center", fontsize=7,
                   color="white" if v > 24 else "#1f1f1d")
        a.set_xticks([0, 1, 2], ["C1", "C2", "C3"])
        a.set_yticks([0, 1, 2], [str(x) for x in DIST] if j == 0 else ["", "", ""])
        a.set_title(f"{cfg}{f}", fontsize=8, loc="left")
        a.tick_params(length=0)
        for s in a.spines.values():
            s.set_visible(False)
    ax[i, 0].set_ylabel("Distância à entrada (mm)")
cb = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
cb.set_label("Excesso térmico local, Tᵢ − Tᵢₙ (K)")
fig.savefig(C.FIG / "fig_4_7b_mapas_theta.png", dpi=300, bbox_inches="tight")
print("Gravado: fig_4_7b_mapas_theta.png")
