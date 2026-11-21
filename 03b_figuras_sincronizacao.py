"""03b — Figuras que mostram, passo a passo, como se sincronizaram o Arduino e o Victron.

Correr (no Jupyter, dentro da pasta codigo):  %run 03b_figuras_sincronizacao.py
Lê:      dados/brutos/DATA10.CSV, dados/brutos/Ensaio10_Victron.xlsx
Escreve: resultados/figuras/sinc_1_curvas_desencontradas.png
         resultados/figuras/sinc_2_procura_deslocamento.png
         resultados/figuras/sinc_3_curvas_sincronizadas.png
         resultados/figuras/sinc_4_defasagem_diaria.png

Ideia
  Os dois sistemas medem a potência do mesmo módulo, por isso as duas curvas diárias têm
  a mesma forma. Se os relógios estiverem desacertados, uma aparece deslocada da outra.
  Desloca-se a curva do Victron minuto a minuto e mede-se a sobreposição (correlação).
  O deslocamento com maior correlação é a defasagem desse dia.

As curvas são normalizadas pelo máximo diário (0 a 1) porque só interessa comparar a forma:
os dois sistemas não medem exatamente o mesmo valor absoluto.
"""
import importlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import config as C

ext = importlib.import_module("03_exterior_sincronizacao_modelo")   # reutiliza a leitura dos ficheiros

DIA = "2026-06-20"          # dia de exemplo (céu limpo, defasagem elevada)
DESLOC = range(-30, 181)    # deslocamentos testados (min)

sns.set_theme(style="whitegrid", context="paper", font_scale=1.25)
C.aplicar_fonte()
COR_ARD, COR_VIC = "#2a78d6", "#eb6834"
hora = mdates.DateFormatter("%H:%M")


def normalizar(s):
    return s / s.max()


def guardar(fig, nome):
    fig.savefig(C.FIG / nome, dpi=200, bbox_inches="tight")
    print("Gravado:", nome)


# ---------------------------------------------------------------- leitura
v = ext.ler_victron()
a = ext.ler_arduino_p1().set_index("t")
ard = normalizar(a.loc[DIA, "Pa"].clip(lower=0))
vic = v["P"]

# ---------------------------------------------------------------- 1. curvas tal como foram registadas
fig, ax = plt.subplots(figsize=(7, 3.6))
ax.plot(ard.index, ard, color=COR_ARD, lw=1.6, label="Arduino (V × I)")
ax.plot(vic.loc[DIA].index, normalizar(vic.loc[DIA]), color=COR_VIC, lw=1.6, label="Victron")
ax.set(xlabel=f"Hora registada ({pd.Timestamp(DIA):%d/%m/%Y})", ylabel="Potência normalizada (–)",
       title="Curvas de potência tal como foram registadas")
ax.xaxis.set_major_formatter(hora)
ax.legend(frameon=False, loc="upper left")
guardar(fig, "sinc_1_curvas_desencontradas.png")

# ---------------------------------------------------------------- 2. procura do melhor deslocamento
corr = []
for d in DESLOC:
    deslocada = vic.shift(freq=pd.Timedelta(minutes=d)).rename("vic")
    j = ard.to_frame("ard").join(deslocada, how="inner").dropna()
    corr.append(j["ard"].corr(j["vic"]))
corr = pd.Series(corr, index=list(DESLOC))
melhor = int(corr.idxmax())

fig, ax = plt.subplots(figsize=(7, 3.6))
ax.plot(corr.index, corr.values, color="#5c5c58", lw=1.8)
ax.axvline(melhor, color=COR_VIC, ls="--", lw=1.2)
ax.scatter([melhor], [corr.max()], color=COR_VIC, s=50, zorder=3)
ax.annotate(f"melhor sobreposição\n{melhor} min (r = {corr.max():.3f})".replace(".", ","),
            (melhor, corr.max()), xytext=(-190, -45), textcoords="offset points", fontsize=10,
            arrowprops=dict(arrowstyle="->", color="#5c5c58", lw=0.8))
ax.set(xlabel="Deslocamento aplicado à curva do Victron (min)", ylabel="Coeficiente de correlação, r (–)",
       title="Procura do deslocamento que melhor sobrepõe as curvas")
guardar(fig, "sinc_2_procura_deslocamento.png")

# ---------------------------------------------------------------- 3. curvas depois de deslocadas
vic_corr = normalizar(vic.shift(freq=pd.Timedelta(minutes=melhor)).loc[DIA])
fig, ax = plt.subplots(figsize=(7, 3.6))
ax.plot(ard.index, ard, color=COR_ARD, lw=1.6, label="Arduino (V × I)")
ax.plot(vic_corr.index, vic_corr, color=COR_VIC, lw=1.6, ls="--", label=f"Victron deslocado {melhor} min")
ax.set(xlabel=f"Hora do Arduino ({pd.Timestamp(DIA):%d/%m/%Y})", ylabel="Potência normalizada (–)",
       title="Curvas de potência após o deslocamento")
ax.xaxis.set_major_formatter(hora)
ax.legend(frameon=False, loc="upper left")
guardar(fig, "sinc_3_curvas_sincronizadas.png")

# ---------------------------------------------------------------- 4. defasagem de todos os dias e reta de correção
dd = ext.defasagens_diarias(ext.ler_arduino_p1(), v)
ok = dd["correlacao"] > 0.9
x = (dd["t"] - dd["t"].min()).dt.total_seconds() / 86400
reta = np.polyfit(x[ok], dd["defasagem_min"][ok], 1)

fig, ax = plt.subplots(figsize=(7, 3.6))
ax.plot(dd["t"], np.polyval(reta, x), color="#5c5c58", lw=1.4,
        label=f"Reta ajustada ({reta[0]:.2f} min/dia)".replace(".", ","))
ax.scatter(dd["t"][ok], dd["defasagem_min"][ok], color=COR_ARD, s=40, zorder=3, label="Defasagem diária")
ax.scatter(dd["t"][~ok], dd["defasagem_min"][~ok], facecolor="none", edgecolor=COR_ARD, s=40,
           label="Dia excluído (registo incompleto)")
ax.set(xlabel="Data (2026)", ylabel="Defasagem (min)", title="Defasagem ao longo da campanha")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
ax.legend(frameon=False)
guardar(fig, "sinc_4_defasagem_diaria.png")

print(f"\nDia {DIA}: defasagem = {melhor} min, r = {corr.max():.3f}")
print(f"Reta: defasagem = {reta[1]:.1f} {reta[0]:+.2f}·dias  →  cada registo dura {60 * (1 - reta[0] / 1440):.2f} s")

# ---------------------------------------------------------------- 5. figura única para a dissertação (3 painéis)
# Largura = largura útil do texto (16 cm). Inserir no Word SEM redimensionar.
LARGURA_CM = 16
sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)
C.aplicar_fonte()
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "legend.fontsize": 8})
fig, ax = plt.subplots(3, 1, figsize=(LARGURA_CM / 2.54, 15 / 2.54), constrained_layout=True)
janela = slice(f"{DIA} 05:00", f"{DIA} 23:00")

ax[0].plot(ard.loc[janela].index, ard.loc[janela], color=COR_ARD, lw=1.3, label="Arduino (V × I)")
ax[0].plot(vic.loc[janela].index, normalizar(vic.loc[DIA]).loc[janela], color=COR_VIC, lw=1.3, label="Victron")
ax[0].set(ylabel="Potência normalizada (–)", xlabel="Hora registada")
ax[0].xaxis.set_major_formatter(hora)

ax[1].plot(corr.index, corr.values, color="#5c5c58", lw=1.4)
ax[1].axvline(melhor, color=COR_VIC, ls="--", lw=1)
ax[1].scatter([melhor], [corr.max()], color=COR_VIC, s=25, zorder=3)
ax[1].annotate(f"{melhor} min; r = {corr.max():.3f}".replace(".", ","), (melhor, corr.max()),
               xytext=(-105, -28), textcoords="offset points", fontsize=8)
ax[1].set(xlabel="Deslocamento aplicado à curva do Victron (min)", ylabel="Correlação, r (–)")

ax[2].plot(ard.loc[janela].index, ard.loc[janela], color=COR_ARD, lw=1.3, label="Arduino (V × I)")
ax[2].plot(vic_corr.loc[janela].index, vic_corr.loc[janela], color=COR_VIC, lw=1.3, ls="--",
           label=f"Victron deslocado {melhor} min")
ax[2].set(ylabel="Potência normalizada (–)", xlabel="Hora do Arduino")
ax[2].xaxis.set_major_formatter(hora)

for a, letra in zip(ax, "abc"):
    a.text(0.99, 0.95, f"({letra})", transform=a.transAxes, fontsize=10, fontweight="bold", va="top", ha="right")
for a in (ax[0], ax[2]):
    a.legend(frameon=False, loc="upper left")
guardar(fig, "fig_4_2_sincronizacao_3paineis.png")
