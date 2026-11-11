# Gráficos para o relatório e a apresentação

Gerados por `analise/scripts/3_graficos.py`. Para refazer: `bash analise/rodar_tudo.sh`.

## Base de dados usada nos 5 gráficos

Todos os gráficos são feitos **a partir da tabela limpa** `1_dados_limpos/escalas_TCAT_conteineres.csv`,
gerada no passo de limpeza (procedimento completo em `1_dados_limpos/LIMPEZA.md`).

| Item | Valor |
|---|---|
| Fonte | Escalas de navios do Porto de Barcelona, 2025 (dados abertos da Autoridade Portuária) |
| Recorte | Navios **porta-contêineres** no **Terminal Catalunya (TCAT)** |
| Observações | **1.328 escalas** (1.327 intervalos entre chegadas) |
| Limpeza | Removidas as escalas duplicadas (mesma escala listada em dois terminais); não havia datas faltando nem permanência ≤ 0 |
| Estado da escala | **Todos os estados foram mantidos** (concluída, iniciada, solicitada…). Toda escala pedida é demanda; se ficassem só as concluídas, dezembro cairia artificialmente de 130 para 104 navios, porque as escalas do fim do ano ainda estavam em andamento quando os dados foram extraídos |
| Grupos de tamanho | **< 300 m** (974 navios, 73,3%) e **≥ 300 m** (354 navios, 26,7%) |

| Gráfico | Coluna(s) da tabela limpa usadas |
|---|---|
| 1. Intervalo entre chegadas | `INTERVALO_CHEGADA_H` |
| 2. Permanência por tamanho | `PERM_H`, `GRUPO_TAMANHO`, `ATIPICO_EXTREMO` (para tirar os extremos do ajuste) |
| 3. Comprimento | `ESLORA_METRES` |
| 4. Boxplot | `PERM_H`, `GRUPO_TAMANHO` |
| 5. Navios por mês | `ETA` |

---

## 1. Histograma do intervalo entre chegadas (obrigatório)

**Arquivo:** `1_hist_intervalo_chegadas.png`

**O que mostra:** quanto tempo passa entre a chegada de um navio e a do seguinte. As barras são os dados
reais; as curvas são as distribuições teóricas ajustadas por cima.

| Medida | Valor |
|---|---|
| n | 1.327 intervalos |
| Média | 6,59 h (≈ 3,6 navios/dia) |
| Mediana | 5,05 h |
| Desvio padrão | 5,93 h |
| Coeficiente de variação (CV) | 0,90 |
| **Distribuição ajustada** | **`WEIB(6.91, 1.14)`**: KS p = 0,75 (**aceita**) |
| Exponencial, para comparação | `EXPO(6.59)`: KS p = 0,0004 (rejeitada) |

**Como ler:**
- A **curva azul (Weibull)** acompanha as barras, inclusive no começo: quase não há navios chegando com
  menos de 1 h de diferença.
- A **curva laranja tracejada (Exponencial)** superestima os intervalos muito curtos. Ela supõe que o
  "mais provável" é chegar um navio logo depois do outro, o que não acontece num terminal com janelas de
  atracação programadas.
- **KS p** é o p-valor do teste de Kolmogorov-Smirnov. Acima de 0,05, não há evidência contra o ajuste;
  abaixo de 0,05, a distribuição é rejeitada.

**O que significa para o modelo:** no módulo **Create** do Arena, use
`WEIB(6.91, 1.14)` horas entre chegadas. A forma 1,14 (pouco acima de 1) indica chegadas **um pouco mais
regulares que aleatórias puras**. Isso é coerente com navios de linhas regulares, que têm escala
programada, mas sofrem atrasos de mar e de outros portos.

**Para ter a "prova" no Input Analyzer:** abra `intervalo_chegadas_TCAT.dst` (nesta pasta) em *File › Data
File › Use Existing* e depois *Fit › Weibull* (ou *Fit All*). A tela do Input Analyzer mostra o mesmo
histograma com a curva e o erro quadrático; usem o print dela no relatório junto com este gráfico.
Os parâmetros podem variar um pouco, porque o Input Analyzer usa outro método de estimação.

---

## 2. Histograma da permanência no berço, por tamanho de navio (obrigatório)

**Arquivo:** `2_hist_permanencia_por_tamanho.png`

**O que mostra:** o tempo que cada navio fica atracado (da chegada à saída, ETD − ETA), em dois
painéis: navios com menos de 300 m e com 300 m ou mais.

| Medida | < 300 m | ≥ 300 m |
|---|---|---|
| n | 974 | 354 |
| **Média** | **17,7 h** | **32,6 h** |
| Mediana | 14,3 h | 28,2 h |
| Desvio padrão | 15,7 h | 19,3 h |
| Mínimo / máximo | 3,3 h / 252,8 h | 6,5 h / 122,5 h |
| **Distribuição ajustada (Arena)** | **`2.9 + LOGN(13.71, 9.71)`**: KS p = 0,17 | **`5.8 + LOGN(27.00, 23.20)`**: KS p = 0,13 |

**Como ler:**
- A linha tracejada é a média de cada grupo. O navio grande fica, em média, **1,84 vez mais tempo** no
  berço (32,6 ÷ 17,7).
- O painel dos pequenos é estreito e concentrado entre 8 e 25 h. O dos grandes é mais espalhado, com
  boa parte entre 15 e 50 h.
- O teste de Mann-Whitney confirma que os dois grupos são diferentes (p < 0,001); não é efeito do acaso.

**O que significa para o modelo:** justifica o **Decide por tamanho**. Depois dele, cada grupo segue para
um **Process** com a sua própria distribuição de tempo. Se o modelo usasse uma média única (≈ 21,7 h),
subestimaria a ocupação do berço causada pelos navios grandes e superestimaria a dos pequenos.

**Sobre as distribuições:** a Lognormal com deslocamento (o número antes do `+`) foi escolhida porque o
tempo de atracação tem um **mínimo físico**: nenhum navio opera em zero hora, e o deslocamento representa
esse piso. Além disso, ele tem **cauda à direita**, já que alguns navios movimentam muito mais contêineres
que a média. A Normal não serve, porque seria simétrica e poderia gerar tempos negativos. No ajuste, os
atípicos extremos (3×IQR, 16 + 3 navios) foram excluídos; no gráfico eles continuam aparecendo.

`LOGN(média, desvio)` no Arena recebe a média e o desvio **da própria variável** (não do logaritmo).

---

## 3. Histograma do comprimento dos navios (obrigatório, 3ª variável)

**Arquivo:** `3_hist_comprimento.png`

**O que mostra:** a quantidade de navios por faixa de comprimento (eslora), de 10 em 10 m. A linha vermelha
marca o corte de **300 m**; as barras azuis são os navios < 300 m e as laranjas os ≥ 300 m.

| Medida | Valor |
|---|---|
| n | 1.328 |
| Média / mediana | 235,2 m / 207,7 m |
| Mínimo / máximo | 121,8 m / 400,0 m |
| Desvio padrão | 85,9 m |
| **% de navios ≥ 300 m** | **26,7%** |

**Como ler:**
- A distribuição **não tem um único pico**. Há um grupo grande de navios menores (130–190 m, os *feeders*,
  que fazem a distribuição regional) e vários picos de navios oceânicos (270–300 m, 330–340 m, 360–370 m
  e 400 m). Cada pico corresponde a uma "classe" de navio usada pelos armadores.
- Por isso nenhuma distribuição clássica (Normal, Triangular etc.) se ajusta bem ao comprimento.

**O que significa para o modelo:** o modelo **não precisa sortear o comprimento**. Basta a proporção:
no **Decide** "2-way by chance", **26,7%** dos navios vão para o ramo "≥ 300 m" e **73,3%** para o ramo
"< 300 m". Se preferirem guardar o comprimento como atributo (para exibir na animação, por exemplo), usem a
distribuição empírica construída pelos decis observados:
`CONT(0.0, 121.8, 0.1, 139.1, 0.2, 151.7, 0.3, 169.9, 0.4, 172.0, 0.5, 207.7, 0.6, 270.1, 0.7, 299.9, 0.8, 333.0, 0.9, 366.0, 1.0, 400.0)`.

**Cuidado se a professora perguntar "por que 300 m?":** há muitos navios com 299–300 m (90 navios entre
290 e 300 m e 34 entre 300 e 310 m), e eles ficam tempos parecidos (≈ 21 h e ≈ 20 h). A diferença grande
vem dos navios de **330 a 400 m** (os maiores porta-contêineres que escalam em Barcelona). O 300 m é um
corte operacional simples e fácil de explicar, mas não é uma fronteira natural dos dados. Isso pode entrar
como limitação no relatório.

---

## 4. Boxplot da permanência por tamanho (opcional, recomendado)

**Arquivo:** `4_boxplot_permanencia_tamanho.png`

**O que mostra:** a mesma informação do gráfico 2, resumida em caixas, que é a forma mais direta de mostrar
os **valores atípicos** exigidos no enunciado.

**Como ler um boxplot:**
- **Caixa:** vai do 1º quartil (25% dos navios ficam menos que isso) ao 3º quartil (75%).
- **Linha dentro da caixa:** a mediana.
- **"Bigodes":** vão até o último valor dentro de 1,5 × IQR (IQR = Q3 − Q1).
- **Pontos vermelhos:** **valores atípicos** (acima do bigode), pela regra de Tukey.

| Medida | < 300 m | ≥ 300 m |
|---|---|---|
| Q1 – Q3 | 10,4 – 21,0 h | 18,7 – 40,2 h |
| Limite de atípico (Q3 + 1,5×IQR) | 36,8 h | 72,3 h |
| **Atípicos moderados** | **43 (4,4%)** | **16 (4,5%)** |
| Atípicos extremos (Q3 + 3×IQR) | 16 | 3 |

**Interpretação:** os atípicos são navios que ficaram muito mais tempo que o normal (até 252 h ≈ 10 dias).
Provavelmente são reparos, esperas comerciais ou paradas técnicas, e não operação normal de carga e
descarga. **Decisão adotada:** os extremos (3×IQR) ficam fora do ajuste da distribuição, para não distorcer o
tempo de serviço, mas continuam sendo contados como chegadas. A lista com o nome de cada navio atípico está
em `lista_atipicos_pequenos.csv` e `lista_atipicos_grandes.csv`.

---

## 5. Navios por mês em 2025 (introdução / slide de abertura)

**Arquivo:** `5_navios_por_mes.png`

**O que mostra:** o número de navios porta-contêineres que chegaram ao TCAT em cada mês de 2025, com uma
linha de tendência.

| Medida | Valor |
|---|---|
| Janeiro | **80** navios |
| Pico | **133** navios (outubro) |
| Crescimento janeiro → pico | +66% |
| 1º semestre → 2º semestre | 569 → 759 navios (**+33%**) |
| Tendência linear | **+4,9 navios a cada mês** |
| Média mensal | 110,7 navios |

**Como ler:** a demanda cresceu de forma quase contínua ao longo do ano. A queda de junho (101) é pontual,
e a partir de julho o terminal ficou num patamar de 120–133 navios/mês.

**O que significa para o trabalho:**
- **Justifica o problema:** o terminal está recebendo cada vez mais navios com a mesma estrutura de
  berços. A pergunta "até quando a capacidade atual aguenta?" é real.
- **Justifica o cenário de +20% de demanda:** o pico de outubro (133) é **exatamente 20% acima da média
  mensal** (133 ÷ 110,7 = 1,20). Ou seja, +20% não é um número arbitrário: é o nível que o terminal já
  enfrentou no mês mais movimentado de 2025. No Arena, isso equivale a dividir o intervalo entre
  chegadas por 1,2.
- **Limitação a declarar:** o modelo usa uma taxa média constante; a tendência de crescimento ao longo
  do ano não é simulada dentro de uma réplica.

> **Diferença em relação ao texto de vocês:** o texto dizia "de **85** para 133". Nesta base, janeiro tem
> **80** navios porta-contêineres. Se contarmos **todos os tipos de navio** no TCAT, janeiro tem 87, e
> com só as escalas concluídas, 85, mas aí o pico vira 134. Para manter a coerência com os outros gráficos
> (só porta-contêineres), sugiro usar **80 → 133** no texto.

---

## Outros arquivos desta pasta

| Arquivo | O que é |
|---|---|
| `numeros_graficos.csv` | Todos os números citados acima, em tabela (para copiar para o relatório) |
| `ajustes_permanencia.csv` | Estatísticas e expressão do Arena para cada grupo de tamanho |
| `atipicos_permanencia.csv` | Quartis, limites e contagem de atípicos por grupo |
| `lista_atipicos_pequenos.csv` / `lista_atipicos_grandes.csv` | Quais navios são atípicos (nome, comprimento, datas, permanência) |
| `navios_por_mes.csv` | Série mensal usada no gráfico 5 |
| `intervalo_chegadas_TCAT.dst` | Intervalos entre chegadas, um por linha, para abrir no Arena Input Analyzer |

### O que significa cada coluna das tabelas

**`numeros_graficos.csv`**

| Coluna | Significado |
|---|---|
| Gráfico | Número do gráfico ao qual o indicador pertence (1 a 5) |
| Indicador | Nome da medida (ex.: média, mediana, KS p) |
| Valor | Valor calculado (horas, metros, % ou contagem, conforme o indicador) |

Indicadores menos óbvios:
- **CV** (coeficiente de variação) = desvio ÷ média. Perto de 1, chegadas aleatórias (Exponencial); abaixo de 1, mais regulares.
- **Weibull escala β / forma α**: parâmetros da `WEIB(β, α)` do Arena. Forma 1 seria igual à Exponencial; acima de 1, mais regular.
- **KS p**: p-valor do teste de Kolmogorov-Smirnov. ≥ 0,05 → a distribuição **não é rejeitada**; < 0,05 → rejeitada.
- **Mann-Whitney p**: testa se a permanência dos dois grupos de tamanho é diferente. 0,0 significa p < 0,0001 (diferença garantida).
- **Razão médias grande/pequeno**: quantas vezes o navio ≥ 300 m fica mais tempo que o < 300 m.
- **% navios ≥ 300 m**: probabilidade a usar no Decide do Arena.
- **Tendência**: inclinação da reta ajustada no gráfico 5 (quantos navios a mais por mês, em média).

**`ajustes_permanencia.csv`**

| Coluna | Significado |
|---|---|
| Grupo | `< 300 m` ou `≥ 300 m` |
| N total | Navios do grupo |
| N no ajuste (sem extremos 3×IQR) | Navios usados para ajustar a distribuição (sem os atípicos extremos) |
| Média / Mediana / Desvio / Mín / Máx (h) | Estatísticas da permanência com **todos** os navios do grupo |
| Média sem extremos (h) | Média só dos navios usados no ajuste |
| Expressão Arena | Distribuição ajustada, pronta para colar no Process |
| KS p | Teste de aderência da distribuição ajustada (≥ 0,05 = aceita) |

**`atipicos_permanencia.csv`**

| Coluna | Significado |
|---|---|
| Q1 (h) / Q3 (h) | 1º e 3º quartis: 25% e 75% dos navios ficam menos que esse tempo |
| Limite superior 1,5×IQR (h) | Q3 + 1,5 × (Q3 − Q1). Acima disso = **atípico moderado** (ponto vermelho no boxplot) |
| Atípicos moderados | Quantos navios passam desse limite |
| Limite superior 3×IQR (h) | Q3 + 3 × (Q3 − Q1). Acima disso = **atípico extremo** (excluído do ajuste) |
| Atípicos extremos | Quantos navios passam desse limite |
| % atípicos | Atípicos moderados ÷ navios do grupo |

**`lista_atipicos_pequenos.csv` / `lista_atipicos_grandes.csv`**: uma linha por navio atípico, com `ESCALANUM`
(nº da escala), `VAIXELLNOM` (nome), `ESLORA_METRES` (comprimento), `ETA`/`ETD` (chegada/saída), `PERM_H`
(permanência em horas) e `Grupo`. Serve para citar exemplos concretos no relatório.

**`navios_por_mes.csv`**: `Mês` e `Navios` (chegadas de porta-contêineres no TCAT naquele mês).

## Resumo para colar no Arena

| Módulo | Parâmetro | Valor |
|---|---|---|
| Create | Intervalo entre chegadas (h) | `WEIB(6.91, 1.14)` |
| Decide (2-way by chance) | % para "≥ 300 m" | `26.7` |
| Process: navio < 300 m | Tempo no berço (h) | `2.9 + LOGN(13.71, 9.71)` |
| Process: navio ≥ 300 m | Tempo no berço (h) | `5.8 + LOGN(27.00, 23.20)` |
| Cenário +20% demanda | Intervalo entre chegadas (h) | `WEIB(6.91, 1.14) / 1.2` |
