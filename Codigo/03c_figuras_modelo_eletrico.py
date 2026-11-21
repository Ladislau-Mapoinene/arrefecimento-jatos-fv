"""03c — Figuras da secção 4.1.3 (modelo de potência elétrica).

Correr (Jupyter, pasta codigo):  %run 03c_figuras_modelo_eletrico.py
Escreve em resultados/figuras/:
  fig_4_4_potencia_temperatura_vs_G.png  (a) P vs G, cor = T ; (b) T vs G
  fig_4_5_gamma_por_faixa.png            γ estimado em 4 faixas de irradiância vs ficha técnica
  fig_4_6_sensor_24h.png                 leitura do sensor ao longo de 24 h (desvio de zero noturno)

Raciocínio que as figuras sustentam
  1. A potência cresce com G (efeito dominante) e T também cresce com G, porque o módulo
     aquece com a radiação absorvida: as duas variáveis andam juntas (r ≈ 0,80).
  2. Para separar o efeito da temperatura, fixa-se G em faixas estreitas e estima-se γ em cada
     uma. O valor varia de +0,44 a −0,23 %/°C conforme a faixa: um coeficiente físico não pode
     depender da irradiância, logo há um erro sistemático nas medições.
  3. A origem provável é o sensor de irradiância: regista ~100 W/m² durante a noite, quando a
     irradiância real é nula (desvio de zero). Um desvio fixo pesa mais quando G é baixo
     (100 W/m² são 20 % de 500 W/m², mas 12 % de 800 W/m²), o que distorce mais as faixas baixas.
Inserir no Word sem redimensionar (largura = 16 cm).
"""
import importlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import config as C

ext = importlib.import_module("03_exterior_sincronizacao_modelo")
L = 16 / 2.54
sns.set_theme(style="whitegrid", context="paper")
C.aplicar_fonte()
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "legend.fontsize": 8})
AZUL, LARANJA, CINZA = "#2a78d6", "#eb6834", "#5c5c58"


def guardar(fig, nome):
    fig.savefig(C.FIG / nome, dpi=200, bbox_inches="tight")
    print("Gravado:", nome)


def letra(ax, l):
    ax.text(0.99, 0.95, f"({l})", transform=ax.transAxes, fontsize=10, fontweight="bold", va="top", ha="right")


# ------------------------------------------------ dados sincronizados e filtrados (Bulk, G ≥ 200)
v, a = ext.ler_victron(), ext.ler_arduino_p1()
a, _ = ext.corrigir_relogio(a, ext.defasagens_diarias(a, v))
s = ext.juntar(a, v, "t_real")
r_GT = np.corrcoef(s["G"], s["T"])[0, 1]
print(f"Registos: {len(s)}; correlação G–T = {r_GT:.2f}")

# ------------------------------------------------ Figura 4.4: P vs G e T vs G
fig, ax = plt.subplots(2, 1, figsize=(L, 12 / 2.54), constrained_layout=True)
sc = ax[0].scatter(s["G"], s["P"], c=s["T"], cmap="viridis", s=3, alpha=0.6, rasterized=True)
cb = fig.colorbar(sc, ax=ax[0], pad=0.01)
cb.set_label("T do módulo (°C)")
ax[0].set(xlabel="Irradiância, G (W/m²)", ylabel="Potência, P (W)")
ax[1].scatter(s["G"], s["T"], color=AZUL, s=3, alpha=0.3, rasterized=True)
ax[1].set(xlabel="Irradiância, G (W/m²)", ylabel="Temperatura do módulo, T (°C)")
ax[1].text(0.02, 0.92, f"r = {r_GT:.2f}".replace(".", ","), transform=ax[1].transAxes, fontsize=9)
letra(ax[0], "a"); letra(ax[1], "b")
guardar(fig, "fig_4_4_potencia_temperatura_vs_G.png")

# ------------------------------------------------ Figura 4.5: γ estimado em faixas de irradiância fixa
# Em cada faixa estreita de G, o efeito da irradiância fica praticamente fixo e a variação de
# P/G (potência por unidade de irradiância) com T deve dar o coeficiente γ. Usa-se a reta de
# Theil–Sen (robusta a pontos isolados) e um intervalo de confiança por reamostragem de dias.
from scipy.stats import theilslopes
FAIXAS = [(450, 550), (550, 650), (650, 750), (750, 850)]
rng = np.random.default_rng(1)


def gamma_faixa(d):
    y = d["P"] / d["G"]
    b = theilslopes(y, d["T"])[0]
    return 100 * b / (np.median(y) - b * (np.median(d["T"]) - 25))


res = []
for lo, hi in FAIXAS:
    f = s[(s["G"] >= lo) & (s["G"] < hi)]
    dias = f["dia"].unique()
    boot = [gamma_faixa(pd.concat([f[f["dia"] == x] for x in rng.choice(dias, len(dias))])) for _ in range(300)]
    res.append(dict(faixa=f"{lo}–{hi}", n=len(f), gamma=gamma_faixa(f),
                    ic_inf=np.percentile(boot, 2.5), ic_sup=np.percentile(boot, 97.5)))
res = pd.DataFrame(res)
res.to_csv(C.TAB / "gamma_por_faixa.csv", index=False)
print(res.round(2).to_string())

fig, ax = plt.subplots(figsize=(L, 6.5 / 2.54), constrained_layout=True)
x = np.arange(len(res))
ax.errorbar(x, res["gamma"], yerr=[res["gamma"] - res["ic_inf"], res["ic_sup"] - res["gamma"]],
            fmt="o", color=AZUL, ms=7, mec="white", mew=1.5, capsize=4, lw=1.5, label="Estimado a partir dos dados (IC 95 %)")
ax.axhline(C.GAMMA_FICHA * 100, color=LARANJA, ls="--", lw=1.5, label="Ficha técnica (−0,35 %/°C)")
ax.axhline(0, color=CINZA, lw=0.8)
ax.set_xticks(x, [f"{r}\n(n = {n})" for r, n in zip(res["faixa"], res["n"])])
ax.set(xlabel="Faixa de irradiância (W/m²)", ylabel="Coeficiente de temperatura, γ (%/°C)")
ax.legend(frameon=False, loc="upper right")
ax.set_ylim(-0.55, 1.15)
guardar(fig, "fig_4_5_gamma_por_faixa.png")

# ------------------------------------------------ Figura 4.6: leitura do sensor ao longo de 24 h (período 2, RTC)
# À noite a irradiância real é nula; o valor registado nesse período é o desvio de zero do sensor.
DIA = "2026-07-18"
e = pd.read_csv(C.ARDUINO_P2, sep=";", usecols=[0, 5])
e.columns = ["ts", "G"]
serie = e.assign(t=pd.to_datetime(e["ts"], unit="s")).set_index("t")["G"].resample("1min").mean()
noturno = serie[(serie.index.hour >= 23) | (serie.index.hour < 4)]          # 23h–04h, todas as noites
med_noite = noturno.median()
g = serie.loc[DIA]
fig, ax = plt.subplots(figsize=(L, 7 / 2.54), constrained_layout=True)
ax.plot(g.index, g.rolling(5, center=True).median(), color=AZUL, lw=1.2, label="Irradiância registada pelo sensor")
ax.axhline(0, color=CINZA, ls="--", lw=1.2, label="Irradiância real durante a noite (0 W/m²)")
ax.set(xlabel=f"Hora ({pd.Timestamp(DIA):%d/%m/%Y})", ylabel="Irradiância no plano (W/m²)")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.legend(frameon=False, loc="upper left")
guardar(fig, "fig_4_6_sensor_24h.png")
print(f"Leitura noturna (23h–04h), mediana de todo o período 2: {med_noite:.0f} W/m² "
      f"(percentil 95: {noturno.quantile(0.95):.0f} W/m²)")
