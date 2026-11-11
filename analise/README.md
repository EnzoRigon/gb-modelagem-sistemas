# Análise de dados — Terminais de contêineres do Porto de Barcelona

Material de apoio às **Etapas 2, 3, 4, 5 e 7** do Trabalho Final (Grau B) de Simulação e Modelagem de Sistemas.
Tudo aqui é gerado por código e pode ser refeito com um comando:

```bash
bash analise/rodar_tudo.sh
```

(cria o ambiente Python em `.venv/` se não existir e roda os 5 scripts em ordem, em cerca de 1 minuto)

---

## Recorte do sistema

| Item | Definição |
|---|---|
| Fonte | Escalas de navios da Autoritat Portuària de Barcelona, 2025 (dados abertos, CSV na raiz) |
| Sistema modelado | Navios **porta-contêineres** nos 3 terminais de contêineres: **TCAT** (Terminal Catalunya), **APM** (APM Terminals) e **PNOU** (Terminal Port Nou) |
| Entidade | Navio |
| Recursos | Berços de cada terminal, práticos, rebocadores |
| Processos | Manobra de entrada → operação no cais → manobra de saída |
| Fila | Navio fundeado esperando berço (e esperando prático/rebocador) |
| Decisões | Terminal de destino (probabilidade) e nº de rebocadores (pela eslora) |
| Unidade de tempo | horas |

---

## O que é cada pasta/arquivo

### `scripts/`: código

| Script | Etapa do enunciado | O que faz |
|---|---|---|
| `comum.py` | — | Funções compartilhadas: leitura, limpeza e recorte dos dados |
| `01_preparar_dados.py` | **2. Coleta e organização** | Limpa o CSV, remove duplicadas/não concluídas, marca atípicos, gera os dados sintéticos de manobra e monta a planilha final |
| `02_estatistica_descritiva.py` | **3. Análise estatística (descritiva)** | Média, mediana, mín., máx., desvio, CV, quartis, histogramas, boxplots, atípicos, testes de independência e de diferença entre terminais |
| `03_ajuste_distribuicoes.py` | **3. Avaliação e justificativa das distribuições** | Testa 5 a 6 distribuições por variável (com e sem offset), calcula erro quadrático (o mesmo do Input Analyzer), Qui², KS e AIC, e escolhe a distribuição por teoria + ajuste |
| `04_parametros_validacao.py` | **4. Modelo, 5. Validação, 7. Cenários** | Probabilidades das decisões, capacidade dos berços (a partir da ocupação real), sazonalidade, Lei de Little, demanda de rebocadores, valores de referência para validação e ficha do Arena |
| `05_panorama_porto.py` | Introdução / contexto | Estatísticas do porto inteiro por tipo de navio (extra) |

### `resultados/01_dados/`: base de dados (entregável "Base de dados")

| Arquivo | O que é |
|---|---|
| **`base_dados_modelo.xlsx`** | **Planilha para entregar.** Aba `LEIA-ME` com origem, unidade, método e N de cada variável; aba com as 2.141 escalas; uma aba por variável |
| `escalas_conteineres.csv` | Escalas limpas do recorte, com colunas derivadas (permanência, manobras, operação, classe, nº de rebocadores) |
| `escalas_porto_limpo.csv` | Porto inteiro, já limpo (10.038 escalas) |
| `variaveis/*.dst` | Um valor por linha, para abrir direto no **Arena Input Analyzer** (*File › Data File › Use Existing*) |
| `log_limpeza.md` | Passo a passo da limpeza: quantos registros saíram e por quê (serve para a "descrição do procedimento de coleta") |

**Variáveis** (todas com ≥ 200 observações nos totais):

| Variável | Unid. | Origem | N |
|---|---|---|---|
| `TEC_GERAL` / `TEC_TCAT` / `TEC_APM` / `TEC_PNOU`: tempo entre chegadas | h | Real | 2140 / 1289 / 656 / 193 |
| `OPER_GERAL` / `OPER_TCAT` / `OPER_APM` / `OPER_PNOU`: operação no cais | h | Real − sintético | 2110 / 1264 / 652 / 194 |
| `PERM_GERAL`: permanência no porto (ETD − ETA) | h | Real | 2110 |
| `ESLORA`: comprimento | m | Real | 2141 |
| `CALADO` | m | Real | 2141 |
| `MANOBRA_ENTRADA` / `MANOBRA_SAIDA` | h | **Sintético** | 2141 |

### `resultados/02_descritiva/`: estatística descritiva

| Arquivo | O que é |
|---|---|
| `estatisticas_descritivas.md` / `.csv` | Tabela com todas as medidas exigidas + texto com os testes |
| `atipicos.csv` | Limites de Tukey (1,5×IQR e 3×IQR) e contagem de atípicos por variável |
| `hist_<VAR>.png` | Histograma + boxplot de cada variável (com média e mediana marcadas) |
| `boxplot_por_terminal.png` | Permanência e operação comparadas entre TCAT, APM e PNOU |
| `dispersao_eslora_operacao.png` | Comprimento × tempo de operação (correlação de Spearman) |
| `autocorrelacao_tec.png` / `.csv` | Autocorrelação dos tempos entre chegadas (justifica chegadas independentes) |

### `resultados/03_ajuste/`: ajuste de distribuições (entregável "Análise estatística")

| Arquivo | O que é |
|---|---|
| **`distribuicoes_escolhidas.md`** | **Tabela final com a expressão do Arena + justificativa escrita de cada escolha** (pronto para o relatório) |
| `distribuicoes_escolhidas.csv` | Mesmo conteúdo em CSV |
| `ranking_<VAR>.csv` | Todas as distribuições testadas, ordenadas por erro quadrático, com Qui², KS e AIC (evidência do ajuste) |
| `ajuste_<VAR>.png` | 3 painéis: histograma + 3 melhores curvas, Q-Q plot e CDF empírica × teórica |

### `resultados/04_parametros/`: parâmetros do modelo e validação

| Arquivo | O que é |
|---|---|
| **`parametros_arena.md`** | **Ficha completa para montar o modelo:** estrutura dos módulos, expressões, capacidades, Run Setup, referência de validação, cenários e animação |
| `prob_terminal.csv` | Probabilidades do Decide "Qual terminal?" (60,25% / 30,69% / 9,06%) |
| `prob_classe_eslora.csv` | % de navios pequenos/médios/grandes por terminal → nº de rebocadores |
| `ocupacao_simultanea.csv` | Nº de navios ao mesmo tempo em cada terminal (média, P95, P99, máx.) → capacidade dos berços |
| `ocupacao_serie_junho.png` / `ocupacao_hist.png` | Gráficos da ocupação real dos terminais |
| `perfil_chegadas.png` + `perfil_chegadas_*.csv` | Chegadas por hora, dia da semana e mês, com teste χ² (decide se usa taxa constante ou Schedule) |
| `validacao_referencia.csv` | **Valores reais para comparar com o cenário A**: navios/30 dias, permanência média, navios simultâneos e utilização |
| `lei_little.csv` | Verificação L = λ·W nos dados (diferença < 0,2%) |
| `demanda_rebocadores.csv` | Horas de trabalho de práticos e rebocadores por dia → utilização esperada |

### `resultados/05_panorama_porto/`: contexto (extra)

| Arquivo | O que é |
|---|---|
| `panorama.md` | Resumo do porto inteiro: 9 tipos de navio, top terminais, origens, bandeiras e consignatários |
| `resumo_por_tipo_navio.csv` | Volume, chegadas/dia, permanência e distribuição sugerida por tipo de navio (útil se mudarem o recorte) |
| `chegadas_por_tipo_mes.png` / `permanencia_por_tipo.png` | Gráficos para a introdução |

---

## Principais achados (para usar no relatório)

1. **Chegadas são um processo de Poisson.** CV = 0,97, autocorrelação ≈ 0 e a Exponencial não é rejeitada (KS p = 0,054) → `EXPO(4.082)` h, ≈ 5,9 navios/dia.
2. **Os terminais são diferentes** (Kruskal-Wallis p ≈ 4·10⁻¹⁰): uma distribuição de operação por terminal. TCAT e APM seguem Lognormal; **PNOU é bimodal** (serviços de ~12 h e ~40 h), por isso usa empírica `CONT`.
3. **O PNOU recebe linhas regulares:** tempo entre chegadas com CV = 0,64 → Erlang k = 2, mais regular que Poisson.
4. **A eslora é bimodal** (feeders × navios oceânicos): nenhuma paramétrica serve, então usa empírica `CONT`.
5. **Ocupação real:** TCAT tem em média 2,9 navios simultâneos (máx. 6), APM 1,3 e PNOU 0,5. Com os berços sugeridos (5/3/2), a utilização fica em ~58%, ~42% e ~26%; o **TCAT é o candidato a gargalo**.
6. **Sazonalidade:** a variação por mês não é significativa (p = 0,18), então a taxa constante numa réplica de 30 dias é defensável. A variação por hora do dia é significativa (opcional: Arrival Schedule).
7. **Os dados são internamente consistentes:** a Lei de Little fecha com < 0,2% de erro, o que dá uma boa base de validação.

## Sugestão de perguntas de simulação

1. Qual terminal é o gargalo, e quanto tempo os navios esperam fundeados por um berço?
2. Como um aumento de 25% no tráfego de contêineres afeta a espera e a utilização dos berços?
3. O que traz mais ganho: um berço adicional no TCAT ou 15% a mais de produtividade na operação (guindastes)?
4. *(opcional)* Com quantos rebocadores eles passam a ser gargalo nos picos de manobra?

---

## Hipóteses e limitações (declarar no relatório)

- **ETA/ETD são horários estimados/programados** pela Autoridade Portuária, não horários reais medidos por AIS.
- A permanência (ETD − ETA) inclui eventual espera; por isso a capacidade dos berços foi calibrada pela **ocupação simultânea observada (P99)**. Confiram o número físico de berços de cada terminal e ajustem, se necessário.
- **Manobras são SINTÉTICAS** (o dataset não as registra), geradas por `0,30 + 0,0020·eslora + N(0; 0,08)` h na entrada e `0,20 + 0,0017·eslora + N(0; 0,07)` h na saída, com semente 2026. A operação no cais = permanência real − manobras.
- **Nº de rebocadores por porte (1/2/3) e quantidade de práticos (2) e rebocadores (4) são hipóteses**, não dados.
- 31 estadias extremas (> 3×IQR do terminal, ex.: reparos e paradas) foram excluídas dos tempos de serviço; os 2.141 navios continuam nas chegadas.
- Escalas duplicadas (mesma escala em dois terminais) e não concluídas foram removidas (ver `log_limpeza.md`).
- Com n grande (> 500), os testes KS/Qui² rejeitam até desvios mínimos; por isso a escolha também considera o Q-Q plot, o erro quadrático e a teoria.
