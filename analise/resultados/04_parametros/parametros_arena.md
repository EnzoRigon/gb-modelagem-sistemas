# Ficha de parâmetros para o Arena

> Gerada automaticamente por `04_parametros_validacao.py`. Unidade de tempo base: **horas**.
> Fonte: escalas reais do Porto de Barcelona (2025), recorte de porta-contêineres em 3 terminais
> (2141 escalas, 364 dias). Itens marcados com **[H]** são hipóteses/sintéticos.

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
| Tempo entre chegadas (único Create) | `EXPO(4.082)` horas | TEC_GERAL, n = 2140 |
| Taxa equivalente | 0.2450 navios/h = 5.88 navios/dia | |
| Alternativa: 1 Create por terminal | TCAT `WEIB(7.143, 1.158)` · APM `EXPO(13.283)` · PNOU `ERLA(22.532, 2)` | TEC_* |

Sazonalidade: χ² por hora p = 1.1e-31, por dia da semana p = 1.6e-05,
por mês p = 0.18. Variação mensal da taxa: 4.94 a 6.77 navios/dia
(±16% em torno da média).
→ Há variação significativa ao longo do dia; se quiserem mais realismo, use Arrival Schedule com `perfil_chegadas_hora.csv`. Para uma réplica de 30 dias, a taxa média constante é uma simplificação aceitável (justificar no relatório).

## 3. Atributos (Assign)

| Atributo | Expressão | Observação |
|---|---|---|
| `Eslora` (m) | `CONT(0.00, 99.95, 0.10, 140.67, 0.20, 151.00, 0.30, 159.00, 0.40, 172.00, 0.50, 195.00, 0.60, 237.00, 0.70, 272.30, 0.80, 300.07, 0.90, 364.15, 1.00, 400.00)` | Empírica: distribuição bimodal (feeders × navios oceânicos) |
| `Calado` (m) | `CONT(0.00, 6.62, 0.10, 7.42, 0.20, 8.62, 0.30, 9.50, 0.40, 9.88, 0.50, 11.40, 0.60, 12.15, 0.70, 14.02, 0.80, 15.00, 0.90, 16.00, 1.00, 19.00)` | Opcional (pode alimentar uma restrição de cais) |
| `N_Reboc` **[H]** | Decide por condição: `Eslora < 150` → 1; `Eslora < 250` → 2; senão → 3 | Regra hipotética por porte |
| `T_Chegada` | `TNOW` | Para o Record do tempo no sistema |

Distribuição das classes no total: Pequeno (<150 m): 17.89%, Médio (150–250 m): 42.5%, Grande (≥250 m): 39.61%.

## 4. Decide "Qual terminal?" (N-way by chance)

| Terminal   |   Escalas |   Probabilidade (%) |   Chegadas/dia |
|:-----------|----------:|--------------------:|---------------:|
| TCAT       |      1290 |               60.25 |          3.545 |
| APM        |       657 |               30.69 |          1.805 |
| PNOU       |       194 |                9.06 |          0.533 |

## 5. Processos

| Processo | Recurso(s) | Delay (h) |
|---|---|---|
| Manobra de entrada **[H]** | 1 Prático + `N_Reboc` Rebocadores | `TRIA(0.366, 0.613, 1.307)` |
| Operação no cais — TCAT | Berço_TCAT (já apreendido) | `2.000 + LOGN(16.997, 13.999)` |
| Operação no cais — APM | Berço_APM | `LOGN(15.414, 8.478)` |
| Operação no cais — PNOU | Berço_PNOU | `CONT(0.00, 1.92, 0.10, 8.01, 0.20, 10.15, 0.30, 12.22, 0.40, 14.23, 0.50, 17.21, 0.60, 20.72, 0.70, 28.46, 0.80, 39.07, 0.90, 43.03, 1.00, 68.53)` |
| Manobra de saída **[H]** | 1 Prático + `N_Reboc` Rebocadores | `TRIA(0.245, 0.476, 1.053)` |

Se preferirem uma única distribuição de operação: `1.700 + LOGN(16.479, 12.700)`. Mas o teste de
Kruskal-Wallis mostrou que os terminais diferem (ver `02_descritiva`), então o ideal é usar uma por terminal.

## 6. Capacidade dos recursos

| Recurso | Capacidade sugerida | Base |
|---|---|---|
| Berço_TCAT | 5 | ocupação simultânea real: média 2.92, P95 4, P99 5, máx 6 |
| Berço_APM | 3 | ocupação simultânea real: média 1.27, P95 3, P99 3, máx 4 |
| Berço_PNOU | 2 | ocupação simultânea real: média 0.52, P95 2, P99 2, máx 2 |
| Prático **[H]** | 2 | demanda ≈ 7.8 h/dia → utilização ≈ 16% |
| Rebocador **[H]** | 4 | demanda ≈ 18.5 h·rebocador/dia → utilização ≈ 19% |

> A capacidade de berços foi estimada pelo P99 do número de navios simultâneos nos dados, ou seja,
> a quantidade de berços que atendeu 99% do tempo de 2025. Pesquisem o número físico de berços
> de cada terminal e ajustem, se necessário. A permanência real (ETA→ETD) já inclui eventuais esperas.

## 7. Configuração da execução (Run Setup)

- **Tipo de sistema:** não terminal (porto opera 24 h/7 dias; não "esvazia" ao fim do dia).
- **Duração da réplica:** 30 dias = **720 h** (8 h seria menor que a permanência média de um navio,
  ≈ 19 h; o enunciado aceita duração equivalente justificada).
- **Aquecimento (warm-up):** **168 h (7 dias)**: começa vazio e leva alguns ciclos de permanência
  (≈ 19 h cada) até estabilizar. Confirmem com um Plot do nº de navios no porto.
- **Replicações:** ≥ 10 por cenário. Calcule n* = n·(h/h*)² se o semi-intervalo de confiança ficar largo.
- **Estado inicial:** sistema vazio (descartado pelo warm-up).

## 8. Valores de referência para VALIDAÇÃO do cenário A

| Terminal   |   Navios atendidos / 30 dias (média) |   Desvio entre janelas |   Mín. |   Máx. |   Permanência média (h) |   Permanência mediana (h) |   Operação média (h) |   Navios simultâneos (média) |   Utilização dos berços (%) c/ berços sugeridos |
|:-----------|-------------------------------------:|-----------------------:|-------:|-------:|------------------------:|--------------------------:|---------------------:|-----------------------------:|------------------------------------------------:|
| TCAT       |                               106.67 |                  16.47 |     77 |    129 |                   19.99 |                     16.64 |                18.63 |                         2.92 |                                           58.35 |
| APM        |                                54.08 |                   7.23 |     47 |     68 |                   16.8  |                     14.5  |                15.46 |                         1.27 |                                           42.44 |
| PNOU       |                                16.08 |                   1.73 |     14 |     19 |                   23.45 |                     18.32 |                22.37 |                         0.52 |                                           26.22 |
| TOTAL      |                               176.83 |                  13.8  |    149 |    196 |                   19.32 |                     15.86 |                18    |                         4.72 |                                           47.15 |

Lei de Little (consistência interna dos dados; o modelo deve reproduzi-la):

| Terminal   |   λ (navios/h) |   W (h) |    λ·W |   L medido |   Diferença (%) |
|:-----------|---------------:|--------:|-------:|-----------:|----------------:|
| TCAT       |         0.1472 | 19.846  | 2.9214 |     2.9175 |          0.1352 |
| APM        |         0.076  | 16.7833 | 1.2751 |     1.2733 |          0.1394 |
| PNOU       |         0.0225 | 23.3459 | 0.5242 |     0.5244 |         -0.0233 |

Critério sugerido: o cenário A é plausível se as médias simuladas (navios atendidos/30 dias, permanência
média e navios simultâneos) caírem dentro do intervalo de confiança ou com diferença < 10% dos valores acima.

## 9. Cenários sugeridos

| Cenário | Mudança no modelo | Pergunta que responde |
|---|---|---|
| A – Atual | parâmetros acima | Qual é o gargalo? Quanto um navio espera por berço? |
| B – Demanda +25% | `EXPO(3.265)` no Create | Como o crescimento do tráfego afeta a espera e a utilização? |
| C – +1 berço no terminal mais utilizado | capacidade do berço +1 (em B) | O investimento em cais elimina a fila gerada em B? |
| D – Produtividade +15% (mais guindastes) | operação × 0,85 (ex.: `0.85 * (2.000 + LOGN(16.997, 13.999))`) | Melhorar o processo substitui ampliar o cais? |
| E – Menos rebocadores **[H]** | Rebocador = 3 | Os rebocadores viram gargalo em pico de manobras? |

**Indicadores a extrair:** tempo médio de espera por berço (fundeadouro), tempo médio no porto,
número médio na fila, utilização de cada berço/prático/rebocador, navios atendidos, navios/dia.

## 10. Animação (sugestão de ≥4 elementos)

Queue (fundeadouro por terminal) · Resource (berços com estados ocupado/livre) · Variable (navios no porto,
navios atendidos) · Plot (nº de navios no porto × tempo, útil também para o warm-up) · Histogram (tempo no
porto) · Clock (data/hora da simulação) · Level (utilização dos berços).
