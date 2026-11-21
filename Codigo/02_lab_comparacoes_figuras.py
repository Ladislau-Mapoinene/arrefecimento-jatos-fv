"""02 — Comparações SP/CP a caudal igual e a potência de bombagem igual; ζ da placa; figuras.

Correr:  python codigo/02_lab_comparacoes_figuras.py   (depois do 01)
Lê:      resultados/tabelas/lab_indicadores.csv
Escreve: resultados/tabelas/lab_comparacoes.csv
         resultados/figuras/fig_theta_caudal_potencia.png
         resultados/figuras/fig_perfil_longitudinal.png

Métodos
 - Caudal igual: interpolação linear de θ em função de V̇ dentro da gama comum.
 - Potência de bombagem igual: interpolação de θ em função de log(V̇·ΔP).
 - ζ da placa: ΔP_CP − ΔP_SP·(V̇_CP/V̇_SP)² dividido por ½ρU_j²
   (válido porque P1 está no plenum antes da placa e P2 no topo, depois da placa).

PONTOS DE CONTROLO:
  a 246,8 m³/h: SP 18,86 K, CP ≈ 14,89 K  (diferença ≈ 3,97 K)
  potência hidráulica de CP para igualar θ do SP50 ........ ≈ 3,6 W (SP50: 0,93 W)
  ζ CP30 / CP40 / CP50 ..................................... ≈ 3,3 / 3,4 / 3,3
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C

r = pd.read_csv(C.TAB / "lab_indicadores.csv", index_col=0)
sp, cp = r.loc[["SP30", "SP40", "SP50"]], r.loc[["CP30", "CP40", "CP50"]]

# --- Comparações -----------------------------------------------------------
linhas = []
for V in (246.81, 282.07, 323.91, 355.63):
    tsp, tcp = np.interp(V, sp.caudal_m3h, sp.theta_final), np.interp(V, cp.caudal_m3h, cp.theta_final)
    linhas.append(dict(criterio="caudal igual", valor=V, unidade="m3/h",
                       theta_SP=tsp, theta_CP=tcp, diferenca=tsp - tcp))
th_alvo = sp.loc["SP50", "theta_final"]
p_cp = np.exp(np.interp(-th_alvo, -cp.theta_final, np.log(cp.P_hid_W)))
linhas.append(dict(criterio="potência para θ do SP50", valor=th_alvo, unidade="K",
                   theta_SP=sp.loc["SP50", "P_hid_W"], theta_CP=p_cp, diferenca=p_cp / sp.loc["SP50", "P_hid_W"]))
for c, s in (("CP30", "SP30"), ("CP40", "SP40"), ("CP50", "SP50")):
    dp_canal = r.loc[s, "dP_Pa"] * (r.loc[c, "caudal_m3h"] / r.loc[s, "caudal_m3h"]) ** 2
    zeta = (r.loc[c, "dP_Pa"] - dp_canal) / (0.5 * C.RHO_AR * r.loc[c, "Uj_ms"] ** 2)
    linhas.append(dict(criterio="zeta placa", valor=zeta, unidade="-", theta_SP=np.nan,
                       theta_CP=1 / np.sqrt(zeta), diferenca=np.nan))   # theta_CP guarda C_d
comp = pd.DataFrame(linhas)
print(comp.round(3).to_string())
comp.to_csv(C.TAB / "lab_comparacoes.csv", index=False)
for nome, d in (("SP", sp), ("CP", cp)):
    n = np.polyfit(np.log(d.caudal_m3h), np.log(d.dP_Pa), 1)[0]
    print(f"ΔP ∝ V̇^{n:.2f} ({nome})")

# --- Figuras ---------------------------------------------------------------
COR = {"SP": "#2a78d6", "CP": "#eb6834"}
ROT = {"SP": "Sem placa (SP)", "CP": "Com placa (CP)"}
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e6e6e3", "legend.frameon": False})
virgula = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
INC_THETA = 0.5   # K — repetibilidade estimada pela repetição do CP30 (script 02d)

fig, ax = plt.subplots(1, 2, figsize=(16 / 2.54, 6.5 / 2.54), constrained_layout=True)
for cfg, d in (("SP", sp), ("CP", cp)):
    for a, x in ((ax[0], d.caudal_m3h), (ax[1], d.P_hid_W)):
        a.errorbar(x, d.theta_final, yerr=INC_THETA, color=COR[cfg], lw=1.6, marker="o", ms=5,
                   mec="white", mew=1.5, capsize=3, label=ROT[cfg])
        for xi, yi, f in zip(x, d.theta_final, ("30", "40", "50")):
            a.annotate(f"{f} Hz", (xi, yi), textcoords="offset points", xytext=(5, 4), fontsize=7, color="#5c5c58")
ax[0].set(xlabel="Caudal volúmico, V̇ (m³/h)", ylabel="Excesso térmico, θ (K)", ylim=(10, 20.5))
ax[0].set_title("(a) Mesmo caudal", loc="left", fontsize=8)
ax[1].set(xscale="log", xlabel="Potência hidráulica, V̇·ΔP (W, escala log.)", ylim=(10, 20.5))
ax[1].set_xticks([0.2, 0.5, 1, 2, 5])
ax[1].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax[1].set_title("(b) Mesma potência de bombagem", loc="left", fontsize=8)
ax[1].legend(loc="upper right")
for a in ax:
    a.xaxis.set_major_formatter(virgula); a.yaxis.set_major_formatter(virgula)
fig.savefig(C.FIG / "fig_theta_caudal_potencia.png", dpi=300)

pos = [300, 1140, 1979]   # mm desde a entrada do ar (linhas 1, 2, 3)
plt.rcParams.update({"font.size": 8, "axes.labelsize": 8, "legend.fontsize": 7})
fig, ax = plt.subplots(1, 3, figsize=(16 / 2.54, 6 / 2.54), sharey=True, constrained_layout=True)
for i, f in enumerate(("30", "40", "50")):
    for cfg in ("SP", "CP"):
        q = r.loc[cfg + f]
        tin = q.Tm - q.theta_final
        y = np.array([q.linha1_entrada, q.linha2_meio, q.linha3_saida]) - tin
        ax[i].plot(pos, y, color=COR[cfg], lw=2, marker="o", ms=7, mec="white", mew=1.5, label=ROT[cfg])
    ax[i].set_title(f"{f} Hz", loc="left", fontsize=10)
    ax[i].set(xlabel="Distância à entrada (mm)", xticks=pos)
ax[0].set_ylabel("Média da linha − Tᵢₙ (K)")
ax[0].legend(loc="lower right")
fig.savefig(C.FIG / "fig_perfil_longitudinal.png", dpi=200)
print("Figuras gravadas em resultados/figuras/")
