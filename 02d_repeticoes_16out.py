"""02d — Repetições CP30 e CP40 de 16 de outubro: comparação com os ensaios originais.

Correr (Jupyter, pasta codigo, depois do 01):  %run 02d_repeticoes_16out.py
Lê:      dados/brutos/repeticao_16out/CP30_rep.xls e CP40_rep.xls (texto, separado por tabulações)
         dados/processados/lab_series.pkl, resultados/tabelas/lab_indicadores.csv,
         resultados/tabelas/desvios_termopares.csv
Escreve: resultados/figuras/fig_4_6_evolucao_com_repeticoes.png
         resultados/tabelas/lab_repeticoes.csv

Ficheiros sem cabeçalho: 14 colunas = tempo (s) + 13 canais. Identificação dos canais:
  col 1  = T_out   (desce quando o ventilador arranca)
  col 11 = T_amb   (não reage ao arranque)
  col 12 = T_in    (sobe ≈0,5 K com o ventilador, como nos ensaios originais: aquecimento pelo motor)
  col 5  = canal sem termopar (≈2294 °C, circuito aberto)
  cols 2, 3, 4, 6, 7, 8, 9, 10, 13 = os nove termopares da superfície.
A ordem destes nove não está documentada. A média T̄m não depende da ordem, por isso o excesso
térmico θ = T̄m − T_in é calculado sem ambiguidade. A calibração in situ aplica-se assim:
  T̄m: subtrai-se a média dos nove desvios (≈0,01 K, também independente da ordem);
  T_in: subtrai-se o desvio do T_in (−0,38 K).
Os perfis por linha NÃO são calculados com estes ficheiros, porque exigiriam conhecer a ordem.
"""
import importlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import config as C

L = importlib.import_module("01_lab_reanalise")
PASTA = C.BRUTOS / "repeticao_16out"
REP = {"CP30": PASTA / "CP30_rep.xls", "CP40": PASTA / "CP40_rep.xls"}
SUP = [2, 3, 4, 6, 7, 8, 9, 10, 13]
COL_TIN = 12

desv = pd.read_csv(C.TAB / "desvios_termopares.csv", index_col=0)["desvio_K"]
r = pd.read_csv(C.TAB / "lab_indicadores.csv", index_col=0)
S = pd.read_pickle(C.PROC / "lab_series.pkl")

rep, linhas = {}, []
for ensaio, f in REP.items():
    d = pd.read_csv(f, sep="\t", header=None)
    Tm = d[SUP].mean(axis=1) - desv[C.SUPERFICIE].mean()
    Tin = d[COL_TIN] - desv["Tin"]
    theta = Tm - Tin
    i0 = L.indice_arranque(Tm.values)
    rep[ensaio] = pd.DataFrame({"t_s": (np.arange(len(d)) - i0) * C.DT_AMOSTRA, "theta": theta})
    fim = slice(len(d) - C.JANELA, len(d))
    linhas.append(dict(
        ensaio=ensaio,
        duracao_vent_min=(len(d) - i0) * C.DT_AMOSTRA / 60,
        theta_antes_rep=theta.iloc[max(0, i0 - C.JANELA):i0].mean() if i0 > 60 else np.nan,
        theta_final_rep=theta.iloc[fim].mean(),
        declive_final_rep=L.declive(Tm.iloc[fim].values),
        theta_final_orig=r.loc[ensaio, "theta_final"],
        declive_final_orig=r.loc[ensaio, "declive_final"],
        duracao_orig_min=r.loc[ensaio, "duracao_vent_s"] / 60,
        **{f"theta_{t}s_rep": theta.iloc[i0 + t - 5:i0 + t + 5].mean() for t in (60, 120, 300, 480)},
    ))
    # mesmos instantes no ensaio original
    o = S["CP00_30" if ensaio == "CP30" else ensaio]
    j0 = int((o["t_s"] < 0).sum())
    for t in (60, 120, 300, 480):
        linhas[-1][f"theta_{t}s_orig"] = o["theta"].iloc[j0 + t - 5:j0 + t + 5].mean()

tab = pd.DataFrame(linhas).set_index("ensaio")
tab.to_csv(C.TAB / "lab_repeticoes.csv")
pd.set_option("display.width", 200)
print(tab.round(2).T.to_string())

# ---------------------------------------------------------------- figura (formato da Figura 4.6)
sns.set_theme(style="whitegrid", context="paper")
C.aplicar_fonte()
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "legend.fontsize": 7.5})
COR = {"30": "#2a78d6", "40": "#1baa7a", "50": "#eb6834"}
FOLHA = {"SP": {"30": "SP00_30", "40": "SP40", "50": "SP50"},
         "CP": {"30": "CP00_30", "40": "CP40", "50": "CP50"}}
NOME = {"SP": "Sem placa perfurada (SP)", "CP": "Com placa perfurada (CP)"}

fig, ax = plt.subplots(2, 1, figsize=(16 / 2.54, 12 / 2.54), sharex=True, sharey=True, constrained_layout=True)
for a, cfg in zip(ax, ("SP", "CP")):
    for f, folha in FOLHA[cfg].items():
        d = S[folha]; d = d[d["t_s"] >= -600]
        a.plot(d["t_s"] / 60, d["theta"].rolling(15, center=True).mean(), color=COR[f], lw=1.4, label=f"{f} Hz")
        if cfg == "CP" and "CP" + f in rep:
            e = rep["CP" + f]; e = e[e["t_s"] >= -600]
            a.plot(e["t_s"] / 60, e["theta"].rolling(15, center=True).mean(), color=COR[f], lw=1.4, ls="--",
                   label=f"{f} Hz (repetição)")
    th0 = r.loc[cfg + "00", "theta_final"]
    a.axhline(th0, color="#5c5c58", ls=":", lw=1)
    a.text(31.5, th0 + 0.6, f"sem ventilação: {th0:.1f} K".replace(".", ","), ha="right", fontsize=8, color="#5c5c58")
    a.axvline(0, color="#5c5c58", lw=0.8)
    a.set_title(NOME[cfg], loc="left", fontsize=9)
    a.set_ylabel("Excesso térmico, θ (K)")
    a.legend(frameon=False, loc="center right", ncol=1)
ax[1].set_xlabel("Tempo desde o arranque do ventilador (min)")
ax[1].set_xlim(-10, 32)
fig.savefig(C.FIG / "fig_4_6_evolucao_com_repeticoes.png", dpi=200, bbox_inches="tight")
print("Gravado: fig_4_6_evolucao_com_repeticoes.png")
