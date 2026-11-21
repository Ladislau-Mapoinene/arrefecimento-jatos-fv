"""02b — Evolução temporal do excesso térmico nos ensaios laboratoriais (Figura da secção 4.2.1).

Correr (Jupyter, pasta codigo, depois do 01):  %run 02b_figura_evolucao_temporal.py
Lê:      dados/processados/lab_series.pkl, resultados/tabelas/lab_indicadores.csv
Escreve: resultados/figuras/fig_4_7_evolucao_temporal.png
         resultados/tabelas/lab_tabela_4_2.csv

O eixo horizontal é o tempo desde o arranque do ventilador (t = 0). A linha a tracejado
indica o excesso térmico em regime estacionário sem ventilação (SP00 ou CP00).
Inserir no Word sem redimensionar (largura = 16 cm).
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import config as C

S = pd.read_pickle(C.PROC / "lab_series.pkl")
r = pd.read_csv(C.TAB / "lab_indicadores.csv", index_col=0)

sns.set_theme(style="whitegrid", context="paper")
C.aplicar_fonte()
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "legend.fontsize": 8})
COR = {"30": "#2a78d6", "40": "#1baa7a", "50": "#eb6834"}
FOLHA = {"SP": {"30": "SP00_30", "40": "SP40", "50": "SP50"},
         "CP": {"30": "CP00_30", "40": "CP40", "50": "CP50"}}
NOME = {"SP": "Sem placa perfurada (SP)", "CP": "Com placa perfurada (CP)"}

fig, ax = plt.subplots(2, 1, figsize=(16 / 2.54, 12 / 2.54), sharex=True, sharey=True, constrained_layout=True)
for a, cfg in zip(ax, ("SP", "CP")):
    for f, folha in FOLHA[cfg].items():
        d = S[folha]
        d = d[(d["t_s"] >= -600)]
        a.plot(d["t_s"] / 60, d["theta"].rolling(15, center=True).mean(), color=COR[f], lw=1.4, label=f"{f} Hz")
    th0 = r.loc[cfg + "00", "theta_final"]
    a.axhline(th0, color="#5c5c58", ls="--", lw=1)
    a.text(31.5, th0 + 0.6, f"sem ventilação: {th0:.1f} K".replace(".", ","), ha="right", fontsize=8, color="#5c5c58")
    a.axvline(0, color="#5c5c58", lw=0.8)
    a.set_title(NOME[cfg], loc="left", fontsize=9)
    a.set_ylabel("Excesso térmico, θ (K)")
ax[1].set_xlabel("Tempo desde o arranque do ventilador (min)")
ax[0].legend(frameon=False, loc="center right", title="Frequência")
ax[1].set_xlim(-10, 32)
fig.savefig(C.FIG / "fig_4_7_evolucao_temporal.png", dpi=200, bbox_inches="tight")
print("Gravado: fig_4_7_evolucao_temporal.png")

# Tabela de apoio ao texto: excesso final, declive final e redução face ao ensaio sem ventilação
linhas = []
for cfg in ("SP", "CP"):
    th0 = r.loc[cfg + "00", "theta_final"]
    for f in ("30", "40", "50"):
        q = r.loc[cfg + f]
        linhas.append(dict(ensaio=cfg + f, caudal_m3h=q.caudal_m3h, duracao_min=q.duracao_vent_s / 60,
                           theta_final_K=q.theta_final, declive_final_C_min=q.declive_final,
                           reducao_pct=100 * (th0 - q.theta_final) / th0))
t = pd.DataFrame(linhas).set_index("ensaio")
t.to_csv(C.TAB / "lab_tabela_4_2.csv")
print(t.round(2).to_string())
