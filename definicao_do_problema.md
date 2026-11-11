# Definição do problema — Simulação do Terminal Catalunya (Porto de Barcelona)

> Base: escalas de navios do Porto de Barcelona em 2025 (dados abertos da Autoridade Portuária),
> limpas e analisadas em `analise/` (procedimento em `analise/resultados/1_dados_limpos/LIMPEZA.md`).

---

## 1. Tema

**Simulação da atracação de navios porta-contêineres no Terminal Catalunya (TCAT), Porto de Barcelona.**

O TCAT é o principal terminal de contêineres de Barcelona: recebe **52% das escalas de porta-contêineres do
porto** e, em 2025, atendeu **1.328 navios**, cerca de **3,6 por dia**, funcionando 24 horas. Cada navio chega,
espera um berço livre (fundeado, se o cais estiver cheio), atraca, faz a carga e descarga de contêineres e vai embora.

| Item | Definição |
|---|---|
| Sistema | Cais do Terminal Catalunya (berços de atracação) |
| Área | Logística / transporte marítimo |
| Entidade | Navio porta-contêineres |
| Período dos dados | 01/01/2025 a 31/12/2025 |
| Fonte | Registro histórico real (Autoritat Portuària de Barcelona), 1.328 escalas |

---

## 2. Problema

**A demanda no TCAT cresceu ao longo de 2025, mas a estrutura de cais continuou a mesma.**
O terminal passou a operar lotado com mais frequência, e não se sabe quanto mais demanda ele aguenta antes de
os navios começarem a esperar fundeados por um berço.

### O que os dados mostram

| Evidência | Valor | Onde está |
|---|---|---|
| Navios por mês, de janeiro ao pico (outubro) | **80 → 133** (+66%) | `3_graficos/5_navios_por_mes.png` |
| Navios no 1º semestre → 2º semestre | **569 → 759** (+33%) | `3_graficos/numeros_graficos.csv` |
| Horas de berço demandadas, 1º → 2º semestre | **13.099 h → 15.722 h** (+20%) | tabela limpa (`PERM_H` somada) |
| Pico de outubro em relação à média mensal | **1,20×** (133 ÷ 110,7) | `3_graficos/GRAFICOS.md` |
| Navios no terminal ao mesmo tempo (média) | **3,0 → 3,5** do 1º para o 2º semestre | tabela limpa (ocupação simultânea) |
| % do tempo com **5 ou mais navios** ao mesmo tempo | **3,9% → 13,3%** (3,4× mais) | idem |
| Máximo de navios simultâneos | **6** | idem |

O problema fica mais sério por causa de **duas fontes de variabilidade**, que formam fila mesmo quando a
capacidade "na média" parece suficiente:

1. **As chegadas são irregulares.** O intervalo entre navios tem média de 6,6 h, mas varia muito (CV = 0,90).
   Às vezes chegam vários navios em poucas horas.
2. **Os navios grandes ocupam o berço por muito mais tempo.** Os navios com 300 m ou mais são só **26,7%
   das chegadas**, mas ocupam **40% das horas de berço**: ficam em média **32,6 h**, contra **17,7 h** dos
   menores (1,84×). Além disso, 4,4% das escalas são atípicas (59 navios), com até 252 h atracado.

**Consequência:** quando todos os berços estão ocupados, o navio que chega fica **fundeado esperando**. Isso
gera atraso para o armador (que paga por dia de navio parado), atrasa as escalas seguintes do navio e reduz a
confiabilidade do terminal. Testar mais demanda ou mais berços no terminal real é inviável; a simulação permite
fazer isso sem custo nem risco.

### Enunciado do problema

> *Com a demanda crescente e a ocupação desigual do cais entre navios pequenos e grandes, a capacidade atual
> de berços do Terminal Catalunya é suficiente para atender os navios sem espera significativa? Se não for, que
> mudança traz mais ganho: ampliar o cais ou acelerar a operação dos navios grandes?*

---

## 3. Cerne do estudo

O foco é **a disputa dos navios pelos berços do cais**: como a combinação de chegadas irregulares com tempos
de atracação diferentes por tamanho de navio forma a **fila de navios fundeados**.

### Limites do sistema

- **Começa:** quando o navio chega à área do porto (ETA).
- **Termina:** quando o navio deixa o berço e sai do porto (ETD).
- **Fora do escopo:** pátio de contêineres, caminhões e trens, outros terminais do porto e o mar aberto.
- **Tipo de sistema:** **não terminal**. O terminal opera 24 h por dia, todos os dias, e não "esvazia" no fim
  do expediente; por isso o modelo precisa de período de aquecimento.

### Componentes do modelo

| Elemento do Arena | No sistema | Base nos dados |
|---|---|---|
| **Entidade** | Navio porta-contêineres | 1.328 escalas |
| **Chegada (Create)** | Chegada do navio ao porto | Intervalo entre chegadas: `WEIB(6.91, 1.14)` h, KS p = 0,75 |
| **Atributos (Assign)** | Tamanho do navio, hora de chegada | Comprimento (`ESLORA_METRES`), `TNOW` |
| **Decisão (Decide)** | Navio < 300 m ou ≥ 300 m | 26,7% dos navios têm ≥ 300 m |
| **Fila** | Navios fundeados esperando berço | Resultado do modelo (o dataset não mede a espera separadamente) |
| **Recurso 1** | Berços do cais do TCAT | Até 6 navios simultâneos observados; quantidade a confirmar pela equipe |
| **Recurso 2** | Rebocadores das manobras | **Hipótese**: o dataset não registra manobras |
| **Processo 1** | Manobra de entrada e atracação | **Hipótese** de tempo (sem dado direto) |
| **Processo 2** | Carga e descarga no berço | < 300 m: `2.9 + LOGN(13.71, 9.71)` h · ≥ 300 m: `5.8 + LOGN(27.00, 23.20)` h |
| **Processo 3** | Manobra de desatracação e saída | **Hipótese** de tempo (sem dado direto) |
| **Record** | Tempo de espera e tempo no porto, por tamanho | Comparados com a permanência real (17,7 h e 32,6 h) na validação |

### Indicadores que o modelo precisa medir

- **Tempo médio de espera por berço** (horas fundeado), no geral e por tamanho de navio
- **Número médio de navios na fila** (fundeados)
- **Utilização dos berços** (%)
- **Tempo médio no porto** (espera + atracação), para comparar com os 21,7 h observados
- **Navios atendidos por mês**, para comparar com a média de 110,7 de 2025

---

## 4. Perguntas a serem respondidas pelo modelo

### P1. Onde está o gargalo hoje?

**Com a demanda média de 2025 (3,6 navios/dia), quanto tempo um navio espera fundeado por um berço, e qual é a
utilização dos berços?**

- *Por que importa:* é o diagnóstico da situação atual e a base de comparação para os outros cenários.
- *Cenário:* **A — atual**.
- *Indicadores:* tempo médio de espera, fila média, utilização dos berços. Se a utilização dos berços ficar bem
  acima da dos rebocadores e a fila se formar antes da atracação, o gargalo é o cais.

### P2. O terminal aguenta o pico de demanda?

**Se a demanda subir 20%, chegando ao nível de outubro de 2025, quanto aumentam a espera, a fila e a utilização
dos berços?**

- *Por que importa:* o pico de outubro já foi 20% acima da média, e as horas de berço cresceram 20% de um
  semestre para o outro. Não é um cenário hipotético: o terminal já viveu esse nível de demanda.
- *Cenário:* **B — demanda +20%** (intervalo entre chegadas dividido por 1,2).
- *Indicadores:* variação da espera e da fila em relação ao cenário A. Em sistemas de fila, a espera cresce
  muito mais que a demanda quando a utilização se aproxima de 100%; a pergunta é se o TCAT já está nessa faixa.

### P3. Os navios grandes fazem os pequenos esperarem?

**Os navios de 300 m ou mais, que são 27% das chegadas mas ocupam 40% das horas de berço, aumentam a espera de
todos? Quem espera mais: o navio grande ou o pequeno?**

- *Por que importa:* indica se uma melhoria voltada só aos navios grandes (mais guindastes, berço preferencial)
  beneficia o terminal inteiro.
- *Cenários:* A e B, com a espera registrada **separadamente por tamanho** (Record por grupo).
- *Indicadores:* tempo médio de espera dos navios < 300 m × ≥ 300 m; participação dos navios grandes na ocupação
  dos berços.

### P4. Ampliar o cais ou acelerar a operação?

**No pico de demanda (+20%), o que reduz mais a espera: um berço adicional ou reduzir em 15% o tempo de
atracação dos navios grandes (mais guindastes por navio)?**

- *Por que importa:* são as duas alternativas de melhoria típicas de um terminal. Um berço novo é uma obra cara
  e demorada; aumentar a produtividade custa menos, mas tem limite físico.
- *Cenários:* **C — B + 1 berço** e **D — B + permanência dos navios ≥ 300 m × 0,85**.
- *Indicadores:* espera, fila e utilização em C e D, comparadas com B, com intervalo de confiança para ver se a
  diferença é estatisticamente significativa.

### Resumo dos cenários

| Cenário | Mudança | Responde |
|---|---|---|
| A — Atual | Parâmetros de 2025 | P1, P3 |
| B — Pico | Demanda +20% | P2, P3 |
| C — Melhoria 1 | B + 1 berço | P4 |
| D — Melhoria 2 | B + 15% menos tempo de atracação dos navios ≥ 300 m | P4 |

O enunciado exige no mínimo 3 cenários (atual + 2 melhorias); aqui são 4, porque o cenário de pico (B) é a
base para testar as melhorias.
