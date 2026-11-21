"""03d — Dados medidos na monitorização exterior: um dia completo e resumo da campanha (secção 4.1).

Correr (Jupyter, pasta codigo):  %run 03d_dados_exterior.py
Lê:      dados/brutos/DATA10.CSV, dados/brutos/Ensaio10_Victron.xlsx
Escreve: resultados/figuras/fig_4_dia_exterior.png
         resultados/tabelas/exterior_resumo.csv

Usa a correção do relógio do Arduino (script 03). Mostra os valores tal como foram medidos,
antes de qualquer seleção, para dar o ponto de partida da análise.
"""
import importlib
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import config as C

ext = importlib.import_module("03_exterior_sincronizacao_modelo")
DIA = "2026-06-20"

v, a = ext.ler_victron(), ext.ler_arduino_p1()
d = ext.defasagens_diarias(a, v)
a, reta = ext.corrigir_relogio(a, d)
a["tm"] = a["t_real"].dt.round("min")
j = a.drop_duplicates("tm").set_index("tm").join(v, how="left")

# resumo da campanha (registos selecionados: Bulk, MPPT ativo, G ≥ 200 W/m², P > 0)
sel = ext.juntar(a, v, "t_real")
res = pd.DataFrame({
    "registos": [len(sel)], "dias": [sel["dia"].nunique()],
    "G_min": [sel["G"].min()], "G_max": [sel["G"].max()], "G_media": [sel["G"].mean()],
    "T_min": [sel["T"].min()], "T_max": [sel["T"].max()], "T_media": [sel["T"].mean()],
    "P_max": [sel["P"].max()], "P_media": [sel["P"].mean()]})
res.to_csv(C.TAB / "exterior_resumo.csv", index=False)
print(res.round(1).T.to_string())

dia = j.loc[DIA]
print(f"\n{DIA}: G máx {dia['G'].max():.0f} W/m²; T máx {dia['T'].max():.1f} °C; P Victron máx {dia['P'].max():.0f} W")

plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(3, 1, figsize=(16 / 2.54, 10 / 2.54), sharex=True, constrained_layout=True)
ax[0].plot(dia.index, dia["G"], color="#c98a00", lw=1)
ax[0].set_ylabel("Irradiância\n(W/m²)")
ax[1].plot(dia.index, dia["T"], color="#c0392b", lw=1)
ax[1].set_ylabel("Temperatura do\nmódulo (°C)")
ax[2].plot(dia.index, dia["P"], color="#eb6834", lw=1, label="Victron")
ax[2].plot(dia.index, dia["Pa"], color="#2a78d6", lw=0.8, alpha=0.8, label="Arduino (V·I)")
ax[2].set_ylabel("Potência (W)")
ax[2].legend(frameon=False, loc="upper left")
for k, x in enumerate(ax):
    x.grid(color="#e6e6e3")
    x.set_title(f"({'abc'[k]})", loc="left", fontsize=8)
ax[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax[2].set_xlabel("Hora (20/06/2026, registos do Arduino corrigidos)")
fig.savefig(C.FIG / "fig_4_dia_exterior.png", dpi=300, bbox_inches="tight")
print("Gravado: fig_4_dia_exterior.png")
