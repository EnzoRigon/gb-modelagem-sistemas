"""ETAPA 3 (parte 1) — Análise exploratória.

Saídas em resultados/02_descritiva/:
  - estatisticas_descritivas.csv / .md -> média, mediana, mín, máx, desvio, CV, quartis, assimetria...
  - atipicos.csv                       -> contagem de valores atípicos (1,5×IQR e 3×IQR)
  - hist_<VAR>.png                     -> histograma de cada variável
  - boxplot_por_terminal.png           -> permanência e operação por terminal
  - dispersao_eslora_permanencia.png   -> relação comprimento × tempo (justifica atributo)
  - autocorrelacao_tec.png / .csv      -> teste de independência das chegadas
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from comum import ORDEM_TERM, RES, limites_iqr, pasta, salvar_fig

OUT = pasta("02_descritiva")
VAR_DIR = RES / "01_dados" / "variaveis"
cont = pd.read_csv(RES / "01_dados" / "escalas_conteineres.csv", parse_dates=["ETA", "ETD"])

UNID = {"ESLORA": "m", "CALADO": "m"}
linhas, atip = [], []
for f in sorted(VAR_DIR.glob("*.dst")):
    nome = f.stem
    x = np.loadtxt(f)
    un = UNID.get(nome, "h")
    lo, hi = limites_iqr(x, 1.5)
    lo3, hi3 = limites_iqr(x, 3)
    linhas.append({
        "Variável": nome, "Unidade": un, "N": len(x), "Média": x.mean(), "Mediana": np.median(x),
        "Mínimo": x.min(), "Máximo": x.max(), "Desvio padrão": x.std(ddof=1),
        "CV": x.std(ddof=1) / x.mean(), "Q1": np.percentile(x, 25), "Q3": np.percentile(x, 75),
        "P95": np.percentile(x, 95), "Assimetria": stats.skew(x), "Curtose": stats.kurtosis(x)})
    atip.append({"Variável": nome, "Limite inf. 1,5×IQR": lo, "Limite sup. 1,5×IQR": hi,
                 "Atípicos moderados (1,5×IQR)": int(((x < lo) | (x > hi)).sum()),
                 "Limite sup. 3×IQR": hi3, "Atípicos extremos (3×IQR)": int(((x < lo3) | (x > hi3)).sum()),
                 "% extremos": 100 * ((x < lo3) | (x > hi3)).mean()})

    # Histograma + boxplot horizontal
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(7, 4.6), sharex=True,
                                 gridspec_kw={"height_ratios": [4, 1]})
    bins = min(40, max(10, int(np.sqrt(len(x)))))
    ax.hist(x, bins=bins, color="#3b6ea5", edgecolor="white")
    ax.axvline(x.mean(), color="#c0392b", ls="--", label=f"média = {x.mean():.2f}")
    ax.axvline(np.median(x), color="#27ae60", ls=":", label=f"mediana = {np.median(x):.2f}")
    ax.set_ylabel("Frequência")
    ax.set_title(f"{nome} — n = {len(x)}")
    ax.legend()
    bx.boxplot(x, orientation="horizontal", widths=.6, flierprops={"markersize": 3})
    bx.set_yticks([])
    bx.set_xlabel(f"{nome} ({un})")
    salvar_fig(fig, OUT / f"hist_{nome}.png")

desc = pd.DataFrame(linhas).round(3)
atip = pd.DataFrame(atip).round(3)
desc.to_csv(OUT / "estatisticas_descritivas.csv", index=False)
atip.to_csv(OUT / "atipicos.csv", index=False)

# Boxplot por terminal (com e sem atípicos de permanência)
fig, axs = plt.subplots(1, 2, figsize=(10, 4))
for ax, col, tit in [(axs[0], "PERM_H", "Permanência no porto (h) — todos"),
                     (axs[1], "OPER_H", "Operação no cais (h) — sem atípicos")]:
    d = cont if col == "PERM_H" else cont[~cont.OUTLIER_PERM]
    ax.boxplot([d.loc[d.TERMINAL == t, col] for t in ORDEM_TERM], tick_labels=ORDEM_TERM,
               flierprops={"markersize": 3})
    ax.set_title(tit)
salvar_fig(fig, OUT / "boxplot_por_terminal.png")

# Teste: as distribuições de operação diferem entre terminais? (Kruskal-Wallis)
ok = cont[~cont.OUTLIER_PERM]
kw = stats.kruskal(*[ok.loc[ok.TERMINAL == t, "OPER_H"] for t in ORDEM_TERM])

# Comprimento × permanência
r, p_r = stats.spearmanr(ok["ESLORA_METRES"], ok["OPER_H"])
fig, ax = plt.subplots(figsize=(6.5, 4.2))
for t, c in zip(ORDEM_TERM, ["#3b6ea5", "#e67e22", "#27ae60"]):
    d = ok[ok.TERMINAL == t]
    ax.scatter(d.ESLORA_METRES, d.OPER_H, s=8, alpha=.5, label=t, color=c)
ax.set_xlabel("Eslora (m)"); ax.set_ylabel("Operação no cais (h)")
ax.set_title(f"Eslora × operação — Spearman ρ = {r:.2f}")
ax.legend()
salvar_fig(fig, OUT / "dispersao_eslora_operacao.png")

# Independência das chegadas: autocorrelação dos tempos entre chegadas
tec = np.loadtxt(VAR_DIR / "TEC_GERAL.dst")
lags = range(1, 21)
acf = [pd.Series(tec).autocorr(k) for k in lags]
lim = 1.96 / np.sqrt(len(tec))
pd.DataFrame({"lag": lags, "autocorrelacao": acf, "limite_95%": lim}).round(4)\
    .to_csv(OUT / "autocorrelacao_tec.csv", index=False)
fig, ax = plt.subplots(figsize=(6.5, 3.5))
ax.bar(lags, acf, color="#3b6ea5")
ax.axhline(lim, color="r", ls="--"); ax.axhline(-lim, color="r", ls="--")
ax.set_xlabel("Defasagem (lag)"); ax.set_ylabel("Autocorrelação")
ax.set_title("Autocorrelação do tempo entre chegadas (faixa = IC 95%)")
salvar_fig(fig, OUT / "autocorrelacao_tec.png")

md = ["# Estatística descritiva\n",
      "## Medidas por variável\n", desc.to_markdown(index=False),
      "\n## Valores atípicos (regra de Tukey)\n", atip.to_markdown(index=False),
      "\n> Nas variáveis PERM/OPER os atípicos extremos de permanência (3×IQR por terminal) já foram"
      " retirados no script 01 (ver `01_dados/log_limpeza.md`). Os restantes são estadias longas,"
      " porém plausíveis, e foram mantidos.",
      "\n## Testes complementares\n",
      f"- **Diferença entre terminais (Kruskal-Wallis, operação no cais):** H = {kw.statistic:.2f}, "
      f"p = {kw.pvalue:.3g} → {'diferem; usar uma distribuição por terminal' if kw.pvalue < .05 else 'não diferem; pode usar distribuição única'}.",
      f"- **Correlação eslora × operação (Spearman):** ρ = {r:.3f}, p = {p_r:.3g}. "
      + ("Correlação fraca: o comprimento quase não influencia o tempo de operação." if abs(r) < .3 else
         "Correlação moderada: navios maiores tendem a operar mais tempo (mais contêineres). Parte desse efeito já "
         "aparece na diferença entre terminais; no modelo, a eslora entra como atributo (nº de rebocadores). "
         "Como melhoria, a operação poderia ser sorteada por classe de eslora (limitação a citar no relatório)."
         if abs(r) < .6 else "Correlação forte: considerar distribuição de operação por classe de eslora."),
      f"- **Autocorrelação dos tempos entre chegadas:** {sum(abs(a) > lim for a in acf)} de 20 lags fora do IC 95% "
      f"(lag 1 = {acf[0]:.3f}). Valores próximos de zero sustentam a hipótese de chegadas independentes (processo de Poisson)."]
(OUT / "estatisticas_descritivas.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(md))
