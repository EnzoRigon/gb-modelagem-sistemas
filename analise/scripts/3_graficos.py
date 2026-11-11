"""PASSO 3 — Gráficos do relatório e dos slides — Terminal Catalunya (TCAT), porta-contêineres.

Entrada : analise/resultados/1_dados_limpos/escalas_TCAT_conteineres.csv  (TABELA LIMPA, gerada no passo 1)
          Usa as colunas INTERVALO_CHEGADA_H, PERM_H, ESLORA_METRES, GRUPO_TAMANHO e ATIPICO_EXTREMO.

Saídas em analise/resultados/3_graficos/:
  1_hist_intervalo_chegadas.png     (obrigatório)
  2_hist_permanencia_por_tamanho.png (obrigatório)
  3_hist_comprimento.png            (obrigatório)
  4_boxplot_permanencia_tamanho.png (opcional)
  5_navios_por_mes.png              (introdução / slide de abertura)
  numeros_graficos.csv / atipicos_permanencia.csv / ajustes_permanencia.csv
"""
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from comum import RES, limites_iqr, pasta, salvar_fig

warnings.filterwarnings("ignore")
OUT = pasta("3_graficos")
CORTE = 300  # m (o mesmo usado na limpeza para GRUPO_TAMANHO)
AZUL, LARANJA, CINZA = "#3b6ea5", "#e67e22", "#7f8c8d"
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

d = pd.read_csv(RES / "1_dados_limpos" / "escalas_TCAT_conteineres.csv", parse_dates=["ETA", "ETD"])
d = d.sort_values("ETA").reset_index(drop=True)
d["GRANDE"] = d.GRUPO_TAMANHO == f">= {CORTE} m"
ROT = {False: f"< {CORTE} m", True: f"≥ {CORTE} m"}
nums = []


def lognormal_arena(x):
    """Ajusta Lognormal com offset (fração do mínimo) e devolve (dist, expressão Arena, KS p)."""
    loc = np.floor(x.min() * 0.9 * 10) / 10
    s, _, sc = stats.lognorm.fit(x, floc=loc)
    dist = stats.lognorm(s, loc, sc)
    m, dp = dist.mean() - loc, dist.std()
    return dist, f"{loc:.1f} + LOGN({m:.2f}, {dp:.2f})", stats.kstest(x, dist.cdf).pvalue


# ---------------------------------------------------------------- 1. Intervalo entre chegadas
tec = d.INTERVALO_CHEGADA_H.dropna().to_numpy()
tec_fit = np.where(tec <= 0, 0.01, tec)
c, _, sc = stats.weibull_min.fit(tec_fit, floc=0)
weib = stats.weibull_min(c, 0, sc)
expo = stats.expon(0, tec.mean())
ks_w, ks_e = stats.kstest(tec, weib.cdf).pvalue, stats.kstest(tec, expo.cdf).pvalue
fig, ax = plt.subplots(figsize=(8, 4.6))
ax.hist(tec, bins=np.arange(0, 40.5, 1.5), density=True, color="#cfd8e3", edgecolor="white",
        label=f"dados (n = {len(tec)})")
xs = np.linspace(0.05, 40, 400)
ax.plot(xs, weib.pdf(xs), color=AZUL, lw=2.4, label=f"WEIB({sc:.2f}, {c:.2f}) — KS p = {ks_w:.2f}")
ax.plot(xs, expo.pdf(xs), color=LARANJA, lw=1.4, ls="--", label=f"EXPO({tec.mean():.2f}) — KS p = {ks_e:.3f}")
ax.axvline(tec.mean(), color=CINZA, ls=":", lw=1)
ax.text(tec.mean() + .4, ax.get_ylim()[1] * .55, f"média = {tec.mean():.2f} h", color=CINZA, fontsize=9)
ax.set_xlim(0, 40)
ax.set_xlabel("Intervalo entre chegadas (h)"); ax.set_ylabel("Densidade")
ax.set_title("Intervalo entre chegadas de navios porta-contêineres — TCAT 2025")
ax.legend()
fora = (tec > 40).sum()
if fora:
    ax.text(.99, .02, f"{fora} valores > 40 h fora do gráfico", transform=ax.transAxes, ha="right",
            fontsize=8, color=CINZA)
salvar_fig(fig, OUT / "1_hist_intervalo_chegadas.png")
np.savetxt(OUT / "intervalo_chegadas_TCAT.dst", tec, fmt="%.4f")
nums += [("1", "Intervalo entre chegadas: n", len(tec)), ("1", "média (h)", tec.mean()),
         ("1", "mediana (h)", np.median(tec)), ("1", "desvio (h)", tec.std(ddof=1)),
         ("1", "CV", tec.std(ddof=1) / tec.mean()), ("1", "Weibull escala β", sc), ("1", "Weibull forma α", c),
         ("1", "KS p Weibull", ks_w), ("1", "KS p Exponencial", ks_e)]

# ---------------------------------------------------------------- 2. Permanência por tamanho
ajustes = []
fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
bins = np.arange(0, 100.5, 4)
for ax, g, cor in zip(axs, [False, True], [AZUL, LARANJA]):
    x = d.loc[d.GRANDE == g, "PERM_H"].to_numpy()
    x_fit = d.loc[(d.GRANDE == g) & ~d.ATIPICO_EXTREMO, "PERM_H"].to_numpy()   # marcação da limpeza
    dist, expr, ksp = lognormal_arena(x_fit)
    ajustes.append({"Grupo": ROT[g], "N total": len(x), "N no ajuste (sem extremos 3×IQR)": len(x_fit),
                    "Média (h)": x.mean(), "Mediana (h)": np.median(x), "Desvio (h)": x.std(ddof=1),
                    "Mín (h)": x.min(), "Máx (h)": x.max(),
                    "Média sem extremos (h)": x_fit.mean(), "Expressão Arena": expr, "KS p": ksp})
    ax.hist(x, bins=bins, density=True, color=cor, alpha=.35, edgecolor="white", label=f"dados (n = {len(x)})")
    xs = np.linspace(dist.ppf(.0005), 100, 400)
    ax.plot(xs, dist.pdf(xs), color=cor, lw=2.2, label=expr)
    ax.axvline(x.mean(), color="k", ls="--", lw=1)
    ax.text(x.mean() + 1.2, ax.get_ylim()[1] * .9 if ax.get_ylim()[1] > 0 else .05,
            f"média = {x.mean():.1f} h", fontsize=9)
    ax.set_title(f"Navios {ROT[g]}"); ax.set_xlabel("Permanência no berço (h)"); ax.set_xlim(0, 100)
    ax.legend(fontsize=8, loc="center right")
    if (x > 100).sum():
        ax.text(.99, .02, f"{(x > 100).sum()} valores > 100 h fora do gráfico", transform=ax.transAxes,
                ha="right", fontsize=8, color=CINZA)
    nums += [("2", f"Permanência {ROT[g]}: n", len(x)), ("2", f"Permanência {ROT[g]}: média (h)", x.mean()),
             ("2", f"Permanência {ROT[g]}: mediana (h)", np.median(x))]
axs[0].set_ylabel("Densidade")
fig.suptitle("Permanência no berço por tamanho de navio — TCAT 2025", fontweight="bold")
salvar_fig(fig, OUT / "2_hist_permanencia_por_tamanho.png")
xp, gp = d.loc[~d.GRANDE, "PERM_H"], d.loc[d.GRANDE, "PERM_H"]
mw = stats.mannwhitneyu(xp, gp)
nums += [("2", "Mann-Whitney p (grupos diferem?)", mw.pvalue),
         ("2", "Razão médias grande/pequeno", gp.mean() / xp.mean())]
pd.DataFrame(ajustes).round(3).to_csv(OUT / "ajustes_permanencia.csv", index=False)

# ---------------------------------------------------------------- 3. Comprimento
L = d.ESLORA_METRES.to_numpy()
p_g = (L >= CORTE).mean()
fig, ax = plt.subplots(figsize=(8, 4.6))
nb, edges, patches = ax.hist(L, bins=np.arange(90, 411, 10), color=AZUL, edgecolor="white")
for p, e in zip(patches, edges[:-1]):
    if e >= CORTE:
        p.set_facecolor(LARANJA)
ax.axvline(CORTE, color="r", ls="--", lw=2)
ymax = ax.get_ylim()[1]
ax.text(CORTE - 5, ymax * .92, f"< {CORTE} m: {100 * (1 - p_g):.1f}%\n(n = {(L < CORTE).sum()})",
        ha="right", color=AZUL, fontweight="bold")
ax.text(CORTE + 5, ymax * .92, f"≥ {CORTE} m: {100 * p_g:.1f}%\n(n = {(L >= CORTE).sum()})",
        ha="left", color=LARANJA, fontweight="bold")
ax.set_xlabel("Comprimento do navio — eslora (m)"); ax.set_ylabel("Nº de navios")
ax.set_title("Comprimento dos navios porta-contêineres — TCAT 2025")
salvar_fig(fig, OUT / "3_hist_comprimento.png")
nums += [("3", "Comprimento: n", len(L)), ("3", "média (m)", L.mean()), ("3", "mediana (m)", np.median(L)),
         ("3", "mín (m)", L.min()), ("3", "máx (m)", L.max()), ("3", "desvio (m)", L.std(ddof=1)),
         ("3", f"% navios ≥ {CORTE} m (prob. do Decide)", 100 * p_g)]

# ---------------------------------------------------------------- 4. Boxplot
fig, ax = plt.subplots(figsize=(7, 4.8))
grupos = [xp.to_numpy(), gp.to_numpy()]
bp = ax.boxplot(grupos, tick_labels=[ROT[False], ROT[True]], patch_artist=True, widths=.5,
                flierprops={"marker": "o", "markersize": 4, "markerfacecolor": "#c0392b", "alpha": .6})
for patch, cor in zip(bp["boxes"], [AZUL, LARANJA]):
    patch.set_facecolor(cor); patch.set_alpha(.45)
atip = []
for i, (x, g) in enumerate(zip(grupos, [False, True]), start=1):
    lo, hi = limites_iqr(x, 1.5)
    _, hi3 = limites_iqr(x, 3)
    n_out = int((x > hi).sum())
    ax.text(i + .28, np.median(x), f"mediana {np.median(x):.1f} h\n{n_out} atípicos", fontsize=8, va="center")
    sub = d[(d.GRANDE == g) & (d.PERM_H > hi)]
    atip.append({"Grupo": ROT[g], "Q1 (h)": np.percentile(x, 25), "Q3 (h)": np.percentile(x, 75),
                 "Limite superior 1,5×IQR (h)": hi, "Atípicos moderados": n_out,
                 "Limite superior 3×IQR (h)": hi3, "Atípicos extremos": int((x > hi3).sum()),
                 "% atípicos": 100 * n_out / len(x)})
    sub[["ESCALANUM", "VAIXELLNOM", "ESLORA_METRES", "ETA", "ETD", "PERM_H"]].assign(Grupo=ROT[g])\
        .to_csv(OUT / f"lista_atipicos_{'grandes' if g else 'pequenos'}.csv", index=False)
ax.set_ylabel("Permanência no berço (h)")
ax.set_title("Permanência por tamanho de navio — valores atípicos em vermelho")
salvar_fig(fig, OUT / "4_boxplot_permanencia_tamanho.png")
pd.DataFrame(atip).round(2).to_csv(OUT / "atipicos_permanencia.csv", index=False)

# ---------------------------------------------------------------- 5. Navios por mês
mes = d.ETA.dt.month.value_counts().reindex(range(1, 13), fill_value=0)
fig, ax = plt.subplots(figsize=(9, 4.4))
ax.plot(range(1, 13), mes.values, marker="o", color=AZUL, lw=2.2)
for m, v in mes.items():
    ax.annotate(str(v), (m, v), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9)
coef = np.polyfit(range(1, 13), mes.values, 1)
ax.plot(range(1, 13), np.polyval(coef, range(1, 13)), color=CINZA, ls="--", lw=1,
        label=f"tendência linear: +{coef[0]:.1f} navios/mês")
ax.set_xticks(range(1, 13), MESES); ax.set_ylabel("Navios atendidos")
ax.set_ylim(0, mes.max() * 1.18)
ax.set_title("Navios porta-contêineres por mês — TCAT 2025")
ax.legend(loc="lower right")
salvar_fig(fig, OUT / "5_navios_por_mes.png")
s1, s2 = mes.iloc[:6].sum(), mes.iloc[6:].sum()
nums += [("5", "Navios em jan", mes.iloc[0]), ("5", "Pico (mês)", MESES[mes.idxmax() - 1]),
         ("5", "Navios no pico", mes.max()), ("5", "Crescimento jan → pico (%)", 100 * (mes.max() / mes.iloc[0] - 1)),
         ("5", "1º semestre", s1), ("5", "2º semestre", s2), ("5", "Crescimento 2º/1º semestre (%)", 100 * (s2 / s1 - 1)),
         ("5", "Tendência (navios/mês por mês)", coef[0])]
pd.DataFrame({"Mês": MESES, "Navios": mes.values}).to_csv(OUT / "navios_por_mes.csv", index=False)

tab = pd.DataFrame(nums, columns=["Gráfico", "Indicador", "Valor"])
tab["Valor"] = [round(float(v), 4) if not isinstance(v, str) else v for v in tab["Valor"]]
tab.to_csv(OUT / "numeros_graficos.csv", index=False)
print(tab.to_string(index=False))
print(pd.DataFrame(ajustes).round(3).to_string())
print(pd.DataFrame(atip).round(2).to_string())
