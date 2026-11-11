"""EXTRA — Panorama do porto inteiro (todos os tipos de navio).

Útil para a introdução do relatório (contextualizar o recorte escolhido) e caso a
equipe queira modelar outro subsistema (ex.: terminais de ferry/cruzeiros).

Saídas em resultados/05_panorama_porto/:
  - resumo_por_tipo_navio.csv       -> volume, chegadas/dia, permanência e distribuições sugeridas por tipo
  - top_terminais/origens/bandeiras/consignatarios.csv
  - chegadas_por_tipo_mes.png, permanencia_por_tipo.png
  - panorama.md
"""
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from comum import RES, limites_iqr, pasta, salvar_fig, tec_horas

warnings.filterwarnings("ignore")
OUT = pasta("05_panorama_porto")
porto = pd.read_csv(RES / "01_dados" / "escalas_porto_limpo.csv", parse_dates=["ETA", "ETD"], low_memory=False)
DIAS = (porto.ETA.max() - porto.ETA.min()).total_seconds() / 86400
TRAD = {"Transbordadors": "Ferry (transbordador)", "Portacontenidors": "Porta-contêineres", "Tancs": "Tanque",
        "Passatge": "Passageiros/cruzeiro", "Ro-Ro": "Ro-Ro", "Car-carrier": "Transporte de veículos",
        "Càrrega (Lo-Lo)": "Carga geral (Lo-Lo)", "Petroliers": "Petroleiro", "Granelers": "Graneleiro"}
porto["TIPO"] = porto.VAIXELLTIPUS.map(TRAD).fillna(porto.VAIXELLTIPUS)


def melhor_dist(x):
    """Melhor entre EXPO/GAMM/WEIB/LOGN pelo erro quadrático; devolve expressão Arena."""
    x = np.where(x <= 0, 1e-2, x)
    k = min(40, max(8, int(np.ceil(np.sqrt(len(x))))))
    edges = np.linspace(x.min(), x.max(), k + 1)
    obs = np.histogram(x, edges)[0] / len(x)
    out = []
    for nome, d in [("EXPO", stats.expon), ("GAMM", stats.gamma), ("WEIB", stats.weibull_min),
                    ("LOGN", stats.lognorm)]:
        par = d.fit(x, floc=0)
        fr = d(*par)
        sq = np.sum((obs - np.diff(fr.cdf(edges))) ** 2)
        if nome == "EXPO":
            ex = f"EXPO({par[1]:.2f})"
        elif nome == "LOGN":
            m = fr.mean(); ex = f"LOGN({m:.2f}, {fr.std():.2f})"
        else:
            ex = f"{nome}({par[2]:.2f}, {par[0]:.3f})"
        out.append((sq, ex))
    return min(out)[1]


rows = []
for tipo, g in porto.groupby("TIPO"):
    _, sup = limites_iqr(g.PERM_H, 3)
    p = g.PERM_H[g.PERM_H <= sup]
    tec = tec_horas(g.ETA)
    rows.append({"Tipo de navio": tipo, "Escalas": len(g), "% do porto": 100 * len(g) / len(porto),
                 "Chegadas/dia": len(g) / DIAS, "TEC médio (h)": tec.mean(), "CV do TEC": tec.std() / tec.mean(),
                 "Permanência média (h)": p.mean(), "Permanência mediana (h)": p.median(),
                 "Desvio perm. (h)": p.std(), "Atípicos perm. (3×IQR)": int((g.PERM_H > sup).sum()),
                 "Eslora média (m)": g.ESLORA_METRES.mean(),
                 "Dist. sugerida TEC": melhor_dist(tec.to_numpy()),
                 "Dist. sugerida permanência": melhor_dist(p.to_numpy())})
res = pd.DataFrame(rows).sort_values("Escalas", ascending=False).round(2)
res.to_csv(OUT / "resumo_por_tipo_navio.csv", index=False)

tops = {}
for col, nome in [("TERMINALNOM", "terminais"), ("PORTORIGENNOM", "origens"),
                  ("VAIXELLBANDERANOM", "bandeiras"), ("CONSIGNATARI", "consignatarios")]:
    t = porto[col].str.strip().value_counts().head(15).rename_axis(col).reset_index(name="Escalas")
    t["%"] = (100 * t.Escalas / len(porto)).round(2)
    t.to_csv(OUT / f"top_{nome}.csv", index=False)
    tops[nome] = t

piv = porto.groupby([porto.ETA.dt.month, "TIPO"]).size().unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(11, 4.5))
piv[res["Tipo de navio"]].plot(kind="bar", stacked=True, ax=ax, width=.8, colormap="tab10")
ax.set_xlabel("Mês de 2025"); ax.set_ylabel("Escalas"); ax.set_title("Escalas por mês e tipo de navio")
ax.legend(fontsize=8, ncol=3); ax.tick_params(axis="x", rotation=0)
salvar_fig(fig, OUT / "chegadas_por_tipo_mes.png")

fig, ax = plt.subplots(figsize=(10, 4.5))
ordem = res["Tipo de navio"].tolist()
dados = [porto.loc[porto.TIPO == t, "PERM_H"].clip(upper=200) for t in ordem]
ax.boxplot(dados, tick_labels=[o.replace(" ", "\n", 1) for o in ordem], flierprops={"markersize": 2})
ax.set_ylabel("Permanência (h, cortada em 200)"); ax.set_title("Permanência no porto por tipo de navio")
salvar_fig(fig, OUT / "permanencia_por_tipo.png")

md = ["# Panorama do Porto de Barcelona — 2025\n",
      f"{len(porto)} escalas válidas em {DIAS:.0f} dias ({len(porto) / DIAS:.1f} navios/dia).\n",
      "## Por tipo de navio\n", res.to_markdown(index=False), "\n![](chegadas_por_tipo_mes.png)\n",
      "![](permanencia_por_tipo.png)\n"]
for nome, t in tops.items():
    md += [f"## Top 15 {nome}\n", t.to_markdown(index=False), ""]
(OUT / "panorama.md").write_text("\n".join(md), encoding="utf-8")
print(res.to_string())
