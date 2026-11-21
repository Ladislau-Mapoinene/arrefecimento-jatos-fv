"""03 — Monitorização exterior: relógio do Arduino, sincronização com o Victron, modelo elétrico,
verificação do sensor de irradiância e da orientação.

Correr:  python codigo/03_exterior_sincronizacao_modelo.py
Lê:      dados/brutos/DATA10.CSV, DATA25.CSV, Ensaio10_Victron.xlsx
Escreve: resultados/tabelas/defasagens_diarias.csv, modelo_eletrico.csv, sensor_ceu_limpo.csv
         resultados/figuras/fig_defasagem_relogio.png

Passos
 A. Lê o Victron (hora de verão, UTC+1) e o Arduino do período 1.
 B. Para cada dia, procura a defasagem (min) que maximiza a correlação entre a potência
    do Arduino (V·I) e a potência PV do Victron. Ajusta uma reta defasagem–tempo e corrige
    a escala de tempo do Arduino.
 C. Reproduz o modelo original SEM correção (controlo) e reajusta COM correção:
      M0  P = aG + bG(T−25) + c          (forma original)
      M1  P = k·G·[1 + γ(T−25)]          (forma física)
      M2  P = k·G·[1 + γ_ficha(T−25)]    (γ fixo na ficha técnica)
    Validação cruzada deixando um dia de fora.
 D. Período 2 (RTC, 1 Hz): compara G medido com o modelo de céu limpo (pvlib, Ineichen)
    para azimutes de 150°, 180° e 210°; dias limpos = correlação > 0,97.

PONTOS DE CONTROLO:
  modelo original reproduzido: n = 3313, a = 0,6995, b = −0,004129, c = −20,05, R² = 0,892
  defasagem: ≈ 141 min no início, −7,8 min/dia (registo ≈ 60,32 s em vez de 60 s)
  após correção: M1 dá γ positivo (+0,38 %/K na janela; +0,19 %/K no período completo)
  e M0 dá −0,15 %/K com c = −75 W → γ depende da forma do modelo: não identificável
  céu limpo: melhor azimute 150° (r ≈ 0,98), razão medido/teórico ≈ 0,82
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates
import openpyxl
import pvlib
import config as C


# ---------------------------------------------------------------- A. leitura
def ler_victron():
    wb = openpyxl.load_workbook(C.VICTRON_XLSX, read_only=True)
    it = wb["Log Data"].iter_rows(values_only=True)
    h0, h1 = next(it), next(it)
    nomes = [f"{a}|{b}" for a, b in zip(h0, h1)]
    quer = {"Timestamp|Hora de Verão de GMT": "t", "Solar Charger [288]|Charge state": "estado",
            "Solar Charger [288]|MPPT State": "mppt", "Solar Charger [288]|PV power": "P"}
    idx = {nomes.index(k): v for k, v in quer.items()}
    v = pd.DataFrame([[row[i] for i in idx] for row in it], columns=list(idx.values()))
    v["t"] = pd.to_datetime(v["t"]).dt.floor("min")
    return v.drop_duplicates("t").set_index("t")


def ler_arduino_p1():
    a = pd.read_csv(C.ARDUINO_P1, sep=";").iloc[:, :5]
    a.columns = ["t", "T", "V", "I", "G"]
    a["t"] = pd.to_datetime(a["t"], format="%d/%m/%Y %H:%M")
    a["Pa"] = -(a["V"] * a["I"])          # o sensor de corrente estava montado com sinal invertido
    return a


# ---------------------------------------------------------------- B. relógio
def defasagens_diarias(a, v):
    ai = a.set_index("t")
    res = []
    for dia in pd.date_range(ai.index.min().normalize(), ai.index.max().normalize()):
        melhor = None
        for lag in range(-30, 181):
            j = ai.loc[str(dia.date())].join(v["P"].shift(freq=pd.Timedelta(minutes=lag)).rename("Pv"),
                                             how="inner").dropna()
            if len(j) < 300:
                break
            r = j["Pa"].corr(j["Pv"])
            if melhor is None or r > melhor[1]:
                melhor = (lag, r)
        if melhor:
            res.append((dia + pd.Timedelta(hours=12), *melhor))
    return pd.DataFrame(res, columns=["t", "defasagem_min", "correlacao"])


def corrigir_relogio(a, d):
    x = (d["t"] - d["t"].min()).dt.total_seconds() / 86400
    bons = d["correlacao"] > 0.9
    reta = np.polyfit(x[bons], d["defasagem_min"][bons], 1)
    xa = (a["t"] - d["t"].min()).dt.total_seconds() / 86400
    a = a.copy()
    a["t_real"] = a["t"] - pd.to_timedelta(np.polyval(reta, xa), unit="min")
    return a, reta


def juntar(a, v, coluna_tempo):
    a = a.copy()
    a["tm"] = a[coluna_tempo].dt.round("min")
    j = a.drop_duplicates("tm").set_index("tm").join(v, how="inner")
    sel = j[(j["estado"] == "Bulk") & (j["mppt"] == "MPPT active") & (j["G"] >= C.G_MIN) & (j["P"] > 0)].copy()
    sel["dia"] = sel.index.date
    return sel


# ---------------------------------------------------------------- C. modelos
def ajustar(d, modelo):
    G, dT, P = d["G"].values, d["T"].values - 25, d["P"].values
    if modelo == "M0":
        X = np.c_[G, G * dT, np.ones(len(d))]
        return np.linalg.lstsq(X, P, rcond=None)[0]
    if modelo == "M1":
        k, kg = np.linalg.lstsq(np.c_[G, G * dT], P, rcond=None)[0]
        return np.array([k, kg / k])
    x = G * (1 + C.GAMMA_FICHA * dT)
    return np.array([(x * P).sum() / (x * x).sum(), C.GAMMA_FICHA])


def prever(c, d, modelo):
    G, dT = d["G"].values, d["T"].values - 25
    if modelo == "M0":
        return c[0] * G + c[1] * G * dT + c[2]
    return c[0] * G * (1 + c[1] * dT)


def avaliar(d, modelo):
    c = ajustar(d, modelo)
    e = d["P"].values - prever(c, d, modelo)
    sst = ((d["P"] - d["P"].mean()) ** 2).sum()
    erros = []
    for dia in d["dia"].unique():          # validação cruzada: deixa um dia de fora
        tr, te = d[d["dia"] != dia], d[d["dia"] == dia]
        erros.append(te["P"].values - prever(ajustar(tr, modelo), te, modelo))
    ecv = np.concatenate(erros)
    gamma = 100 * (c[1] / c[0] if modelo == "M0" else c[1])
    P_stc = c[0] * 1000 + (c[2] if modelo == "M0" else 0)
    return dict(modelo=modelo, n=len(d), coef=np.round(c, 6).tolist(), gamma_pct_K=gamma,
                P_1000_25_W=P_stc, RMSE_W=np.sqrt((e ** 2).mean()), R2=1 - (e ** 2).sum() / sst,
                RMSE_cv_W=np.sqrt((ecv ** 2).mean()), R2_cv=1 - (ecv ** 2).sum() / sst)


# ---------------------------------------------------------------- D. sensor e orientação
def ceu_limpo():
    e = pd.read_csv(C.ARDUINO_P2, sep=";", usecols=[0, 5])
    e.columns = ["ts", "G"]
    g = e.assign(t=pd.to_datetime(e["ts"], unit="s")).set_index("t")["G"].resample("1min").mean()
    g.index = g.index.tz_localize("Etc/GMT-1").tz_convert("UTC")   # RTC em hora de verão
    loc = pvlib.location.Location(C.LAT, C.LON)
    res = []
    for dia, gd in g.groupby(g.index.date):
        if len(gd) < 1400:
            continue
        sp, cs = loc.get_solarposition(gd.index), loc.get_clearsky(gd.index)
        gs = gd.rolling(21, center=True).median()
        linha = {"dia": dia}
        for az in (150, 180, 210):
            poa = pvlib.irradiance.get_total_irradiance(C.INCLINACAO, az, sp.apparent_zenith, sp.azimuth,
                                                        cs.dni, cs.ghi, cs.dhi).poa_global
            m = poa > 200
            linha[f"r_{az}"] = np.corrcoef(gs[m].fillna(0), poa[m])[0, 1]
            linha[f"razao_{az}"] = (gs[m] / poa[m]).median()
        res.append(linha)
    return pd.DataFrame(res).set_index("dia")


def main():
    v, a = ler_victron(), ler_arduino_p1()
    d = defasagens_diarias(a, v)
    a, reta = corrigir_relogio(a, d)
    print(d.round(3).to_string())
    print(f"\nDefasagem = {reta[1]:.1f} min {reta[0]:+.2f} min/dia → cada registo dura "
          f"{60 * (1 - reta[0] / 1440):.2f} s\n")
    d.to_csv(C.TAB / "defasagens_diarias.csv", index=False)

    linhas = []
    original = juntar(a, v, "t")
    jan = original[(original.index >= "2026-06-29") & (original.index < "2026-07-07")]
    linhas.append({"caso": "original, sem correção, 29/06–06/07", **avaliar(jan, "M0")})
    corr = juntar(a, v, "t_real")
    jan_c = corr[(corr.index >= "2026-06-29") & (corr.index < "2026-07-07")]
    for caso, dd in (("corrigido, 29/06–06/07", jan_c), ("corrigido, todo o período", corr)):
        for m in ("M0", "M1", "M2"):
            linhas.append({"caso": caso, **avaliar(dd, m)})
    mod = pd.DataFrame(linhas)
    pd.set_option("display.width", 220)
    print(mod.round(3).to_string())
    print(f"\nCorrelação G–T (corrigido, todo o período): {np.corrcoef(corr['G'], corr['T'])[0, 1]:.2f}")
    mod.to_csv(C.TAB / "modelo_eletrico.csv", index=False)

    cl = ceu_limpo()
    limpos = cl[cl[["r_150", "r_180", "r_210"]].max(axis=1) > 0.97]
    print(f"\nDias limpos: {len(limpos)}\n{limpos.mean().round(3).to_string()}")
    cl.to_csv(C.TAB / "sensor_ceu_limpo.csv")

    fig, ax = plt.subplots(figsize=(6, 3.2), constrained_layout=True)
    ok = d["correlacao"] > 0.9
    ax.plot(d["t"][ok], d["defasagem_min"][ok], "o", color="#2a78d6", ms=6, label="Defasagem diária (r > 0,9)")
    ax.plot(d["t"][~ok], d["defasagem_min"][~ok], "o", mfc="none", mec="#2a78d6", ms=6,
            label="Dia excluído (registo incompleto, r < 0,9)")
    x = (d["t"] - d["t"].min()).dt.total_seconds() / 86400
    ax.plot(d["t"], np.polyval(reta, x), color="#5c5c58", lw=1.5, label="Ajuste linear")
    ax.set_ylabel("Defasagem Arduino–Victron (min)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d/%m"))
    ax.set_xlabel("Data (2026)")
    fig.savefig(C.FIG / "fig_defasagem_relogio.png", dpi=200)


if __name__ == "__main__":
    main()
