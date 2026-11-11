# Estatística descritiva

## Medidas por variável

| Variável        | Unidade   |    N |   Média |   Mediana |   Mínimo |   Máximo |   Desvio padrão |    CV |      Q1 |      Q3 |     P95 |   Assimetria |   Curtose |
|:----------------|:----------|-----:|--------:|----------:|---------:|---------:|----------------:|------:|--------:|--------:|--------:|-------------:|----------:|
| CALADO          | m         | 2141 |  11.627 |    11.4   |    6.62  |   19     |           3.157 | 0.272 |   9.19  |  14.5   |  16.9   |        0.249 |    -1.129 |
| ESLORA          | m         | 2141 | 225.899 |   195     |   99.95  |  400     |          81.46  | 0.361 | 151.72  | 295.18  | 366     |        0.58  |    -0.999 |
| MANOBRA_ENTRADA | h         | 2141 |   0.75  |     0.717 |    0.371 |    1.306 |           0.182 | 0.243 |   0.608 |   0.888 |   1.081 |        0.45  |    -0.605 |
| MANOBRA_SAIDA   | h         | 2141 |   0.584 |     0.558 |    0.25  |    1.052 |           0.155 | 0.266 |   0.465 |   0.707 |   0.851 |        0.375 |    -0.674 |
| OPER_APM        | h         |  652 |  15.461 |    13.093 |    3.197 |   46.586 |           8.597 | 0.556 |   9.606 |  18.82  |  35.457 |        1.367 |     1.472 |
| OPER_GERAL      | h         | 2110 |  17.997 |    14.612 |    1.924 |   68.531 |          11.29  | 0.627 |  10.054 |  22.221 |  42.106 |        1.447 |     2.01  |
| OPER_PNOU       | h         |  194 |  22.369 |    17.206 |    1.924 |   68.531 |          14.389 | 0.643 |  11.026 |  37.434 |  46.842 |        0.81  |    -0.41  |
| OPER_TCAT       | h         | 1264 |  18.634 |    15.38  |    2.297 |   66.325 |          11.681 | 0.627 |  10.373 |  23.443 |  43.411 |        1.425 |     2.011 |
| PERM_GERAL      | h         | 2110 |  19.325 |    15.858 |    3.017 |   69.7   |          11.429 | 0.591 |  11.217 |  23.6   |  43.428 |        1.431 |     1.959 |
| TEC_APM         | h         |  656 |  13.283 |    10.133 |    0.05  |   86.133 |          12.114 | 0.912 |   5.033 |  18.042 |  35.992 |        1.879 |     5.04  |
| TEC_GERAL       | h         | 2140 |   4.082 |     2.992 |    0     |   60.067 |           3.949 | 0.968 |   1.267 |   5.733 |  11.25  |        2.823 |    21.776 |
| TEC_PNOU        | h         |  193 |  45.064 |    40.217 |    0.483 |  141.933 |          29.006 | 0.644 |  22.817 |  63.933 |  94.543 |        0.811 |     0.284 |
| TEC_TCAT        | h         | 1289 |   6.772 |     5.167 |    0     |   91.383 |           6.271 | 0.926 |   2.383 |   9.45  |  17.227 |        3.364 |    29.672 |

## Valores atípicos (regra de Tukey)

| Variável        |   Limite inf. 1,5×IQR |   Limite sup. 1,5×IQR |   Atípicos moderados (1,5×IQR) |   Limite sup. 3×IQR |   Atípicos extremos (3×IQR) |   % extremos |
|:----------------|----------------------:|----------------------:|-------------------------------:|--------------------:|----------------------------:|-------------:|
| CALADO          |                 1.225 |                22.465 |                              0 |              30.43  |                           0 |        0     |
| ESLORA          |               -63.47  |               510.37  |                              0 |             725.56  |                           0 |        0     |
| MANOBRA_ENTRADA |                 0.188 |                 1.308 |                              0 |               1.728 |                           0 |        0     |
| MANOBRA_SAIDA   |                 0.102 |                 1.07  |                              0 |               1.433 |                           0 |        0     |
| OPER_APM        |                -4.217 |                32.642 |                             48 |              46.465 |                           1 |        0.153 |
| OPER_GERAL      |                -8.198 |                40.473 |                            126 |              58.724 |                          14 |        0.664 |
| OPER_PNOU       |               -28.584 |                77.044 |                              0 |             116.655 |                           0 |        0     |
| OPER_TCAT       |                -9.233 |                43.048 |                             67 |              62.654 |                           6 |        0.475 |
| PERM_GERAL      |                -7.358 |                42.175 |                            123 |              60.75  |                          13 |        0.616 |
| TEC_APM         |               -14.479 |                37.554 |                             26 |              57.067 |                          10 |        1.524 |
| TEC_GERAL       |                -5.433 |                12.433 |                             81 |              19.133 |                          12 |        0.561 |
| TEC_PNOU        |               -38.858 |               125.608 |                              2 |             187.283 |                           0 |        0     |
| TEC_TCAT        |                -8.217 |                20.05  |                             42 |              30.65  |                           6 |        0.465 |

> Nas variáveis PERM/OPER os atípicos extremos de permanência (3×IQR por terminal) já foram retirados no script 01 (ver `01_dados/log_limpeza.md`). Os restantes são estadias longas, porém plausíveis, e foram mantidos.

## Testes complementares

- **Diferença entre terminais (Kruskal-Wallis, operação no cais):** H = 43.14, p = 4.28e-10 → diferem; usar uma distribuição por terminal.
- **Correlação eslora × operação (Spearman):** ρ = 0.455, p = 3.31e-108. Correlação moderada: navios maiores tendem a operar mais tempo (mais contêineres). Parte desse efeito já aparece na diferença entre terminais; no modelo, a eslora entra como atributo (nº de rebocadores). Como melhoria, a operação poderia ser sorteada por classe de eslora (limitação a citar no relatório).
- **Autocorrelação dos tempos entre chegadas:** 3 de 20 lags fora do IC 95% (lag 1 = -0.075). Valores próximos de zero sustentam a hipótese de chegadas independentes (processo de Poisson).