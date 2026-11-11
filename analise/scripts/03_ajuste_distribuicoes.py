"""ETAPA 3 (parte 2) — Ajuste e escolha de distribuições de probabilidade.

Para cada variável testa várias distribuições, calcula as mesmas métricas do
Arena Input Analyzer (erro quadrático) + Qui-quadrado, Kolmogorov-Smirnov e AIC,
e escolhe a distribuição combinando TEORIA (o que faz sentido para o fenômeno)
e QUALIDADE DO AJUSTE — não só o menor erro.

Saídas em resultados/03_ajuste/:
  - ranking_<VAR>.csv          -> todas as distribuições testadas e métricas
  - ajuste_<VAR>.png           -> histograma + curvas, Q-Q plot e CDF da escolhida
  - distribuicoes_escolhidas.csv / .md -> expressão Arena final + justificativa
"""
import math
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from comum import RES, pasta, salvar_fig

warnings.filterwarnings("ignore")
OUT = pasta("03_ajuste")
VAR_DIR = RES / "01_dados" / "variaveis"


# ---------------------------------------------------------------------------
# Conversão scipy -> sintaxe Arena
# ---------------------------------------------------------------------------
def off(loc):
    return f"{loc:.3f} + " if abs(loc) > 1e-9 else ""


def arena_expr(nome, p):
    if nome == "EXPO":
        return f"{off(p['loc'])}EXPO({p['scale']:.3f})"
    if nome == "GAMM":
        return f"{off(p['loc'])}GAMM({p['scale']:.3f}, {p['a']:.3f})"
    if nome == "ERLA":
        return f"{off(p['loc'])}ERLA({p['scale']:.3f}, {int(p['a'])})"
    if nome == "WEIB":
        return f"{off(p['loc'])}WEIB({p['scale']:.3f}, {p['c']:.3f})"
    if nome == "LOGN":
        s, sc = p["s"], p["scale"]
        m = sc * math.exp(s ** 2 / 2)
        dp = m * math.sqrt(math.exp(s ** 2) - 1)
        return f"{off(p['loc'])}LOGN({m:.3f}, {dp:.3f})"
    if nome == "NORM":
        return f"NORM({p['loc']:.3f}, {p['scale']:.3f})"
    if nome == "TRIA":
        a, b = p["loc"], p["loc"] + p["scale"]
        return f"TRIA({a:.3f}, {a + p['c'] * p['scale']:.3f}, {b:.3f})"
    if nome == "UNIF":
        return f"UNIF({p['loc']:.3f}, {p['loc'] + p['scale']:.3f})"
    if nome == "BETA":
        return f"{p['loc']:.3f} + {p['scale']:.3f} * BETA({p['a']:.3f}, {p['b']:.3f})"
    raise ValueError(nome)


SCIPY = {"EXPO": stats.expon, "GAMM": stats.gamma, "ERLA": stats.gamma, "WEIB": stats.weibull_min,
         "LOGN": stats.lognorm, "NORM": stats.norm, "TRIA": stats.triang, "UNIF": stats.uniform,
         "BETA": stats.beta}
NPAR = {"EXPO": 1, "GAMM": 2, "ERLA": 2, "WEIB": 2, "LOGN": 2, "NORM": 2, "TRIA": 3, "UNIF": 2, "BETA": 4}


def ajustar(nome, x, loc):
    """Retorna (dist congelada, dict de parâmetros)."""
    d = SCIPY[nome]
    xp = np.where(x - loc <= 0, loc + 1e-2, x)  # zeros quebram log-verossimilhança
    if nome == "EXPO":
        par = d.fit(xp, floc=loc)
        p = {"loc": par[0], "scale": par[1]}
    elif nome in ("GAMM", "ERLA"):
        a, l, sc = d.fit(xp, floc=loc)
        if nome == "ERLA":
            k = max(1, round(a))
            a, sc = k, (xp.mean() - loc) / k
        p = {"a": a, "loc": l, "scale": sc}
    elif nome == "WEIB":
        c, l, sc = d.fit(xp, floc=loc)
        p = {"c": c, "loc": l, "scale": sc}
    elif nome == "LOGN":
        s, l, sc = d.fit(xp, floc=loc)
        p = {"s": s, "loc": l, "scale": sc}
    elif nome == "NORM":
        l, sc = d.fit(x)
        p = {"loc": l, "scale": sc}
    elif nome == "UNIF":
        p = {"loc": x.min(), "scale": x.max() - x.min()}
    elif nome == "TRIA":
        lo, hi = x.min(), x.max()
        c, l, sc = d.fit(x, loc=lo, scale=hi - lo)
        p = {"c": c, "loc": l, "scale": sc}
    elif nome == "BETA":
        lo, hi = x.min(), x.max()
        span = hi - lo
        a, b, l, sc = d.fit(x, floc=lo - .001 * span, fscale=span * 1.002)
        p = {"a": a, "b": b, "loc": l, "scale": sc}
    frozen = d(**{k: v for k, v in p.items()})
    return frozen, p


def metricas(x, dist, npar):
    n = len(x)
    k = min(40, max(8, int(math.ceil(math.sqrt(n)))))
    edges = np.linspace(x.min(), x.max(), k + 1)
    obs, _ = np.histogram(x, edges)
    pr = np.diff(dist.cdf(edges))
    sq = float(np.sum((obs / n - pr) ** 2))                      # erro quadrático (Input Analyzer)
    # Qui-quadrado: agrupa classes até esperado >= 5
    edges_ext = edges.copy(); edges_ext[0], edges_ext[-1] = -np.inf, np.inf
    esp = np.diff(dist.cdf(edges_ext)) * n
    o_g, e_g, ao, ae = [], [], 0, 0
    for o, e in zip(obs, esp):
        ao += o; ae += e
        if ae >= 5:
            o_g.append(ao); e_g.append(ae); ao = ae = 0
    if ae > 0 and o_g:
        o_g[-1] += ao; e_g[-1] += ae
    chi = float(np.sum((np.array(o_g) - np.array(e_g)) ** 2 / np.array(e_g)))
    gl = max(1, len(o_g) - 1 - npar)
    p_chi = float(stats.chi2.sf(chi, gl))
    ks = stats.kstest(x, dist.cdf)
    ll = np.sum(dist.logpdf(x))
    aic = 2 * npar - 2 * ll if np.isfinite(ll) else np.inf
    return {"Erro quadrático": sq, "Qui² estat.": chi, "Qui² gl": gl, "Qui² p-valor": p_chi,
            "KS estat.": ks.statistic, "KS p-valor": ks.pvalue, "AIC": aic}


def empirica_cont(x, n_pontos=11):
    """Distribuição empírica contínua do Arena: CONT(prob_acum, valor, ...)."""
    ps = np.linspace(0, 1, n_pontos)
    qs = np.quantile(x, ps)
    return "CONT(" + ", ".join(f"{p:.2f}, {q:.2f}" for p, q in zip(ps, qs)) + ")"


# ---------------------------------------------------------------------------
# Candidatas e justificativa teórica por tipo de variável
# ---------------------------------------------------------------------------
TEORIA = {
    "TEC": dict(
        cand=["EXPO", "ERLA", "GAMM", "WEIB", "LOGN"],
        plaus=["EXPO", "ERLA", "GAMM", "WEIB"],
        pref="EXPO",
        txt=("Tempo entre chegadas de navios vindos de portos e armadores diferentes, de forma independente "
             "(autocorrelação ≈ 0). A teoria de filas indica processo de Poisson → Exponencial, cujo CV = 1. ")),
    "OPER": dict(
        cand=["GAMM", "ERLA", "WEIB", "LOGN", "EXPO", "NORM"],
        plaus=["GAMM", "ERLA", "WEIB", "LOGN"],
        pref=None, empirica=True,
        txt=("Tempo de serviço positivo, com mínimo físico (sempre há algumas horas de carga/descarga) e "
             "cauda à direita (navios com muitos contêineres). Famílias adequadas: Gama/Erlang, Weibull e "
             "Lognormal com deslocamento (offset). Normal é inadequada (assimetria) e Exponencial supõe moda em 0. ")),
    "PERM": dict(
        cand=["GAMM", "ERLA", "WEIB", "LOGN", "EXPO", "NORM"],
        plaus=["GAMM", "ERLA", "WEIB", "LOGN"], pref=None,
        txt="Mesma justificativa da operação no cais (é a operação + manobras). Usada como referência de validação. "),
    "ESLORA": dict(
        cand=["BETA", "TRIA", "NORM", "UNIF", "WEIB"],
        plaus=["BETA", "TRIA", "NORM", "UNIF"], pref=None, empirica=True,
        txt=("Variável limitada (navios entre ~100 e 400 m) e com mais de uma moda (feeders pequenos e navios "
             "oceânicos grandes). Distribuições limitadas (Beta/Triangular) são as candidatas teóricas; "
             "se nenhuma reproduzir a forma, a empírica contínua (CONT) é a escolha mais fiel. ")),
    "CALADO": dict(
        cand=["BETA", "TRIA", "NORM", "UNIF", "WEIB"],
        plaus=["BETA", "TRIA", "NORM", "UNIF"], pref=None, empirica=True,
        txt="Variável física limitada pela profundidade do canal/cais; mesma lógica da eslora. "),
    "MANOBRA": dict(
        cand=["NORM", "TRIA", "BETA", "LOGN", "GAMM", "WEIB"],
        plaus=["NORM", "TRIA", "BETA", "LOGN", "GAMM", "WEIB"], pref=None,
        txt=("Dado SINTÉTICO (ver 01_dados/log_limpeza.md). Tempo de tarefa com mínimo e máximo práticos; "
             "Triangular/Beta são clássicas para tempos de atividade estimados por especialistas. ")),
}


def grupo(nome):
    return next(k for k in TEORIA if nome.startswith(k))


escolhas = []
for f in sorted(VAR_DIR.glob("*.dst")):
    nome = f.stem
    x = np.loadtxt(f)
    g = TEORIA[grupo(nome)]
    un = "m" if grupo(nome) in ("ESLORA", "CALADO") else "h"

    # Offset: fração do mínimo observado (como o Input Analyzer faz quando min > 0)
    offsets = [0.0]
    if x.min() > 0.5 and grupo(nome) in ("OPER", "PERM", "TEC"):
        offsets.append(math.floor(x.min() * 0.9 * 10) / 10)

    res, frozen = [], {}
    for d in g["cand"]:
        for loc in (offsets if d in ("EXPO", "GAMM", "ERLA", "WEIB", "LOGN") else [None]):
            try:
                dist, p = ajustar(d, x, loc or 0.0)
                m = metricas(x, dist, NPAR[d] + (1 if loc else 0))
            except Exception as e:  # noqa: BLE001
                print(f"  {nome}/{d}: falhou ({e})")
                continue
            expr = arena_expr(d, p)
            frozen[expr] = dist
            res.append({"Distribuição": d, "Offset": loc or 0.0, "Expressão Arena": expr,
                        "Média teórica": dist.mean(), **m})
    rk = pd.DataFrame(res).sort_values("Erro quadrático").reset_index(drop=True)
    rk.insert(0, "Rank (erro quadr.)", rk.index + 1)
    rk.round(5).to_csv(OUT / f"ranking_{nome}.csv", index=False)

    # ---- Escolha: teoria primeiro, métrica depois -------------------------
    plaus = rk[rk["Distribuição"].isin(g["plaus"])]
    melhor = plaus.iloc[0]
    escolhida, motivo = melhor, ""
    cv = x.std(ddof=1) / x.mean()
    if g["pref"]:
        pref = plaus[plaus["Distribuição"] == g["pref"]].iloc[0]
        # aceita a preferida teórica se CV ≈ 1 e ela NÃO for rejeitada a 5% (KS ou Qui²)
        passa = pref["KS p-valor"] >= .05 or pref["Qui² p-valor"] >= .05
        if 0.8 <= cv <= 1.2 and (passa or pref["Erro quadrático"] <= 2 * melhor["Erro quadrático"]):
            escolhida = pref
            teste = (f"não é rejeitada a 5% (KS p = {pref['KS p-valor']:.3f}; "
                     f"Qui² p = {pref['Qui² p-valor']:.3f})" if passa else "tem erro próximo do melhor")
            motivo = (f"CV observado = {cv:.2f} (≈1); a Exponencial {teste}. "
                      f"{melhor['Distribuição']} tem erro um pouco menor ({melhor['Erro quadrático']:.5f} vs "
                      f"{pref['Erro quadrático']:.5f}), mas com forma ≈ 1 ela é praticamente uma Exponencial; "
                      "preferida por coerência teórica e parcimônia (1 parâmetro, fácil de alterar nos cenários de demanda).")
        elif 0.8 <= cv <= 1.2:
            motivo = (f"CV observado = {cv:.2f}, próximo de 1, mas a Exponencial é rejeitada "
                      f"(KS p = {pref['KS p-valor']:.3g}; Qui² p = {pref['Qui² p-valor']:.3g}) e tem erro "
                      f"{pref['Erro quadrático'] / melhor['Erro quadrático']:.1f}× maior. "
                      f"{melhor['Distribuição']} (forma levemente > 1) indica chegadas um pouco mais regulares "
                      "que Poisson, coerente com escalas de linhas regulares programadas. "
                      f"Alternativa simplificada aceitável: EXPO({x.mean():.3f}).")
        else:
            motivo = (f"CV observado = {cv:.2f} (≠1): chegadas mais regulares que Poisson, típico de "
                      "linhas regulares com janelas de atracação programadas; por isso "
                      f"{melhor['Distribuição']} (forma > 1) representa melhor que a Exponencial.")
    if not motivo:
        motivo = (f"Menor erro quadrático entre as famílias teoricamente adequadas "
                  f"({escolhida['Erro quadrático']:.5f}); AIC = {escolhida['AIC']:.1f}.")

    expr_final = escolhida["Expressão Arena"]
    dist_final = frozen[expr_final]
    if g.get("empirica"):
        emp = empirica_cont(x)
        # Se a melhor paramétrica é rejeitada nos dois testes, usa empírica
        if escolhida["Qui² p-valor"] < 0.01 and escolhida["KS p-valor"] < 0.05:
            motivo = (f"Nenhuma paramétrica reproduz a forma (melhor: {escolhida['Distribuição']}, "
                      f"qui² p = {escolhida['Qui² p-valor']:.2g}); usa-se a distribuição EMPÍRICA contínua "
                      f"construída pelos decis observados. Alternativa paramétrica: {expr_final}.")
            expr_final = emp
    n = len(x)
    nota_n = (" Com n grande os testes de aderência rejeitam até desvios pequenos; por isso a decisão "
              "também considera o erro quadrático, o Q-Q plot e a coerência teórica." if n > 500 else "")
    escolhas.append({"Variável": nome, "Unidade": un, "N": n, "Média obs.": x.mean(),
                     "Distribuição": escolhida["Distribuição"] if not expr_final.startswith("CONT") else "Empírica (CONT)",
                     "Expressão Arena": expr_final,
                     "Erro quadrático": escolhida["Erro quadrático"], "Qui² p": escolhida["Qui² p-valor"],
                     "KS p": escolhida["KS p-valor"],
                     "Justificativa": g["txt"] + motivo + nota_n})

    # ---- Gráficos --------------------------------------------------------
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
    bins = min(40, max(10, int(np.sqrt(n))))
    axs[0].hist(x, bins=bins, density=True, color="#cfd8e3", edgecolor="white", label="dados")
    xs = np.linspace(x.min(), x.max(), 400)
    for i, (_, r) in enumerate(plaus.head(3).iterrows()):
        axs[0].plot(xs, frozen[r["Expressão Arena"]].pdf(xs), lw=2 if i == 0 else 1.2,
                    label=f"{r['Distribuição']} (erro {r['Erro quadrático']:.4f})")
    axs[0].set_title(f"{nome}: histograma e densidades ajustadas"); axs[0].legend(fontsize=8)
    axs[0].set_xlabel(un)
    q_teo = dist_final.ppf((np.arange(1, n + 1) - .5) / n)
    axs[1].scatter(q_teo, np.sort(x), s=5, color="#3b6ea5")
    lim = [min(q_teo.min(), x.min()), max(q_teo.max(), x.max())]
    axs[1].plot(lim, lim, "r--")
    axs[1].set_title(f"Q-Q plot — {escolhida['Distribuição']}")
    axs[1].set_xlabel("Quantil teórico"); axs[1].set_ylabel("Quantil observado")
    axs[2].step(np.sort(x), np.arange(1, n + 1) / n, where="post", label="empírica")
    axs[2].plot(xs, dist_final.cdf(xs), "r", label=escolhida["Distribuição"])
    axs[2].set_title("Função de distribuição acumulada"); axs[2].legend()
    salvar_fig(fig, OUT / f"ajuste_{nome}.png")
    print(f"{nome:16s} -> {expr_final}")

esc = pd.DataFrame(escolhas)
esc.round(5).to_csv(OUT / "distribuicoes_escolhidas.csv", index=False)
md = ["# Distribuições escolhidas para o Arena\n",
      "Parametrização do Arena: `EXPO(média)`, `GAMM(escala β, forma α)`, `ERLA(média de cada fase, k)`, "
      "`WEIB(escala β, forma α)`, `LOGN(média, desvio)` (da própria variável, não do log), "
      "`NORM(média, desvio)`, `TRIA(mín, moda, máx)`, `BETA(β, α)` em [0,1] reescalada, "
      "`CONT(prob. acumulada, valor, ...)` empírica.\n",
      "| Variável | N | Média obs. | Distribuição | Expressão Arena | Erro quadr. | Qui² p | KS p |",
      "|---|---|---|---|---|---|---|---|"]
for _, r in esc.iterrows():
    md.append(f"| {r['Variável']} | {r['N']} | {r['Média obs.']:.3f} {r['Unidade']} | {r['Distribuição']} | "
              f"`{r['Expressão Arena']}` | {r['Erro quadrático']:.5f} | {r['Qui² p']:.3g} | {r['KS p']:.3g} |")
md.append("\n## Justificativas\n")
for _, r in esc.iterrows():
    md.append(f"### {r['Variável']}\n\n{r['Justificativa']}\n\n![ajuste](ajuste_{r['Variável']}.png)\n")
(OUT / "distribuicoes_escolhidas.md").write_text("\n".join(md), encoding="utf-8")
