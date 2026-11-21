"""Figura 2.7: coerência entre a redução de temperatura e o ganho elétrico reportados (estudos da Tabela 2.1).

Ganho explicável apenas pela temperatura, com o modelo linear P = P_ref[1 + γ(T − 25)]:
    G = |γ|·ΔT / (1 − |γ|·(T0 − 25)),   T0 = temperatura do módulo sem arrefecimento.
Limite inferior: |γ| = 0,35 %/°C e T0 → 25 °C  ->  G = 0,35·ΔT
Limite superior: |γ| = 0,50 %/°C e T0 = 85 °C  ->  G = 0,50·ΔT / 0,70 ≈ 0,71·ΔT
"""
import importlib, os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ESTUDOS = importlib.import_module("08_sintese_tecnicas").ESTUDOS
for f in ("/root/.fonts/NewsGotT-Regular.ttf", "/root/.fonts/NewsGotT-Bold.ttf"):
    if os.path.exists(f):
        fm.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["NewsGotT", "DejaVu Sans"], "font.size": 9, "axes.edgecolor": "#333333", "axes.linewidth": 0.6,
                     "xtick.color": "#333333", "ytick.color": "#333333"})
PRETO, CINZA, BANDA = "#1a1a1a", "#8c8c8c", "#e3e3e3"
G_INF, G_SUP = 0.35, 0.50 / 0.70

fig, ax = plt.subplots(figsize=(16 / 2.54, 9.5 / 2.54))
x = np.linspace(0, 50, 50)
ax.fill_between(x, G_INF * x, G_SUP * x, color=BANDA, lw=0, zorder=0)
ax.plot(x, G_INF * x, color=CINZA, lw=0.8); ax.plot(x, G_SUP * x, color=CINZA, lw=0.8)
ax.text(46, G_SUP * 46 + 1.0, "|γ| = 0,50 %/°C; T₀ = 85 °C", rotation=0, ha="right", va="bottom", fontsize=7.5, color="#555555")
ax.text(49, 12.2, "|γ| = 0,35 %/°C; T₀ = 25 °C", ha="right", va="top", fontsize=7.5, color="#555555")

for n_, g, tec, est, met, dt, ge, *_ in ESTUDOS:
    if dt is None or ge is None or est == "Gama típica":
        continue
    num = met == "Num."
    cor = "white" if num else PRETO
    if isinstance(dt, tuple) and isinstance(ge, tuple):
        ax.add_patch(plt.Rectangle((dt[0], ge[0]), dt[1] - dt[0], ge[1] - ge[0], fill=False, ec=PRETO, lw=0.9,
                                   ls="-" if not num else (0, (3, 2)), zorder=2))
        ax.text(dt[1] + 0.6, ge[1], str(n_), fontsize=7, color="#444444", va="center")
        continue
    xs = dt if isinstance(dt, tuple) else (dt,)
    ys = ge if isinstance(ge, tuple) else (ge,)
    if len(ys) > 1:
        ax.plot([xs[0]] * 2, ys, color=PRETO, lw=1.1, zorder=2)
    for yy in ys:
        ax.plot(xs[0], yy, marker="o", ms=4.5, mfc=cor, mec=PRETO, mew=0.9, zorder=3)
    ax.text(xs[0] + 0.7, max(ys), str(n_), fontsize=7, color="#444444", va="center")

ax.set_xlim(0, 50); ax.set_ylim(0, 55)
ax.set_xlabel("Redução de temperatura do módulo, ΔT (°C)")
ax.set_ylabel("Ganho elétrico relativo reportado (%)")
ax.grid(color="#ececec", lw=0.6); ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
leg = [Patch(color=BANDA, label="Ganho explicável pela redução de temperatura"),
       Line2D([0], [0], ls="", marker="o", ms=5, mfc=PRETO, mec=PRETO, label="Experimental ou não indicado"),
       Line2D([0], [0], ls="", marker="o", ms=5, mfc="white", mec=PRETO, label="Numérico"),
       Patch(fill=False, ec=PRETO, label="Gamas de um estudo (tracejado: numérico)")]
ax.legend(handles=leg, loc="upper left", frameon=False, fontsize=7.5)
fig.tight_layout()
fig.savefig("../resultados/figuras/fig_2_coerencia_ganho.png", dpi=300, facecolor="white",
            bbox_inches="tight", pad_inches=0.04)
# relatório: posição de cada estudo face à banda
for n_, g, tec, est, met, dt, ge, *_ in ESTUDOS:
    if dt is None or ge is None or est == "Gama típica":
        continue
    a = dt if isinstance(dt, tuple) else (dt, dt); b = ge if isinstance(ge, tuple) else (ge, ge)
    print(n_, est, "inf", round(G_INF * a[0], 1), "sup", round(G_SUP * a[1], 1), "reportado", b)
