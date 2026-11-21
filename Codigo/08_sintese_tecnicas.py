"""Tabela 2.1 e Figura 2.6: valores reportados por estudo para as técnicas de arrefecimento fotovoltaico.

Todos os valores são transcritos das fontes, sem estimativas:
  [25] Dwivedi et al., Case Stud. Therm. Eng. 21 (2020) 100674 - Tabelas 4 a 10 e Secções 3.3 a 3.11
       (os estudos são identificados pelo autor indicado nessa revisão);
  [7] Rahimi et al. 2014; [9] Ali et al. 2025; [27] Bahaidarah et al. 2013; [29] Mazón-Hernández et al.;
  [54] Plant et al. 2023 (revisão).
dT e G: número, (min, max) ou None (não disponível ou não comparável). 'tipica' = gama típica sem estudo associado.
"""
import os
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D

# (n.º, grupo, técnica, estudo, método, dT, G, nota_dT, nota_G, ref)
ESTUDOS = [
    (1, "Passiva", "Dissipadores e alhetas", "Firoozzadeh et al.", "Exp.", 7.4, 2.72, "", "eficiência", "[25]"),
    (2, "Passiva", "Dissipadores e alhetas", "Parkunam et al.", "–", None, 6.05, "n.d.", "características elétricas", "[25]"),
    (3, "Passiva", "Dissipadores e alhetas", "Arifin et al.", "Num.", 12.5, 18.67, "85,3 → 72,8 °C", "potência no PMP", "[25]"),
    (4, "Passiva", "Materiais de mudança de fase", "Hasan et al.", "–", 10.5, 5.9, "média anual", "produção", "[25]"),
    (5, "Passiva", "Materiais de mudança de fase", "Tan et al.", "–", 15, 5.39, "", "eficiência", "[25]"),
    (6, "Passiva", "Materiais de mudança de fase", "Karthick et al.", "Num.", 9, None, "diferença máxima", "n.c.", "[25]"),
    (7, "Passiva", "Tubos de calor", "Tang et al. (ar)", "Exp.", 4.7, 8.4, "", "potência", "[25]"),
    (8, "Passiva", "Tubos de calor", "Tang et al. (água)", "Exp.", 8, 13.9, "", "potência", "[25]"),
    (9, "Passiva", "Tubos de calor", "Alizadeh et al.", "–", 16.1, 18, "", "potência", "[25]"),
    (10, "Passiva", "Tubos de calor", "Habeeb", "Num.", None, (11, 14), "n.c. (15–35 %)", "", "[25]"),
    (11, "Passiva", "Arrefecimento evaporativo", "Alami", "–", None, 15, "n.d.", "potência", "[25]"),
    (12, "Passiva", "Arrefecimento evaporativo", "Suresh et al.", "–", None, 10, "n.d.", "eficiência", "[25]"),
    (13, "Passiva", "Arrefecimento evaporativo", "Haidar et al.", "Num.", 6, None, "", "n.d.", "[25]"),
    (14, "Passiva", "Arrefecimento evaporativo", "Lucas et al.", "–", 8, (4.9, 7.9), "superior a 8 °C", "produção média", "[25]"),
    (15, "Ativa", "Ar forçado em canal", "Mazón-Hernández et al.", "Exp.", 15, 2, "temperatura máxima da célula", "eficiência global, face à convecção natural; valor mais baixo entre [25] e [29]", "[25], [29]"),
    (16, "Ativa", "Pulverização de água", "Nizetic et al.", "Exp.", None, 14.6, "n.d.", "potência", "[25]"),
    (17, "Ativa", "Pulverização de água", "Gama típica", "–", (0, 20), (0, 15), "até 20 °C", "até 15 %", "[25]"),
    (18, "Ativa", "Circulação de água", "Bahaidarah et al.", "Exp.", None, 9, "n.c. (cerca de 20 %)", "eficiência", "[27]"),
    (19, "Ativa", "Circulação de água", "Gama típica", "–", (20, 30), None, "", "n.d.", "[25]"),
    (20, "Ativa", "Imersão em água", "Mehrotra et al.", "–", None, 17.8, "n.d.", "eficiência; 1 cm de água", "[25]"),
    (21, "Ativa", "Imersão em água", "Gama típica", "–", 40, None, "", "n.d.", "[25]"),
    (22, "Ativa", "Módulos termoelétricos", "Benghanem et al.", "–", 18, None, "83 → 65 °C", "n.c.", "[25]"),
    (23, "Intensificação", "Canal de ar com nervuras", "Saadi et al.", "–", 6, None, "", "n.c.", "[25]"),
    (24, "Intensificação", "Microcanais com água", "Ali et al.", "Exp. e Num.", 15, 14, "", "potência", "[25]"),
    (25, "Intensificação", "Nanofluidos (PV/T)", "Hussein et al.", "–", 44, 50, "79 → 35 °C", "potência", "[25]"),
    (26, "Intensificação", "Nanofluidos (PV/T)", "Rostami et al.", "–", None, 51.1, "n.c. (até 57,25 %)", "potência máxima", "[25]"),
    (27, "Intensificação", "Jatos de impacto de ar", "Rahimi et al.", "Exp.", (15, 26), (3, 15), "célula; simulador", "célula; simulador", "[7]"),
    (28, "Intensificação", "Jatos de impacto de ar", "Ali et al.", "Num.", (8, 21), (4, 11), "face a um canal", "eficiência, face a um canal", "[9]"),
    (29, "Intensificação", "Jatos de água ou nanofluido", "Bahaidarah", "Exp.", None, (49.6, 51.6), "n.d.", "potência", "[54]"),
    (30, "Intensificação", "Jatos de água ou nanofluido", "Mohammadpour et al.", "Num.", None, 19.75, "n.d.", "eficiência", "[54]"),
]

if __name__ == "__main__":
    for f in ("/root/.fonts/NewsGotT-Regular.ttf", "/root/.fonts/NewsGotT-Bold.ttf"):
        if os.path.exists(f):
            fm.fontManager.addfont(f)
    plt.rcParams.update({"font.family": "NewsGotT", "font.size": 9, "axes.edgecolor": "#333333",
                         "axes.linewidth": 0.6, "xtick.major.width": 0.6, "xtick.color": "#333333",
                         "axes.labelcolor": "#111111", "mathtext.fontset": "dejavusans"})
    PRETO, CINZA, BANDA, DESTAQUE = "#1a1a1a", "#8c8c8c", "#e3e3e3", "#e8f0fa"

    # linhas: cabeçalhos de grupo + técnicas, pela ordem da tabela
    linhas = []
    for e in ESTUDOS:
        if not linhas or linhas[-1][1] != e[2]:
            if not any(l[0] == "grupo" and l[1] == e[1] for l in linhas):
                linhas.append(("grupo", e[1]))
            linhas.append(("tec", e[2]))
    ypos = {l[1]: len(linhas) - 1 - k for k, l in enumerate(linhas) if l[0] == "tec"}

    fig, axs = plt.subplots(1, 2, figsize=(16 / 2.54, 15 / 2.54), sharey=True, gridspec_kw={"wspace": 0.06})
    for ax, idx, xmax in ((axs[0], 5, 50), (axs[1], 6, 60)):
        ax.axhspan(ypos["Jatos de impacto de ar"] - 0.5, ypos["Jatos de impacto de ar"] + 0.5, color=DESTAQUE, zorder=0)
        # deslocamento vertical de cada estudo dentro da linha da técnica
        por_tec = {}
        for e in ESTUDOS:
            if e[idx] is not None:
                por_tec.setdefault(e[2], []).append(e[0])
        dy = {}
        for tec, ns in por_tec.items():
            m = len(ns)
            for j, n_ in enumerate(ns):
                dy[n_] = 0 if m == 1 else 0.30 - 0.60 * j / (m - 1)
        # banda min-máx por técnica (só estudos, sem gamas típicas)
        for tec, y in ypos.items():
            vals = []
            for e in ESTUDOS:
                if e[2] == tec and e[idx] is not None and e[3] != "Gama típica":
                    v = e[idx]; vals += list(v) if isinstance(v, tuple) else [v]
            if len(vals) > 1:
                ax.add_patch(plt.Rectangle((min(vals), y - 0.42), max(vals) - min(vals), 0.84, color=BANDA,
                                           lw=0, zorder=1))
        # pontos
        for e in ESTUDOS:
            v = e[idx]
            if v is None:
                continue
            y = ypos[e[2]] + dy[e[0]]
            num = e[4] == "Num."
            if e[3] == "Gama típica":
                a, b = v if isinstance(v, tuple) else (v, v)
                if a == b:
                    ax.plot(a, y, marker="D", ms=4, mfc="white", mec=CINZA, mew=1, zorder=3)
                else:
                    ax.plot([a, b], [y, y], color=CINZA, lw=1.2, ls=(0, (3, 2)), zorder=2)
                    ax.plot([a, b], [y, y], ls="", marker="|", ms=6, color=CINZA, zorder=3)
                xr = b
            elif isinstance(v, tuple):
                ax.plot(v, [y, y], color=PRETO, lw=1.2, zorder=2)
                for x in v:
                    ax.plot(x, y, marker="o", ms=4, mfc="white" if num else PRETO, mec=PRETO, mew=0.9, zorder=3)
                xr = v[1]
            else:
                ax.plot(v, y, marker="o", ms=4, mfc="white" if num else PRETO, mec=PRETO, mew=0.9, zorder=3)
                xr = v
            ax.text(xr + 0.018 * xmax, y, str(e[0]), ha="left", va="center", fontsize=6.3, color="#555555", zorder=4)
        ax.set_xlim(0, xmax); ax.set_ylim(-0.7, len(linhas) - 0.3)
        ax.grid(axis="x", color="#ececec", lw=0.6); ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
        for k, l in enumerate(linhas):
            if l[0] == "grupo" and k > 0:
                ax.axhline(len(linhas) - 1 - k + 0.5, color="#bdbdbd", lw=0.6)
    axs[0].set_xlabel("Redução de temperatura do módulo (°C)")
    axs[1].set_xlabel("Ganho elétrico relativo (%)")
    axs[0].set_title("(a)", loc="left", fontsize=9.5); axs[1].set_title("(b)", loc="left", fontsize=9.5)
    axs[0].set_yticks([len(linhas) - 1 - k for k in range(len(linhas))])
    axs[0].set_yticklabels([l[1].upper() if l[0] == "grupo" else l[1] for l in linhas])
    for lab, l in zip(axs[0].get_yticklabels(), linhas):
        if l[0] == "grupo":
            lab.set_fontweight("bold"); lab.set_fontsize(8.5)
    leg = [Line2D([0], [0], ls="", marker="o", ms=5, mfc=PRETO, mec=PRETO, label="Experimental ou não indicado"),
           Line2D([0], [0], ls="", marker="o", ms=5, mfc="white", mec=PRETO, label="Numérico"),
           Line2D([0], [0], color=PRETO, lw=1.3, label="Gama de um estudo"),
           Line2D([0], [0], color=CINZA, lw=1.2, ls=(0, (3, 2)), label="Gama típica [25]"),
           Line2D([0], [0], ls="", marker="D", ms=4.5, mfc="white", mec=CINZA, mew=1, label="Valor típico [25]"),
           Line2D([0], [0], color=BANDA, lw=7, label="Mínimo–máximo entre estudos")]
    fig.legend(handles=leg, loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.56, 0.0),
               columnspacing=1.2, handlelength=2.2)
    fig.subplots_adjust(left=0.27, right=0.985, top=0.96, bottom=0.16)
    os.makedirs("../resultados/figuras", exist_ok=True)
    fig.savefig("../resultados/figuras/fig_2_sintese_tecnicas.png", dpi=300, facecolor="white",
                bbox_inches="tight", pad_inches=0.04)
    print("ok")
