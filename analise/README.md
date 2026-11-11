# Análise de dados — Terminal Catalunya (Porto de Barcelona)

Material das **Etapas 2 e 3** do Trabalho Final (coleta, organização e análise estatística dos dados).
Tudo é gerado por código, em 3 passos encadeados:

```
CSV bruto ──► 1_limpeza_dados.py ──► tabela limpa ──► 2_panorama_porto.py  (porto inteiro, por tipo de navio)
                                                  └─► 3_graficos.py       (5 gráficos do relatório, só TCAT)
```

Para refazer tudo (poucos segundos): `bash analise/rodar_tudo.sh`

## Onde está cada explicação

| Quero entender… | Leia |
|---|---|
| O que significa cada **coluna do CSV original** e cada **valor/código** (tipos de navio, estados, portos…) | [`../dicionario_dados.md`](../dicionario_dados.md) |
| Como os dados foram **limpos**, o que foi removido e por quê, e as **colunas criadas** | [`resultados/1_dados_limpos/LIMPEZA.md`](resultados/1_dados_limpos/LIMPEZA.md) |
| O **porto inteiro por tipo de navio** e o que significa cada coluna do resumo | [`resultados/2_panorama_porto/PANORAMA.md`](resultados/2_panorama_porto/PANORAMA.md) |
| Os **5 gráficos** do relatório, como ler cada um e as colunas das tabelas de apoio | [`resultados/3_graficos/GRAFICOS.md`](resultados/3_graficos/GRAFICOS.md) |

## Arquivos

### `scripts/`

| Script | O que faz |
|---|---|
| `comum.py` | Leitura do CSV bruto, traduções (tipo de navio, estado da escala), regra de atípicos (IQR) |
| `1_limpeza_dados.py` | Limpa o CSV, cria as colunas derivadas, separa a base do modelo (TCAT) e gera a planilha |
| `2_panorama_porto.py` | Resumo do porto inteiro por tipo de navio + rankings (terminais, origens, bandeiras, consignatários) |
| `3_graficos.py` | Gera os 5 gráficos **a partir da tabela limpa do TCAT** |

### `resultados/1_dados_limpos/`

| Arquivo | O que é |
|---|---|
| **`base_dados_TCAT.xlsx`** | **Planilha para entregar** (abas: LEIA-ME, escalas_TCAT, log_limpeza, qualidade_dados_brutos) |
| `escalas_TCAT_conteineres.csv` | **Tabela limpa do modelo**: 1.328 escalas, com intervalo entre chegadas, permanência, comprimento, grupo de tamanho e atípicos |
| `escalas_porto_limpas.csv` | Porto inteiro limpo (10.122 escalas), com tipo e estado traduzidos |
| `qualidade_dados_brutos.csv` | Valores ausentes e problemas de cada coluna do CSV original |
| `LIMPEZA.md` | Procedimento passo a passo, com contagens e explicação das colunas |

### `resultados/2_panorama_porto/`

| Arquivo | O que é |
|---|---|
| `resumo_por_tipo_navio.csv` | Volume, ritmo de chegadas, permanência, principal terminal e distribuição sugerida por tipo de navio |
| `top_terminais.csv`, `top_origens.csv`, `top_bandeiras.csv`, `top_consignatarios.csv` | 15 valores mais frequentes de cada campo |
| `chegadas_por_tipo_mes.png` | Escalas por mês, empilhadas por tipo |
| `permanencia_por_tipo.png` | Boxplot da permanência por tipo |
| `PANORAMA.md` | Tabelas + explicação de cada coluna e de cada tipo de navio |

### `resultados/3_graficos/`

| Arquivo | O que é |
|---|---|
| `1_hist_intervalo_chegadas.png` | Intervalo entre chegadas + curva ajustada `WEIB(6.91, 1.14)` (obrigatório) |
| `2_hist_permanencia_por_tamanho.png` | Permanência: 17,7 h (< 300 m) × 32,6 h (≥ 300 m) (obrigatório) |
| `3_hist_comprimento.png` | Comprimento com a linha de 300 m: 73,3% × 26,7% (obrigatório) |
| `4_boxplot_permanencia_tamanho.png` | Valores atípicos por grupo (opcional) |
| `5_navios_por_mes.png` | 80 → 133 navios/mês (introdução) |
| CSVs e `.dst` | Números dos gráficos, ajustes, atípicos e dados para o Input Analyzer (ver `GRAFICOS.md`) |
