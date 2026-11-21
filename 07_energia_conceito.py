"""07 — Produção anual com dados horários do PVGIS (Beja e Guimarães, 2019–2023):
módulo livre, protótipo, conceito e limite físico; indicadores económicos.

Correr (Jupyter, pasta codigo, depois do 01):  %run 07_energia_conceito.py
Lê:      dados/brutos/clima/pvgis_horario_beja.csv, pvgis_horario_guimaraes.csv
         (PVGIS 5.3, SARAH3, irradiância já no plano: 39° de inclinação, azimute −30°)
         resultados/tabelas/lab_indicadores.csv
Escreve: resultados/tabelas/energia_pvgis.csv, conceito_caudal.csv, economia_conceito.csv
         resultados/figuras/fig_conceito_caudal.png, fig_lcoe.png

Todas as contas são reprodutíveis à mão, hora a hora:
  G  = Gb(i) + Gd(i) + Gr(i)                    irradiância no plano (PVGIS)
  T  = T2m + G / U                              modelo de Faiman, U = U0 + U1·v (v = WS10m)
  P  = 545 · G/1000 · [1 + γ (T − 25)] · 0,95   γ = −0,0035 /K (ficha técnica)
Módulo arrefecido: U_arr = U0 + U1·v + ΔU − f_p·U1·v. Em cada hora escolhe-se o caudal (ou desligado)
que maximiza P − P_vent.

Conceito (placa ensaiada, sem escoamento cruzado):
  h(Re) pela correlação de Martin (script 05), ΔU = h · A_post / A_módulo
  ΔP_placa = ζ · ½ ρ U_j²  com ζ = 3,3 (medido)  →  P_hid = V̇ · ΔP_placa
  P_vent = P_hid / η_vent
  η_vent = 0,13: ventilador comercial pequeno (W2E200-CH38-01, ponto 795 m³/h, 40 Pa, 66 W;
                  0,221 m³/s × 40 Pa / 66 W = 0,13)  [FICHA]
  η_vent = 0,30 e 0,50: valores ilustrativos de ventiladores mais eficientes  [HIPÓTESE]
  Re abaixo de 2000 está fora do domínio da correlação de Martin  [EXTRAPOLAÇÃO]
"""
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import config as C

LOCAIS = {"Beja": C.BRUTOS / "clima" / "pvgis_horario_beja.csv",
          "Guimarães": C.BRUTOS / "clima" / "pvgis_horario_guimaraes.csv"}
ANOS = 5
U0, U1 = C.U0_FAIMAN, C.U1_FAIMAN
A_POST, ZETA, PR = 2.35, 3.3, 0.71
S_D, H_D = 9.17, C.FOLGA_H / C.D_ORIF
f = math.pi / 4 / S_D ** 2
K = (1 + (H_D / (0.6 / math.sqrt(f))) ** 6) ** -0.05
Gm = 2 * math.sqrt(f) * (1 - 2.2 * math.sqrt(f)) / (1 + 0.2 * (H_D - 6) * math.sqrt(f))


def martin(Re):
    return K * Gm * 0.5 * Re ** (2 / 3) * PR ** 0.42 * C.K_AR / C.D_ORIF


def potencia(G, T):
    return (C.P_STC * G / 1000 * (1 + C.GAMMA_FICHA * (T - 25)) * C.ETA_SISTEMA).clip(lower=0)


def ler(local):
    w = pd.read_csv(LOCAIS[local], parse_dates=["time"])
    w["G"] = w["Gb"] + w["Gd"] + w["Gr"]
    return w


def anual(w, estados, f_p):
    """estados: lista de (ΔU, P_vent). Devolve energia anual livre, ótima e horas de ventilação."""
    U = U0 + U1 * w["WS10m"]
    P0 = potencia(w["G"], w["T2m"] + w["G"] / U)
    melhor = potencia(w["G"], w["T2m"] + w["G"] / (U - f_p * U1 * w["WS10m"]))   # desligado (caixa fechada)
    on = pd.Series(False, index=w.index)
    for dU, Pv in estados:
        Pk = potencia(w["G"], w["T2m"] + w["G"] / (U + dU - f_p * U1 * w["WS10m"])) - Pv
        on = on | (Pk > melhor)
        melhor = np.maximum(melhor, Pk)
    return P0.sum() / 1000 / ANOS, melhor.sum() / 1000 / ANOS, on.sum() / ANOS


r = pd.read_csv(C.TAB / "lab_indicadores.csv", index_col=0)
linhas, curva = [], []
for local in LOCAIS:
    w = ler(local)
    U = U0 + U1 * w["WS10m"]
    T = w["T2m"] + w["G"] / U
    sol = w["G"] > 0
    E0 = potencia(w["G"], T).sum() / 1000 / ANOS
    E_lim = potencia(w["G"], w["T2m"]).sum() / 1000 / ANOS
    perda_media = (potencia(w["G"], w["T2m"]) - potencia(w["G"], T))[sol].mean()
    print(f"\n{local}: irradiação {w['G'].sum() / 1000 / ANOS:.0f} kWh/m²·ano; E livre {E0:.0f} kWh/ano; "
          f"T ponderada {np.average(T[sol], weights=w['G'][sol]):.1f} °C; horas T>50 °C {(T > 50).sum() / ANOS:.0f}; "
          f"perda média por temperatura nas horas de sol {perda_media:.1f} W")
    linhas.append(dict(local=local, cenario="limite físico (T = T_ar)", f_p=0, dE=E_lim - E0, E0=E0, horas=0))
    for cfg in ("SP", "CP"):
        dU = {fr: (r.loc[cfg + fr, "UA_final_WK"] - r.loc[cfg + "00", "UA_final_WK"]) / C.A_MODULO for fr in ("30", "40", "50")}
        for nome, Pv in (("ventilador ensaiado", {fr: C.P_VENT[fr] for fr in dU}),
                         ("ventilador ideal (P_hid)", {fr: r.loc[cfg + fr, "P_hid_W"] for fr in dU})):
            for f_p in (0.0, 0.5):
                e0, e1, h = anual(w, [(dU[fr], Pv[fr]) for fr in dU], f_p)
                linhas.append(dict(local=local, cenario=f"protótipo {cfg}, {nome}", f_p=f_p, dE=e1 - e0, E0=e0, horas=h))
    # conceito: varrimento de caudal
    for eta in (0.13, 0.30, 0.50):
        for V_m3h in (60, 100, 150, 215, 280, 355):
            V = V_m3h / 3600
            Uj = V / C.A_LIVRE; Re = Uj * C.D_ORIF / C.NU_AR
            h = martin(Re); dU = h * A_POST / C.A_MODULO
            Ph = V * ZETA * 0.5 * C.RHO_AR * Uj ** 2
            for f_p in (0.0, 0.5):
                e0, e1, hrs = anual(w, [(dU, Ph / eta)], f_p)
                curva.append(dict(local=local, eta=eta, V_m3h=V_m3h, Re=Re, h=h, dU=dU, P_hid=Ph, P_vent=Ph / eta,
                                  f_p=f_p, dE=e1 - e0, dE_pct=100 * (e1 - e0) / e0, horas=hrs))
en = pd.DataFrame(linhas); en["dE_pct"] = 100 * en.dE / en.E0
cv = pd.DataFrame(curva)
en.to_csv(C.TAB / "energia_pvgis.csv", index=False); cv.to_csv(C.TAB / "conceito_caudal.csv", index=False)
pd.set_option("display.width", 220)
print(en.round(2).to_string())
print(cv[cv.f_p == 0].round(2).to_string())

# ---------------------------------------------------------------- economia
PRECO = {"autoconsumo (Eurostat, 1.º sem. 2026)": 0.2367, "mercado grossista (OMIE PT, média 2024)": 0.0632}
N, TAXA, DEG = 25, 0.05, 0.005
F = sum((1 - DEG) ** (t - 1) / (1 + TAXA) ** t for t in range(1, N + 1))


def lcoe(capex, dE):          # custo nivelado da energia adicional (€/kWh)
    return capex / (dE * F) if dE > 0 else np.inf


def val(capex, dE, p):
    return -capex + p * dE * F


def tir(capex, dE, p):
    if p * dE <= 0:
        return np.nan
    lo, hi = -0.99, 1.0
    for _ in range(100):
        m = (lo + hi) / 2
        v = -capex + sum(p * dE * (1 - DEG) ** (t - 1) / (1 + m) ** t for t in range(1, N + 1))
        lo, hi = (m, hi) if v > 0 else (lo, m)
    return m


best = cv[cv.f_p == 0].loc[cv[cv.f_p == 0].groupby(["local", "eta"]).dE.idxmax()]
eco = []
for _, b in best.iterrows():
    for np_, p in PRECO.items():
        imax = p * b.dE * F
        for capex in (10, 25, 50):
            eco.append(dict(local=b.local, eta=b.eta, V_otimo=b.V_m3h, dE=b.dE, dE_pct=b.dE_pct, preco=np_, p=p,
                            I_max=imax, capex=capex, LCOE=lcoe(capex, b.dE), VAL=val(capex, b.dE, p),
                            TIR=tir(capex, b.dE, p)))
eco = pd.DataFrame(eco)
eco.to_csv(C.TAB / "economia_conceito.csv", index=False)
print(f"\nF = {F:.2f}")
print(eco.round(3).to_string())

# ---------------------------------------------------------------- figura do conceito
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(16 / 2.54, 6.5 / 2.54), sharey=True, constrained_layout=True)
cores = {0.13: "#eb6834", 0.30: "#1baa7a", 0.50: "#2a78d6"}
for a, f_p in zip(ax, (0.0, 0.5)):
    for eta, c in cores.items():
        d = cv[(cv.local == "Beja") & (cv.eta == eta) & (cv.f_p == f_p)]
        a.plot(d.V_m3h, d.dE_pct, color=c, marker="o", ms=4, lw=1.6, label=(r"$\eta_{vent}$ = " + f"{eta:.2f}".replace(".", ",")))
    a.axvspan(40, 353, color="#e9e9e6", zorder=0)
    a.text(48, 2.62, r"$Re_j$ < 2000 (fora do domínio de Martin)", fontsize=6.5, color="#5c5c58")
    a.axhline(0, color="#5c5c58", lw=0.8)
    a.axvline(215.6, color="#8a8a86", lw=0.8, ls="--")
    a.text(219, -1.45, "CP30", fontsize=6.5, color="#5c5c58")
    a.set_xlabel("Caudal por módulo (m³/h)"); a.set_xlim(40, 370); a.set_ylim(-1.6, 2.8)
    a.set_title(f"({'ab'[int(f_p * 2)]}) " + ("sem perda do arrefecimento posterior" if f_p == 0 else
                "perda de 50 % do arrefecimento posterior"), loc="left", fontsize=8)
    a.grid(color="#e6e6e3")
ax[0].set_ylabel("Variação da energia anual (%)")
ax[0].legend(frameon=False, loc="lower left")
fig.savefig(C.FIG / "fig_conceito_caudal.png", dpi=300, bbox_inches="tight")
print("Gravado: fig_conceito_caudal.png")


# ---------------------------------------------------------------- mapa ΔU × consumo (Beja), protótipo e conceito
w = ler("Beja")
mapa = []
for f_p in (0.0, 0.5):
    for dU in (2, 4, 7, 10, 15, 20, 30, 40):
        for Pv in (0, 2, 5, 10, 20, 40):
            e0, e1, h = anual(w, [(dU, Pv)], f_p)
            mapa.append(dict(f_p=f_p, dU=dU, P_vent=Pv, dE_pct=100 * (e1 - e0) / e0))
mapa = pd.DataFrame(mapa); mapa.to_csv(C.TAB / "mapa_projeto_beja.csv", index=False)
fig, ax = plt.subplots(1, 2, figsize=(16 / 2.54, 7 / 2.54), sharey=True, constrained_layout=True)
for a, f_p in zip(ax, (0.0, 0.5)):
    g = mapa[mapa.f_p == f_p].pivot(index="dU", columns="P_vent", values="dE_pct")
    im = a.imshow(g.values, origin="lower", cmap="RdBu", vmin=-4, vmax=4, aspect="auto")
    for (i, j), v in np.ndenumerate(g.values):
        a.text(j, i, f"{v:.1f}".replace(".", ",").replace("-0,0", "0,0"), ha="center", va="center", fontsize=6.5,
               color="white" if abs(v) > 2.5 else "#1f1f1d")
    a.set_xticks(range(len(g.columns)), [f"{c:g}" for c in g.columns])
    a.set_yticks(range(len(g.index)), [f"{c:g}" for c in g.index])
    a.set_xlabel("Consumo do ventilador (W)")
    a.set_title(f"({'ab'[int(f_p * 2)]}) " + ("sem perda do arrefecimento posterior" if f_p == 0 else
                "perda de 50 % do arrefecimento posterior"), loc="left", fontsize=8)
    a.tick_params(length=0)
ax[0].set_ylabel("Condutância acrescentada, ΔU (W/m²K)")
cb = fig.colorbar(im, ax=ax, shrink=0.9, pad=0.02); cb.set_label("Variação da energia anual (%)")
fig.savefig(C.FIG / "fig_mapa_projeto_beja.png", dpi=300, bbox_inches="tight")
print(mapa[mapa.f_p == 0].pivot(index="dU", columns="P_vent", values="dE_pct").round(2).to_string())

# ganho horário máximo do protótipo (CP50, ΔU medido) e tabela económica do conceito a 215 m³/h
U = U0 + U1 * w["WS10m"]
dU50 = (r.loc["CP50", "UA_final_WK"] - r.loc["CP00", "UA_final_WK"]) / C.A_MODULO
g = potencia(w["G"], w["T2m"] + w["G"] / (U + dU50)) - potencia(w["G"], w["T2m"] + w["G"] / U)
print(f"Beja: ganho horário máximo CP50 = {g.max():.1f} W")
tab = []
for eta in (0.13, 0.30, 0.50):
    dE = cv[(cv.local == "Beja") & (cv.eta == eta) & (cv.f_p == 0) & (cv.V_m3h == 215)].dE.iloc[0]
    for capex in (10, 25, 50):
        tab.append(dict(eta=eta, dE=dE, capex=capex, LCOE=lcoe(capex, dE),
                        VAL_auto=val(capex, dE, 0.2367), TIR_auto=tir(capex, dE, 0.2367),
                        VAL_merc=val(capex, dE, 0.0632), TIR_merc=tir(capex, dE, 0.0632)))
    print(f"η={eta}: ΔE={dE:.2f} kWh; I_max auto {0.2367 * dE * F:.1f} €, mercado {0.0632 * dE * F:.1f} €")
tab = pd.DataFrame(tab); tab.to_csv(C.TAB / "economia_conceito_215.csv", index=False)
print(tab.round(3).to_string())
for N_ in (20, 25, 30):
    for r_ in (0.03, 0.05, 0.08):
        F_ = sum((1 - DEG) ** (t - 1) / (1 + r_) ** t for t in range(1, N_ + 1))
        print(N_, r_, round(F_, 2))
