"""PASSO 2 — Panorama do porto inteiro por tipo de navio (contexto para a introdução).

Entrada : analise/resultados/1_dados_limpos/escalas_porto_limpas.csv
Saídas em analise/resultados/2_panorama_porto/:
  - resumo_por_tipo_navio.csv     -> volume, ritmo de chegadas, permanência e distribuição sugerida por tipo
  - top_terminais/origens/bandeiras/consignatarios.csv
  - chegadas_por_tipo_mes.png, permanencia_por_tipo.png
  - PANORAMA.md                   -> tabelas + explicação de cada coluna
"""
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from comum import RES, limites_iqr, pasta, salvar_fig

warnings.filterwarnings("ignore")
OUT = pasta("2_panorama_porto")
porto = pd.read_csv(RES / "1_dados_limpos" / "escalas_porto_limpas.csv", parse_dates=["ETA", "ETD"],
                    low_memory=False)
DIAS = 365


def melhor_dist(x):
    """Menor erro quadrático entre EXPO, GAMM, WEIB e LOGN (sem deslocamento) -> expressão Arena."""
    x = np.where(x <= 0, 1e-2, x)
    k = min(40, max(8, int(np.ceil(np.sqrt(len(x))))))
    edges = np.linspace(x.min(), x.max(), k + 1)
    obs = np.histogram(x, edges)[0] / len(x)
    res = []
    for nome, d in [("EXPO", stats.expon), ("GAMM", stats.gamma), ("WEIB", stats.weibull_min),
                    ("LOGN", stats.lognorm)]:
        par = d.fit(x, floc=0)
        fr = d(*par)
        erro = np.sum((obs - np.diff(fr.cdf(edges))) ** 2)
        if nome == "EXPO":
            ex = f"EXPO({par[1]:.2f})"
        elif nome == "LOGN":
            ex = f"LOGN({fr.mean():.2f}, {fr.std():.2f})"
        else:
            ex = f"{nome}({par[2]:.2f}, {par[0]:.3f})"
        res.append((erro, ex))
    return min(res)[1]


linhas = []
for tipo, g in porto.groupby("TIPO_NAVIO"):
    _, sup = limites_iqr(g.PERM_H, 3)
    p = g.PERM_H[g.PERM_H <= sup]
    tec = g.ETA.sort_values().diff().dt.total_seconds().div(3600).dropna()
    term = g.TERMINALNOM[g.TERMINALNOM != "(sem terminal)"].value_counts()
    linhas.append({
        "Tipo de navio": tipo, "Escalas": len(g), "% do porto": 100 * len(g) / len(porto),
        "Chegadas/dia": len(g) / DIAS,
        "Intervalo médio entre chegadas (h)": tec.mean(), "CV do intervalo": tec.std() / tec.mean(),
        "Permanência média (h)": p.mean(), "Permanência mediana (h)": p.median(),
        "Desvio da permanência (h)": p.std(), "Atípicos extremos": int((g.PERM_H > sup).sum()),
        "Comprimento médio (m)": g.ESLORA_METRES.mean(),
        "Principal terminal": f"{term.index[0]} ({100 * term.iloc[0] / len(g):.0f}%)" if len(term) else "—",
        "Distribuição sugerida — intervalo": melhor_dist(tec.to_numpy()),
        "Distribuição sugerida — permanência": melhor_dist(p.to_numpy()),
    })
res = pd.DataFrame(linhas).sort_values("Escalas", ascending=False).round(2)
res.to_csv(OUT / "resumo_por_tipo_navio.csv", index=False)

tops = {}
for col, nome, titulo in [("TERMINALNOM", "terminais", "Terminais"), ("PORTORIGENNOM", "origens", "Portos de origem"),
                          ("VAIXELLBANDERANOM", "bandeiras", "Bandeiras (país de registro)"),
                          ("CONSIGNATARI", "consignatarios", "Consignatários (agentes)")]:
    t = porto[col].astype(str).str.strip().value_counts().head(15).rename_axis(titulo).reset_index(name="Escalas")
    t["% do porto"] = (100 * t.Escalas / len(porto)).round(2)
    t.to_csv(OUT / f"top_{nome}.csv", index=False)
    tops[titulo] = t

ordem = res["Tipo de navio"].tolist()
piv = porto.groupby(["MES", "TIPO_NAVIO"]).size().unstack(fill_value=0)[ordem]
fig, ax = plt.subplots(figsize=(11, 4.8))
piv.plot(kind="bar", stacked=True, ax=ax, width=.8, colormap="tab10")
ax.set_xticklabels(["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"], rotation=0)
ax.set_xlabel(""); ax.set_ylabel("Escalas"); ax.set_title("Escalas por mês e tipo de navio — Porto de Barcelona 2025")
ax.legend(fontsize=8, ncol=3, loc="upper left")
ax.set_ylim(0, piv.sum(axis=1).max() * 1.25)
salvar_fig(fig, OUT / "chegadas_por_tipo_mes.png")

fig, ax = plt.subplots(figsize=(11, 4.8))
ax.boxplot([porto.loc[porto.TIPO_NAVIO == t, "PERM_H"].clip(upper=200) for t in ordem],
           tick_labels=[o.replace(" ", "\n", 1) for o in ordem], flierprops={"markersize": 2})
ax.set_ylabel("Permanência (h) — valores > 200 h mostrados em 200")
ax.set_title("Permanência no porto por tipo de navio — 2025")
salvar_fig(fig, OUT / "permanencia_por_tipo.png")

pc = res.set_index("Tipo de navio")
md = f"""# Panorama do Porto de Barcelona por tipo de navio — 2025

> Gerado automaticamente por `analise/scripts/2_panorama_porto.py` a partir de
> `1_dados_limpos/escalas_porto_limpas.csv` ({len(porto):,} escalas, {len(porto) / DIAS:.1f} navios/dia).

## Para que serve

Contextualiza o recorte do modelo na introdução do relatório: mostra onde os porta-contêineres se encaixam no
movimento total do porto e por que foram escolhidos (é o 2º maior fluxo, com permanência longa e concentrada
em poucos terminais, o que favorece a formação de filas por berço).

## Resumo por tipo de navio

{res.to_markdown(index=False)}

### O que significa cada coluna

| Coluna | Significado |
|---|---|
| Tipo de navio | Classificação Lloyd's do campo `VAIXELLTIPUS`, traduzida (ver tabela de tipos abaixo) |
| Escalas | Nº de escalas (visitas ao porto) em 2025 |
| % do porto | Participação no total de escalas do porto |
| Chegadas/dia | Escalas ÷ 365: ritmo médio de chegada |
| Intervalo médio entre chegadas (h) | Tempo médio entre dois navios consecutivos do mesmo tipo |
| CV do intervalo | Coeficiente de variação (desvio ÷ média). **≈ 1** indica chegadas aleatórias (Poisson/Exponencial); **< 1**, chegadas mais regulares (linhas programadas); **> 1**, chegadas em rajadas (ex.: ferries que chegam juntos de manhã) |
| Permanência média / mediana (h) | Tempo no porto (ETD − ETA), **sem os atípicos extremos**. Média bem maior que a mediana indica cauda longa (alguns navios ficam muito tempo) |
| Desvio da permanência (h) | Dispersão da permanência (sem extremos) |
| Atípicos extremos | Escalas com permanência > Q3 + 3×IQR do próprio tipo (ex.: reparos, paradas longas); excluídas das 3 colunas anteriores |
| Comprimento médio (m) | Média da `ESLORA_METRES` |
| Principal terminal | Terminal que mais recebe esse tipo e a % das escalas do tipo que vão para ele |
| Distribuição sugerida — intervalo / permanência | Melhor ajuste automático (menor erro quadrático) entre EXPO, GAMM, WEIB e LOGN, na sintaxe do Arena. **É ponto de partida, não escolha final**: para o tipo modelado, a escolha é feita com teste de aderência e justificativa (ver `3_graficos/GRAFICOS.md`) |

Sintaxe do Arena: `EXPO(média)`, `GAMM(escala, forma)`, `WEIB(escala, forma)`, `LOGN(média, desvio)`.

## Tipos de navio (valores de `VAIXELLTIPUS`)

| Valor no CSV (catalão) | Tradução | O que é |
|---|---|---|
| Transbordadors | Ferry | Linhas regulares de passageiros + veículos (Baleares, Itália, Norte da África). Permanência curta (~{pc.loc['Ferry', 'Permanência mediana (h)']:.0f} h) |
| Portacontenidors | Porta-contêineres | Carga em contêineres movimentada por guindastes de cais. **Recorte do modelo** |
| Tancs | Navio-tanque | Produtos líquidos (químicos, combustíveis refinados) |
| Passatge | Passageiros (cruzeiro) | Navios de cruzeiro: chegam de manhã e saem à noite (~{pc.loc['Passageiros (cruzeiro)', 'Permanência mediana (h)']:.0f} h) |
| Ro-Ro | Ro-Ro | *Roll-on/roll-off*: carga sobre rodas (caminhões, semirreboques) entra/sai por rampa |
| Car-carrier | Transporte de veículos | Navios-garagem para automóveis novos |
| Càrrega (Lo-Lo) | Carga geral (Lo-Lo) | *Lift-on/lift-off*: carga geral içada por guindaste |
| Petroliers | Petroleiro | Petróleo bruto e derivados |
| Granelers | Graneleiro | Granéis sólidos (grãos, cimento, minério). Maior permanência média |

## Gráficos

![](chegadas_por_tipo_mes.png)

**Escalas por mês e tipo:** cada barra é um mês, dividida por tipo de navio. Mostra o volume total do porto e a
sazonalidade: os ferries têm pico no verão (julho–agosto) e os cruzeiros se concentram de abril a outubro, com
picos em maio e outubro. Os porta-contêineres variam menos de um mês para outro no porto inteiro.

![](permanencia_por_tipo.png)

**Permanência por tipo:** boxplot (caixa = 50% centrais, linha = mediana, pontos = atípicos). Mostra a
diferença de "tempo de serviço" entre tipos: ferries e Ro-Ro ficam poucas horas; graneleiros e tanques, dias.

"""
for titulo, t in tops.items():
    md += f"## Top 15 — {titulo}\n\n{t.to_markdown(index=False)}\n\n"
md += """### Colunas das tabelas top 15

| Coluna | Significado |
|---|---|
| 1ª coluna | Valor do campo (nome do terminal, porto de origem, país de bandeira ou empresa consignatária, como no CSV) |
| Escalas | Nº de escalas de 2025 com esse valor (todos os tipos de navio) |
| % do porto | Participação no total de escalas |

- **Bandeira** = país onde o navio está registrado; muitas são "bandeiras de conveniência" (Panamá, Libéria, Malta), por isso não indicam a nacionalidade do armador.
- **Consignatário** = agência que representa o armador no porto (trâmites, pedidos de praticagem, rebocadores, etc.).
- **(sem terminal)** = escalas sem terminal atribuído no registro.
"""
(OUT / "PANORAMA.md").write_text(md, encoding="utf-8")
print(res.iloc[:, :8].to_string(index=False))
