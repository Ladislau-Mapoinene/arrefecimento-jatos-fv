"""Velocidades do ar medidas à saída (anemómetro de fio quente, 12 pontos, 3 por rasgo) e caudal resultante.
Fonte: folha 'Vout' de dados/brutos/Analise_geral_16.10.xlsx (valores mínimo e máximo lidos em cada ponto)."""
import numpy as np
import pandas as pd
import config as C

A_SAIDA = 0.01104   # m², área total dos quatro rasgos
bruto = pd.read_excel(C.RAIZ / "dados/brutos/Analise_geral_16.10.xlsx", sheet_name="Vout", header=None)
linhas = []
for lin0, prefixo in ((4, "SP"), (23, "CP")):            # linha do cabeçalho 'Ponto' de cada bloco (base 0)
    for col0, freq in ((1, "30"), (6, "40"), (11, "50")):
        b = bruto.iloc[lin0 + 1:lin0 + 13, col0:col0 + 3].astype(float).values   # ponto, Vmax, Vmin
        vmed = (b[:, 1] + b[:, 2]) / 2
        rasgos = vmed.reshape(4, 3).mean(axis=1)
        linhas.append({"ensaio": prefixo + freq, "V_media": vmed.mean(), "desvio": vmed.std(ddof=1),
                       "CV_pct": 100 * vmed.std(ddof=1) / vmed.mean(), "V_min_ponto": vmed.min(),
                       "V_max_ponto": vmed.max(), "dif_max_min_leitura": (b[:, 1] - b[:, 2]).__abs__().max(),
                       "rasgo1": rasgos[0], "rasgo2": rasgos[1], "rasgo3": rasgos[2], "rasgo4": rasgos[3],
                       "caudal_m3h": vmed.mean() * A_SAIDA * 3600})
t = pd.DataFrame(linhas)
t.to_csv(C.RAIZ / "resultados/tabelas/lab_velocidades_saida.csv", index=False)
print(t.round(3).to_string(index=False))
