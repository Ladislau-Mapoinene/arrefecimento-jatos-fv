"""05 — Transferência de calor na face posterior: valores medidos vs correlação de Martin (1977).

Correr (Jupyter, pasta codigo, depois do 01):  %run 05_correlacao_economia.py
Escreve: resultados/tabelas/correlacao_martin.csv

1) Coeficiente efetivo a partir da potência elétrica (valor robusto, porque P_el é conhecida):
      h_UA = (UA_vent − UA_sem_vent) / A_post,     UA = P_el / θ
2) Coeficiente a partir do balanço do ar (verificação; depende de T_out num só ponto):
      h_ar = Q̇_ar / [A_post · (T̄m − (T_in + T_out)/2)]
3) Correlação de Martin (1977) para matrizes de jatos circulares:
      Nu = K·G·F2·Pr^0,42,   K = [1 + ((H/D)/(0,6/√f))^6]^−0,05
      G  = 2√f (1 − 2,2√f) / (1 + 0,2 (H/D − 6) √f),   F2 = 0,5·Re^(2/3)
   Domínio: 2000 ≤ Re ≤ 100 000; 0,004 ≤ f ≤ 0,04; 2 ≤ H/D ≤ 12.
4) Escoamento cruzado: o ar dos jatos sai todo pela folga placa–módulo (16,5 mm) em direção ao topo.
   Velocidade máxima do escoamento cruzado (junto à saída): U_c = V̇ / (H · L), L = 1,064 m.

PONTOS DE CONTROLO: f ≈ 0,0093; h Martin CP50 ≈ 49 W/m²K; h_UA CP50 ≈ 7,7 W/m²K; U_c/U_j ≈ 1,07
"""
import math
import pandas as pd
import config as C

PR = 0.71
S_D = 9.17              # passo/diâmetro da matriz (projeto: 55 mm / 6 mm)
H_D = C.FOLGA_H / C.D_ORIF
A_POST = 2.35           # m² área posterior arrefecida (≈ 1,064 × 2,208 m)
L_PLACA = 1.064         # m  largura da folga

f = math.pi / 4 / S_D ** 2
K = (1 + (H_D / (0.6 / math.sqrt(f))) ** 6) ** -0.05
G = 2 * math.sqrt(f) * (1 - 2.2 * math.sqrt(f)) / (1 + 0.2 * (H_D - 6) * math.sqrt(f))

r = pd.read_csv(C.TAB / "lab_indicadores.csv", index_col=0)
S = pd.read_pickle(C.PROC / "lab_series.pkl")
FOLHA = {"SP30": "SP00_30", "SP40": "SP40", "SP50": "SP50", "CP30": "CP00_30", "CP40": "CP40", "CP50": "CP50"}

linhas = []
for e, folha in FOLHA.items():
    fim = S[folha].iloc[-C.JANELA:]
    dTm = fim["Tm"].mean() - (fim["Tin"].mean() + fim["Tout"].mean()) / 2
    V = r.loc[e, "caudal_m3h"] / 3600
    lin = dict(ensaio=e,
               h_UA=(r.loc[e, "UA_final_WK"] - r.loc[e[:2] + "00", "UA_final_WK"]) / A_POST,
               h_ar=r.loc[e, "Q_ar_W"] / (A_POST * dTm),
               Q_ar_frac_pct=100 * r.loc[e, "Q_ar_W"] / C.P_EL,
               U_cruzado_max=V / (C.FOLGA_H * L_PLACA))
    if e.startswith("CP"):
        Re = r.loc[e, "Re_j"]
        lin.update(Re_j=Re, U_j=r.loc[e, "Uj_ms"], dentro_dominio=Re >= 2000,
                   h_Martin=K * G * 0.5 * Re ** (2 / 3) * PR ** 0.42 * C.K_AR / C.D_ORIF)
        lin["razao_Uc_Uj"] = lin["U_cruzado_max"] / lin["U_j"]
        lin["h_Martin_sobre_h_UA"] = lin["h_Martin"] / lin["h_UA"]
    linhas.append(lin)
cm = pd.DataFrame(linhas).set_index("ensaio")
print(f"f = {f:.4f}, H/D = {H_D:.2f}, K = {K:.3f}, G = {G:.3f}")
pd.set_option("display.width", 200)
print(cm.round(2).to_string())
cm.to_csv(C.TAB / "correlacao_martin.csv")
