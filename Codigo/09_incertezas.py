"""09 — Balanço de incertezas dos ensaios laboratoriais (GUM, avaliação do tipo B e propagação linear).

Limites de erro das fichas técnicas (a), convertidos em incerteza-padrão u = a/√3 (distribuição retangular):
  ΔP  — Sensirion SDP610-500Pa: a = 0,2 Pa + 3 % da leitura (zero + ganho, somados como indica a ficha)
  V   — Benetech GM8903: a = 3 % da leitura + 0,1 m/s (leitura conservadora de «±3 % ±0,1 dgts»)
  V_R — Fluke 87V, tensão alternada: a = 0,7 % + 2 dígitos (0,01 V no valor de 20,45 V)
  R   — Fluke 87V, resistência: a = 0,2 % + 1 dígito (0,1 Ω no valor de 10,8 Ω)
Temperatura: a calibração in situ remove o desvio fixo de cada termopar (classe 2, IEC 60584-1) e do
módulo NI 9212; a incerteza de θ é a repetibilidade obtida na repetição do CP30, u = |Δθ|/√2.
Não incluídos: área dos rasgos de saída, aquecimento das resistências (R medida a frio) e consumo do
ventilador (wattímetro sem exatidão especificada).
Incerteza expandida U = 2u (fator de expansão k = 2, nível de confiança de cerca de 95 %).
"""
import numpy as np
import pandas as pd
import config as C

R3 = np.sqrt(3)
ind = pd.read_csv(C.RAIZ / "resultados/tabelas/lab_indicadores.csv").set_index("ensaio")
vel = pd.read_csv(C.RAIZ / "resultados/tabelas/lab_velocidades_saida.csv").set_index("ensaio")
rep = pd.read_csv(C.RAIZ / "resultados/tabelas/lab_repeticoes.csv").set_index("ensaio")

# --- temperatura (repetibilidade)
u_theta = abs(rep.loc["CP30", "theta_final_rep"] - rep.loc["CP30", "theta_final_orig"]) / np.sqrt(2)

# --- potência de aquecimento P = V²/R, com V = 3·V_R
V_R, R = C.TENSAO_RESIST / 3, C.R_EQ
u_VR = (0.007 * V_R + 0.02) / R3
u_R = (0.002 * R + 0.1) / R3
ur_P = np.hypot(2 * u_VR / V_R, u_R / R)
u_P = ur_P * C.P_EL


def u_dP(dp):
    return (0.2 + 0.03 * dp) / R3


def ur_caudal(e):
    v = vel.loc[e]
    u_inst = (0.03 * v.V_media + 0.1) / R3
    u_esp = v.desvio / np.sqrt(12)              # média de 12 pontos
    return np.hypot(u_inst, u_esp) / v.V_media


linhas = []
for e in ["SP00", "SP30", "SP40", "SP50", "CP00", "CP30", "CP40", "CP50"]:
    th = ind.loc[e, "theta_final"]
    UA = C.P_EL / th
    u_UA = UA * np.hypot(ur_P, u_theta / th)
    lin = dict(ensaio=e, theta=th, U_theta=2 * u_theta, UA=UA, U_UA=2 * u_UA)
    if not e.endswith("00"):
        e0 = e[:2] + "00"; th0 = ind.loc[e0, "theta_final"]
        dinv = 1 / th - 1 / th0
        u_h = np.sqrt((dinv * u_P) ** 2 + (C.P_EL * u_theta / th ** 2) ** 2 + (C.P_EL * u_theta / th0 ** 2) ** 2)
        Vd, dp = ind.loc[e, "caudal_m3h"], ind.loc[e, "dP_Pa"]
        urV, urP = ur_caudal(e), u_dP(dp) / dp
        lin.update(h_ef=C.P_EL * dinv / 2.35, U_h_ef=2 * u_h / 2.35,
                   caudal=Vd, U_caudal=2 * urV * Vd, dP=dp, U_dP=2 * u_dP(dp),
                   P_hid=ind.loc[e, "P_hid_W"], U_P_hid=2 * np.hypot(urV, urP) * ind.loc[e, "P_hid_W"])
    linhas.append(lin)
t = pd.DataFrame(linhas).set_index("ensaio")

# --- coeficiente de perda da placa ζ = (ΔP_CP − ΔP_SP·(V̇_CP/V̇_SP)²) / (½ρU_j²), derivadas numéricas
def zeta(dcp, dsp, vcp, vsp):
    uj = vcp / 3600 / C.A_LIVRE
    return (dcp - dsp * (vcp / vsp) ** 2) / (0.5 * C.RHO_AR * uj ** 2)


for f in ("30", "40", "50"):
    x = np.array([ind.loc["CP" + f, "dP_Pa"], ind.loc["SP" + f, "dP_Pa"],
                  ind.loc["CP" + f, "caudal_m3h"], ind.loc["SP" + f, "caudal_m3h"]])
    u = np.array([u_dP(x[0]), u_dP(x[1]), ur_caudal("CP" + f) * x[2], ur_caudal("SP" + f) * x[3]])
    z0 = zeta(*x); var = 0
    for k in range(4):
        dx = np.zeros(4); dx[k] = 1e-6 * x[k]
        var += ((zeta(*(x + dx)) - z0) / dx[k] * u[k]) ** 2
    t.loc["CP" + f, "zeta"], t.loc["CP" + f, "U_zeta"] = z0, 2 * np.sqrt(var)

t.to_csv(C.RAIZ / "resultados/tabelas/lab_incertezas.csv")
print(f"u_theta = {u_theta:.2f} K; P_el = {C.P_EL:.1f} ± {2*u_P:.1f} W (U, k=2; {200*ur_P:.1f} %)")
pd.set_option("display.width", 200)
print(t.round(3).to_string())
