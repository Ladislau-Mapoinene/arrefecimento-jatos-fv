"""01 — Reanálise dos ensaios laboratoriais (SP/CP; 0, 30, 40, 50 Hz).

Correr:  python codigo/01_lab_reanalise.py
Lê:      dados/brutos/Analise_geral_16.10.xlsx
Escreve: resultados/tabelas/lab_indicadores.csv
         resultados/tabelas/desvios_termopares.csv
         dados/processados/lab_series.pkl  (séries limpas, para as figuras)

Passos
 1. Remove linhas inválidas (zeros no fim de algumas folhas).
 2. Calibração in situ: nos primeiros 120 s do SP00 o módulo estava à
    temperatura da sala, logo todos os termopares deviam ler o mesmo valor.
    O desvio de cada um face à média é subtraído em todos os ensaios.
 3. Deteta o arranque do ventilador (queda mais rápida de T̄m).
 4. Estado sem ventilação: média dos 300 s antes do arranque.
    Estado final: média dos últimos 300 s, declive final e ajuste exponencial
    θ(t) = θ∞ + (θ0 − θ∞)·exp(−t/τ).
 5. Indicadores: UA = P_el/θ, U_j, Re_j, potência hidráulica V̇·ΔP,
    Q̇_ar = ρ·cp·V̇·(T_out − T_in), médias por linha de termopares.

PONTOS DE CONTROLO (devem sair iguais, a ±0,01):
  desvio T_out − T_in no período isotérmico ............. +0,68 K
  θ_final SP30 / CP30 (corrigidos) ..................... 18,86 / 15,63 K
  Re_j CP30 / CP40 / CP50 .............................. 1223 / 1600 / 2018
"""
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import config as C


def ler_folha(folha):
    df = pd.read_excel(C.LAB_XLSX, sheet_name=folha, usecols=range(22))
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(subset=["Tsuf_m"])
    validas = (df[C.TODOS_TERMOPARES] > 5).all(axis=1)   # elimina linhas a zero
    return df[validas].reset_index(drop=True)


def desvios_termopares():
    inicio = ler_folha("SP00_30").iloc[:C.N_ISOTERMICO][C.TODOS_TERMOPARES].mean()
    return inicio - inicio.mean()


def indice_arranque(temp):
    """Instante de arranque do ventilador: a partir da queda mais rápida de T̄m, recua
    enquanto a temperatura ainda estiver a descer de forma clara (> 0,5 °C/min)."""
    suave = pd.Series(temp).rolling(11, center=True, min_periods=1).mean().values
    deriv = np.gradient(suave) / C.DT_AMOSTRA * 60      # °C/min
    i = int(np.argmin(deriv))                           # queda mais rápida
    while i > 0 and deriv[i - 1] < -0.5:
        i -= 1
    return i


def exponencial(t, th_inf, th0, tau):
    return th_inf + (th0 - th_inf) * np.exp(-t / tau)


def declive(x):
    """Declive linear em °C/min."""
    return np.polyfit(np.arange(len(x)) * C.DT_AMOSTRA, x, 1)[0] * 60


def medias_por_linha(bloco):
    return [bloco[[f"T{r}{c}" for c in (1, 2, 3)]].mean(axis=1).mean() for r in (1, 2, 3)]


def main():
    desv = desvios_termopares()
    print("Desvios dos termopares no período isotérmico (K):")
    print(desv.round(2).to_string())
    print(f"→ T_out − T_in = {desv['Tout'] - desv['Tin']:+.2f} K\n")

    linhas, series = [], {}
    for folha in C.FOLHAS_LAB:
        df = ler_folha(folha)
        df[C.TODOS_TERMOPARES] = df[C.TODOS_TERMOPARES] - desv[C.TODOS_TERMOPARES]
        df["Tm"] = df[C.SUPERFICIE].mean(axis=1)
        df["sigma"] = df[C.SUPERFICIE].std(axis=1, ddof=0)
        df["theta"] = df["Tm"] - df["Tin"]

        cfg = folha[:2]
        freq = "30" if folha.endswith("00_30") else folha[2:]
        chave = cfg + freq
        i0 = indice_arranque(df["Tm"].values)
        antes, fim = df.iloc[max(0, i0 - C.JANELA):i0], df.iloc[-C.JANELA:]

        if folha.endswith("00_30"):   # a fase antes do arranque é o ensaio sem ventilação
            linhas.append(dict(ensaio=cfg + "00", theta_final=antes["theta"].mean(),
                               declive_final=declive(antes["Tm"].values),
                               sigma=antes["sigma"].mean(), Tm=antes["Tm"].mean(),
                               linhas_T=medias_por_linha(antes)))

        trans = df.iloc[i0 + 20:]     # transitório, sem os primeiros 20 s
        t = np.arange(len(trans)) * C.DT_AMOSTRA
        par, cov = curve_fit(exponencial, t, trans["theta"].values,
                             p0=[trans["theta"].iloc[-1], trans["theta"].iloc[0], 300.0], maxfev=20000)

        V = C.CAUDAL_M3H[chave] / 3600
        dp = C.DP_PA[chave][0]
        Uj = V / C.A_LIVRE if cfg == "CP" else np.nan
        dT_ar = (fim["Tout"] - fim["Tin"]).mean()
        linhas.append(dict(
            ensaio=chave, duracao_vent_s=(len(df) - i0) * C.DT_AMOSTRA,
            theta_antes=antes["theta"].mean(), declive_antes=declive(antes["Tm"].values),
            theta_final=fim["theta"].mean(), declive_final=declive(fim["Tm"].values),
            theta_inf=par[0], theta_inf_ep=np.sqrt(cov[0, 0]), tau_s=par[2],
            sigma=fim["sigma"].mean(), Tm=fim["Tm"].mean(),
            caudal_m3h=C.CAUDAL_M3H[chave], dP_Pa=dp, P_hid_W=V * dp, P_vent_W=C.P_VENT[freq],
            Uj_ms=Uj, Re_j=Uj * C.D_ORIF / C.NU_AR,
            dT_ar=dT_ar, Q_ar_W=C.RHO_AR * C.CP_AR * V * dT_ar,
            linhas_T=medias_por_linha(fim)))
        series[folha] = df.assign(t_s=(np.arange(len(df)) - i0) * C.DT_AMOSTRA)

    res = pd.DataFrame(linhas).set_index("ensaio")
    res["UA_final_WK"] = C.P_EL / res["theta_final"]
    res["UA_inf_WK"] = C.P_EL / res["theta_inf"]
    linhas_T = pd.DataFrame(res.pop("linhas_T").tolist(), index=res.index,
                            columns=["linha1_entrada", "linha2_meio", "linha3_saida"])
    res = res.join(linhas_T)

    pd.set_option("display.width", 200)
    print(res[["theta_final", "declive_final", "theta_inf", "tau_s", "sigma",
               "UA_final_WK", "Re_j", "P_hid_W", "Q_ar_W"]].round(2).to_string())
    res.to_csv(C.TAB / "lab_indicadores.csv")
    desv.to_csv(C.TAB / "desvios_termopares.csv", header=["desvio_K"])
    pd.to_pickle(series, C.PROC / "lab_series.pkl")
    print("\nGravado em resultados/tabelas/lab_indicadores.csv")


if __name__ == "__main__":
    main()
