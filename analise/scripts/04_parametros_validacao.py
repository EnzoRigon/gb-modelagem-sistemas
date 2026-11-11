"""ETAPAS 4, 5 e 7 — Parâmetros do modelo, referências de validação e base dos cenários.

Saídas em resultados/04_parametros/:
  - prob_terminal.csv              -> probabilidades do Decide "Qual terminal?"
  - prob_classe_eslora.csv         -> % de navios por classe (nº de rebocadores) em cada terminal
  - ocupacao_simultanea.csv        -> nº de navios ao mesmo tempo em cada terminal (dimensiona os berços)
  - ocupacao_serie.png / _hist.png -> gráficos da ocupação
  - perfil_chegadas_hora/dia/mes.* -> sazonalidade (justifica taxa constante ou Schedule)
  - validacao_referencia.csv       -> indicadores reais por 30 dias (comparar com o cenário A no Arena)
  - lei_little.csv                 -> verificação L = λ·W
  - demanda_rebocadores.csv        -> carga de trabalho de práticos e rebocadores
  - parametros_arena.md            -> FICHA FINAL: tudo que entra no Arena, módulo a módulo
"""
import numpy as np
import pandas as pd
from scipy import stats

from comum import CLASSES_ESLORA, ORDEM_TERM, RES, pasta, salvar_fig
import matplotlib.pyplot as plt

OUT = pasta("04_parametros")
cont = pd.read_csv(RES / "01_dados" / "escalas_conteineres.csv", parse_dates=["ETA", "ETD"])
esc = pd.read_csv(RES / "03_ajuste" / "distribuicoes_escolhidas.csv").set_index("Variável")
ok = cont[~cont.OUTLIER_PERM]
DIAS = (cont.ETA.max() - cont.ETA.min()).total_seconds() / 86400
CORES = dict(zip(ORDEM_TERM, ["#3b6ea5", "#e67e22", "#27ae60"]))

# 1) Decisão: terminal --------------------------------------------------------
pt = cont.TERMINAL.value_counts().reindex(ORDEM_TERM)
prob_term = pd.DataFrame({"Terminal": pt.index, "Escalas": pt.values,
                          "Probabilidade (%)": (100 * pt / pt.sum()).round(2).values,
                          "Chegadas/dia": (pt / DIAS).round(3).values})
prob_term.to_csv(OUT / "prob_terminal.csv", index=False)

# 2) Classes de eslora -> nº de rebocadores (hipótese) ------------------------
cl = pd.crosstab(cont.TERMINAL, cont.CLASSE, normalize="index").reindex(ORDEM_TERM) * 100
cl = cl[[c[2] for c in CLASSES_ESLORA]].round(2)
cl["Rebocadores médios"] = (cont.groupby("TERMINAL").N_REBOC.mean().reindex(ORDEM_TERM)).round(2)
cl.to_csv(OUT / "prob_classe_eslora.csv")
p_cl_geral = (cont.CLASSE.value_counts(normalize=True)[[c[2] for c in CLASSES_ESLORA]] * 100).round(2)

# 3) Ocupação simultânea (varredura de eventos) ------------------------------
ini, fim = pd.Timestamp("2025-01-15"), pd.Timestamp("2025-12-15")   # evita efeito de borda
ocup_rows, series = [], {}
grade = pd.date_range(ini, fim, freq="10min")
for t in ORDEM_TERM:
    d = ok[ok.TERMINAL == t]
    n = np.zeros(len(grade), dtype=int)
    for a, b in zip(d.ETA.values, d.ETD.values):
        n[(grade >= a) & (grade < b)] += 1
    series[t] = n
    ocup_rows.append({"Terminal": t, "Média": n.mean(), "Mediana": np.median(n), "P90": np.percentile(n, 90),
                      "P95": np.percentile(n, 95), "P99": np.percentile(n, 99), "Máximo": n.max(),
                      **{f"% tempo com ≥{k}": 100 * (n >= k).mean() for k in range(1, 7)},
                      "Berços sugeridos (P99 arred.)": int(np.ceil(np.percentile(n, 99)))})
ocup = pd.DataFrame(ocup_rows).round(2)
ocup.to_csv(OUT / "ocupacao_simultanea.csv", index=False)
BERCOS = dict(zip(ocup.Terminal, ocup["Berços sugeridos (P99 arred.)"]))

fig, axs = plt.subplots(3, 1, figsize=(11, 6.5), sharex=True)
jan = (grade >= "2025-06-01") & (grade < "2025-07-01")
for ax, t in zip(axs, ORDEM_TERM):
    ax.step(grade[jan], series[t][jan], where="post", color=CORES[t])
    ax.axhline(BERCOS[t], color="r", ls="--", lw=1, label=f"berços sugeridos = {BERCOS[t]}")
    ax.set_ylabel(f"{t}\nnavios"); ax.legend(loc="upper right", fontsize=8)
axs[0].set_title("Navios simultaneamente no terminal — junho/2025 (dados reais)")
fig.autofmt_xdate()
salvar_fig(fig, OUT / "ocupacao_serie_junho.png")

fig, ax = plt.subplots(figsize=(7, 4))
w = .27
for i, t in enumerate(ORDEM_TERM):
    v = pd.Series(series[t]).value_counts(normalize=True).sort_index()
    ax.bar(v.index + (i - 1) * w, 100 * v.values, width=w, label=t, color=CORES[t])
ax.set_xlabel("Nº de navios simultâneos"); ax.set_ylabel("% do tempo"); ax.legend()
ax.set_title("Distribuição da ocupação dos terminais")
salvar_fig(fig, OUT / "ocupacao_hist.png")

# 4) Perfil de chegadas -------------------------------------------------------
h = cont.ETA.dt.hour.value_counts().reindex(range(24), fill_value=0)
dsem = cont.ETA.dt.day_of_week.value_counts().reindex(range(7), fill_value=0)
mes = cont.ETA.dt.month.value_counts().reindex(range(1, 13), fill_value=0)
chi_h = stats.chisquare(h); chi_d = stats.chisquare(dsem)
dias_mes = cont.ETA.dt.to_period("M").value_counts().sort_index().index.days_in_month
taxa_mes = mes.values / dias_mes.values
chi_m = stats.chisquare(mes, mes.sum() * dias_mes.values / dias_mes.values.sum())
perfil_h = pd.DataFrame({"Hora": h.index, "Chegadas no ano": h.values,
                         "Taxa média (navios/h)": (h.values / DIAS).round(4)})
perfil_h.to_csv(OUT / "perfil_chegadas_hora.csv", index=False)
pd.DataFrame({"Dia": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"], "Chegadas": dsem.values})\
    .to_csv(OUT / "perfil_chegadas_dia_semana.csv", index=False)
pd.DataFrame({"Mês": range(1, 13), "Chegadas": mes.values, "Chegadas/dia": taxa_mes.round(3)})\
    .to_csv(OUT / "perfil_chegadas_mes.csv", index=False)
fig, axs = plt.subplots(1, 3, figsize=(15, 3.8))
axs[0].bar(h.index, h.values, color="#3b6ea5"); axs[0].set_title(f"Por hora do dia (χ² p = {chi_h.pvalue:.2g})")
axs[0].set_xlabel("Hora")
axs[1].bar(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"], dsem.values, color="#3b6ea5")
axs[1].set_title(f"Por dia da semana (χ² p = {chi_d.pvalue:.2g})")
axs[2].bar(range(1, 13), taxa_mes, color="#3b6ea5"); axs[2].set_xticks(range(1, 13))
axs[2].axhline(len(cont) / DIAS, color="r", ls="--", label="média anual")
axs[2].set_title(f"Chegadas/dia por mês (χ² p = {chi_m.pvalue:.2g})"); axs[2].legend()
for a in axs: a.set_ylabel("Chegadas")
salvar_fig(fig, OUT / "perfil_chegadas.png")

# 5) Referência de validação (por janelas de 30 dias) --------------------------
cont["JANELA"] = ((cont.ETA - cont.ETA.min()).dt.days // 30)
jan_ok = cont[cont.JANELA < 12]                                      # 12 janelas completas
ref = []
for t in ORDEM_TERM + ["TOTAL"]:
    d = jan_ok if t == "TOTAL" else jan_ok[jan_ok.TERMINAL == t]
    dk = ok if t == "TOTAL" else ok[ok.TERMINAL == t]
    cnt = d.groupby("JANELA").size().reindex(range(12), fill_value=0)
    L = sum(series[x].mean() for x in ORDEM_TERM) if t == "TOTAL" else series[t].mean()
    ref.append({"Terminal": t, "Navios atendidos / 30 dias (média)": cnt.mean(),
                "Desvio entre janelas": cnt.std(), "Mín.": cnt.min(), "Máx.": cnt.max(),
                "Permanência média (h)": dk.PERM_H.mean(), "Permanência mediana (h)": dk.PERM_H.median(),
                "Operação média (h)": dk.OPER_H.mean(),
                "Navios simultâneos (média)": L,
                "Utilização dos berços (%) c/ berços sugeridos":
                    100 * L / (sum(BERCOS.values()) if t == "TOTAL" else BERCOS[t])})
ref = pd.DataFrame(ref).round(2)
ref.to_csv(OUT / "validacao_referencia.csv", index=False)

# 6) Lei de Little: L = λ·W -----------------------------------------------------
lit = []
for t in ORDEM_TERM:
    dk = ok[(ok.TERMINAL == t) & (ok.ETA >= ini) & (ok.ETA < fim)]
    lam = len(dk) / ((fim - ini).total_seconds() / 3600)
    W = dk.PERM_H.mean()
    lit.append({"Terminal": t, "λ (navios/h)": lam, "W (h)": W, "λ·W": lam * W,
                "L medido": series[t].mean(), "Diferença (%)": 100 * (lam * W / series[t].mean() - 1)})
lit = pd.DataFrame(lit).round(4)
lit.to_csv(OUT / "lei_little.csv", index=False)

# 7) Demanda de práticos e rebocadores ----------------------------------------
lam_dia = len(cont) / DIAS
man_media = cont.MAN_ENT_H.mean() + cont.MAN_SAI_H.mean()
reboc_h = (cont.N_REBOC * (cont.MAN_ENT_H + cont.MAN_SAI_H)).sum() / DIAS
prat_h = lam_dia * man_media
dem = pd.DataFrame([
    {"Recurso": "Prático", "Horas de trabalho/dia": prat_h,
     **{f"Utilização c/ {c}": 100 * prat_h / (24 * c) for c in (1, 2, 3)}},
    {"Recurso": "Rebocador", "Horas de trabalho/dia": reboc_h,
     **{f"Utilização c/ {c}": 100 * reboc_h / (24 * c) for c in (3, 4, 6)}},
]).round(2)
dem.to_csv(OUT / "demanda_rebocadores.csv", index=False)

# 8) FICHA DO ARENA -------------------------------------------------------------
E = esc["Expressão Arena"]
tec_mean = esc.loc["TEC_GERAL", "Média obs."]
md = f"""# Ficha de parâmetros para o Arena

> Gerada automaticamente por `04_parametros_validacao.py`. Unidade de tempo base: **horas**.
> Fonte: escalas reais do Porto de Barcelona (2025), recorte de porta-contêineres em 3 terminais
> ({len(cont)} escalas, {DIAS:.0f} dias). Itens marcados com **[H]** são hipóteses/sintéticos.

## 1. Estrutura sugerida do modelo

```
Create "Chegada de navios"  --> Assign atributos --> Decide "Qual terminal?" (N-way by chance)
   |                                                 |-- TCAT --|
   |                                                 |-- APM  --|--> Seize "Berço_<terminal>"   (fila = fundeadouro)
   |                                                 |-- PNOU --|
   --> Process "Manobra de entrada"  (Seize Prático + N_REBOC Rebocadores, Delay, Release)
   --> Process "Operação no cais"    (Delay pela distribuição do terminal)
   --> Process "Manobra de saída"    (Seize Prático + N_REBOC Rebocadores, Delay, Release)
   --> Release "Berço_<terminal>" --> Record (tempo no sistema, espera no fundeadouro, contadores)
   --> Dispose "Saída do porto"
```

- **Processos (≥3):** manobra de entrada, operação no cais, manobra de saída.
- **Recursos (≥2 tipos):** Berço_TCAT, Berço_APM, Berço_PNOU, Prático, Rebocador.
- **Fila:** espera por berço = navio fundeado aguardando cais livre (+ fila por prático/rebocador).
- **Decisões:** (1) terminal de destino, por probabilidade; (2) nº de rebocadores pela eslora (por condição).
- **Assign:** atributos `Eslora`, `Terminal`, `N_Reboc`, `T_Chegada = TNOW`; variáveis `NaviosNoPorto`.
- **Record:** `TNOW - T_Chegada` (tempo no porto), tempo de espera por berço, contagem por terminal.

## 2. Chegadas (Create)

| Parâmetro | Valor | Origem |
|---|---|---|
| Tempo entre chegadas (único Create) | `{E['TEC_GERAL']}` horas | TEC_GERAL, n = {int(esc.loc['TEC_GERAL', 'N'])} |
| Taxa equivalente | {1 / tec_mean:.4f} navios/h = {24 / tec_mean:.2f} navios/dia | |
| Alternativa: 1 Create por terminal | TCAT `{E['TEC_TCAT']}` · APM `{E['TEC_APM']}` · PNOU `{E['TEC_PNOU']}` | TEC_* |

Sazonalidade: χ² por hora p = {chi_h.pvalue:.2g}, por dia da semana p = {chi_d.pvalue:.2g},
por mês p = {chi_m.pvalue:.2g}. Variação mensal da taxa: {taxa_mes.min():.2f} a {taxa_mes.max():.2f} navios/dia
(±{100 * (taxa_mes.max() - taxa_mes.min()) / 2 / taxa_mes.mean():.0f}% em torno da média).
→ {'Há variação significativa ao longo do dia; se quiserem mais realismo, use Arrival Schedule com `perfil_chegadas_hora.csv`. ' if chi_h.pvalue < .05 else ''}Para uma réplica de 30 dias, a taxa média constante é uma simplificação aceitável (justificar no relatório).

## 3. Atributos (Assign)

| Atributo | Expressão | Observação |
|---|---|---|
| `Eslora` (m) | `{E['ESLORA']}` | Empírica: distribuição bimodal (feeders × navios oceânicos) |
| `Calado` (m) | `{E['CALADO']}` | Opcional (pode alimentar uma restrição de cais) |
| `N_Reboc` **[H]** | Decide por condição: `Eslora < 150` → 1; `Eslora < 250` → 2; senão → 3 | Regra hipotética por porte |
| `T_Chegada` | `TNOW` | Para o Record do tempo no sistema |

Distribuição das classes no total: {', '.join(f'{k}: {v}%' for k, v in p_cl_geral.items())}.

## 4. Decide "Qual terminal?" (N-way by chance)

{prob_term.to_markdown(index=False)}

## 5. Processos

| Processo | Recurso(s) | Delay (h) |
|---|---|---|
| Manobra de entrada **[H]** | 1 Prático + `N_Reboc` Rebocadores | `{E['MANOBRA_ENTRADA']}` |
| Operação no cais — TCAT | Berço_TCAT (já apreendido) | `{E['OPER_TCAT']}` |
| Operação no cais — APM | Berço_APM | `{E['OPER_APM']}` |
| Operação no cais — PNOU | Berço_PNOU | `{E['OPER_PNOU']}` |
| Manobra de saída **[H]** | 1 Prático + `N_Reboc` Rebocadores | `{E['MANOBRA_SAIDA']}` |

Se preferirem uma única distribuição de operação: `{E['OPER_GERAL']}`. Mas o teste de
Kruskal-Wallis mostrou que os terminais diferem (ver `02_descritiva`), então o ideal é usar uma por terminal.

## 6. Capacidade dos recursos

| Recurso | Capacidade sugerida | Base |
|---|---|---|
{chr(10).join(f"| Berço_{r.Terminal} | {int(r['Berços sugeridos (P99 arred.)'])} | ocupação simultânea real: média {r['Média']:.2f}, P95 {r['P95']:.0f}, P99 {r['P99']:.0f}, máx {int(r['Máximo'])} |" for _, r in ocup.iterrows())}
| Prático **[H]** | 2 | demanda ≈ {prat_h:.1f} h/dia → utilização ≈ {100 * prat_h / 48:.0f}% |
| Rebocador **[H]** | 4 | demanda ≈ {reboc_h:.1f} h·rebocador/dia → utilização ≈ {100 * reboc_h / 96:.0f}% |

> A capacidade de berços foi estimada pelo P99 do número de navios simultâneos nos dados, ou seja,
> a quantidade de berços que atendeu 99% do tempo de 2025. Pesquisem o número físico de berços
> de cada terminal e ajustem, se necessário. A permanência real (ETA→ETD) já inclui eventuais esperas.

## 7. Configuração da execução (Run Setup)

- **Tipo de sistema:** não terminal (porto opera 24 h/7 dias; não "esvazia" ao fim do dia).
- **Duração da réplica:** 30 dias = **720 h** (8 h seria menor que a permanência média de um navio,
  ≈ {ok.PERM_H.mean():.0f} h; o enunciado aceita duração equivalente justificada).
- **Aquecimento (warm-up):** **168 h (7 dias)**: começa vazio e leva alguns ciclos de permanência
  (≈ {ok.PERM_H.mean():.0f} h cada) até estabilizar. Confirmem com um Plot do nº de navios no porto.
- **Replicações:** ≥ 10 por cenário. Calcule n* = n·(h/h*)² se o semi-intervalo de confiança ficar largo.
- **Estado inicial:** sistema vazio (descartado pelo warm-up).

## 8. Valores de referência para VALIDAÇÃO do cenário A

{ref.to_markdown(index=False)}

Lei de Little (consistência interna dos dados; o modelo deve reproduzi-la):

{lit.to_markdown(index=False)}

Critério sugerido: o cenário A é plausível se as médias simuladas (navios atendidos/30 dias, permanência
média e navios simultâneos) caírem dentro do intervalo de confiança ou com diferença < 10% dos valores acima.

## 9. Cenários sugeridos

| Cenário | Mudança no modelo | Pergunta que responde |
|---|---|---|
| A – Atual | parâmetros acima | Qual é o gargalo? Quanto um navio espera por berço? |
| B – Demanda +25% | `EXPO({tec_mean / 1.25:.3f})` no Create | Como o crescimento do tráfego afeta a espera e a utilização? |
| C – +1 berço no terminal mais utilizado | capacidade do berço +1 (em B) | O investimento em cais elimina a fila gerada em B? |
| D – Produtividade +15% (mais guindastes) | operação × 0,85 (ex.: `0.85 * ({E['OPER_TCAT']})`) | Melhorar o processo substitui ampliar o cais? |
| E – Menos rebocadores **[H]** | Rebocador = 3 | Os rebocadores viram gargalo em pico de manobras? |

**Indicadores a extrair:** tempo médio de espera por berço (fundeadouro), tempo médio no porto,
número médio na fila, utilização de cada berço/prático/rebocador, navios atendidos, navios/dia.

## 10. Animação (sugestão de ≥4 elementos)

Queue (fundeadouro por terminal) · Resource (berços com estados ocupado/livre) · Variable (navios no porto,
navios atendidos) · Plot (nº de navios no porto × tempo, útil também para o warm-up) · Histogram (tempo no
porto) · Clock (data/hora da simulação) · Level (utilização dos berços).
"""
(OUT / "parametros_arena.md").write_text(md, encoding="utf-8")
print(md)
