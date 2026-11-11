# Limpeza e organização dos dados

> Gerado automaticamente por `analise/scripts/1_limpeza_dados.py`. Os números abaixo saem do próprio código.

## Origem dos dados

| Item | Descrição |
|---|---|
| Fonte | Autoritat Portuària de Barcelona — portal de dados abertos, conjunto de **escalas de navios** |
| Arquivo | `b8966d7a-d570-4256-bd1b-b5757ad3a0d6.csv` (raiz do projeto) |
| Período | Chegadas (ETA) de 01/01/2025 a 31/12/2025 |
| Tamanho | 10,309 registros × 33 colunas |
| Método de obtenção | **Registro histórico** (fonte secundária). Nenhum dado é sintético |
| Significado de cada coluna | ver `dicionario_dados.md` na raiz do projeto |

## Procedimento de limpeza (passo a passo)

|   Passo | Ação                                                             | Motivo                                                                                                                                             |   Registros restantes |   Removidos |
|--------:|:-----------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------|----------------------:|------------:|
|       0 | Leitura do CSV bruto                                             | Dados abertos da Autoridade Portuária de Barcelona, 33 colunas                                                                                     |                 10309 |           0 |
|       1 | Remover escalas duplicadas (mesmo ESCALANUM)                     | A mesma escala aparece listada em dois terminais (ex.: SETRAM e AUTOTERMINAL); manter 1 cópia                                                      |                 10122 |         187 |
|       2 | Remover registros sem ETA ou ETD                                 | Sem as datas não há como calcular intervalos nem permanência                                                                                       |                 10122 |           0 |
|       3 | Remover permanência ≤ 0 (ETD antes da ETA)                       | Erro de digitação/registro                                                                                                                         |                 10122 |           0 |
|       4 | Manter chegadas (ETA) em 2025                                    | Período de estudo = ano de 2025                                                                                                                    |                 10122 |           0 |
|       5 | Manter todos os estados da escala (não remove nada)              | Toda escala pedida representa demanda; filtrar só as 'Finalitzada' esvaziaria dezembro (escalas do fim do ano ainda em andamento na extração)      |                 10122 |           0 |
|       6 | Recorte: só o Terminal Catalunya (TCAT)                          | Terminal escolhido para o modelo                                                                                                                   |                  1365 |        8757 |
|       7 | Recorte: só navios porta-contêineres                             | Remove 37 navios de carga geral (Lo-Lo) que também atracam no TCAT                                                                                 |                  1328 |          37 |
|       8 | Marcar atípicos de permanência por grupo de tamanho (não remove) | Regra de Tukey: moderado > Q3 + 1,5×IQR; extremo > Q3 + 3×IQR. Extremos ficam fora do ajuste de distribuição, mas continuam contando como chegadas |                  1328 |           0 |

**Resultado:** 10,122 escalas válidas no porto inteiro (`escalas_porto_limpas.csv`) e
**1,328 escalas** de porta-contêineres no TCAT (`escalas_TCAT_conteineres.csv`), a base do modelo.

Estados das escalas mantidas no TCAT: Finalizada: 1290, Solicitada: 29, Iniciada: 4, Autorizada: 2, Confirmada: 2, Fundeio prévio: 1.

## Qualidade do CSV bruto

Colunas com problemas (lista completa em `qualidade_dados_brutos.csv`):

| Coluna        |   Valores ausentes |   % ausente | Observação                                                                                   |
|:--------------|-------------------:|------------:|:---------------------------------------------------------------------------------------------|
| ANYESCALA     |                  0 |        0    | 700 escalas com ano 2024 mas chegada em 2025 (provavelmente escala registrada ainda em 2024) |
| TERMINALCODI  |               1427 |       13.84 | Escala sem terminal atribuído no registro (o dataset não informa o motivo); não afeta o TCAT |
| CALAT_METRES  |                  0 |        0    | 13 registros com calado = 0 (valor faltante gravado como zero)                               |
| MANEGA_METRES |               6537 |       63.41 | Boca (largura) não informada na maioria dos registros; NÃO usada na análise                  |
| MESINFO       |                 18 |        0.17 | Link do MarineTraffic ausente; não afeta a análise                                           |
| TERMINALNOM   |               1427 |       13.84 | Idem TERMINALCODI                                                                            |
| PORTDESTICODI |                  0 |        0    | 449 registros com destino 'ZZZZZ' = desconhecido                                             |
| MMSI          |                 18 |        0.17 | Identificador de rádio ausente; não afeta a análise                                          |
| MOLLMODULS    |               1449 |       14.06 | Módulos do cais não informados                                                               |
| ESCALANUM     |                  0 |        0    | 187 números de escala repetidos (mesma escala em 2 terminais)                                |
| ETA           |                  0 |        0    | Horário local de Barcelona; difere de ETAUTC em 1 h (inverno) ou 2 h (verão)                 |

Nenhum desses problemas afeta as 3 variáveis do modelo (ETA, ETD e ESLORA_METRES estão 100% preenchidas no TCAT).

## Arquivos gerados

| Arquivo | Linhas | O que é |
|---|---|---|
| `escalas_porto_limpas.csv` | 10,122 | Porto inteiro, limpo. Todas as colunas originais + as colunas criadas abaixo. Usado no panorama por tipo de navio |
| `escalas_TCAT_conteineres.csv` | 1,328 | **Base do modelo.** Usado para gerar os 5 gráficos |
| `base_dados_TCAT.xlsx` | — | **Planilha para entregar**: abas `LEIA-ME` (variáveis, unidade, origem, método), `escalas_TCAT`, `log_limpeza`, `qualidade_dados_brutos` |
| `qualidade_dados_brutos.csv` | 33 | Diagnóstico de cada coluna do CSV bruto |

## Colunas criadas na limpeza

As colunas originais mantêm o nome do CSV bruto (em catalão; ver `dicionario_dados.md`). As colunas novas são:

| Coluna | Tipo | Significado |
|---|---|---|
| `TIPO_NAVIO` | texto | Tipo do navio traduzido para português (de `VAIXELLTIPUS`) |
| `ESTADO_ESCALA` | texto | Estado da escala traduzido (de `ESCALAESTAT`) |
| `CONCLUIDA` | sim/não | `True` se a escala já terminou (estado Finalizada) |
| `MES` | inteiro 1–12 | Mês da chegada (ETA) |
| `PERM_H` | horas | **Permanência no porto/berço** = ETD − ETA |
| `INTERVALO_CHEGADA_H` | horas | **Intervalo entre chegadas** = ETA do navio − ETA do navio anterior no TCAT. Vazio na 1ª linha (não há navio anterior) |
| `GRUPO_TAMANHO` | texto | `< 300 m` ou `>= 300 m`, pela `ESLORA_METRES` |
| `ATIPICO_MODERADO` | sim/não | Permanência acima de Q3 + 1,5×IQR **do seu grupo de tamanho** (59 navios) |
| `ATIPICO_EXTREMO` | sim/não | Permanência acima de Q3 + 3×IQR do seu grupo (19 navios). Ficam fora do ajuste de distribuição |

As 4 últimas (`INTERVALO_CHEGADA_H` em diante) existem só em `escalas_TCAT_conteineres.csv`. A tabela do modelo mantém só as colunas úteis
(identificação, datas, as 3 variáveis, origem/destino, bandeira e consignatário).

## As 3 variáveis do estudo (requisito: ≥ 200 observações cada)

| Variável            | Descrição                                                              | Unidade   |    N | Origem             | Método                      |
|:--------------------|:-----------------------------------------------------------------------|:----------|-----:|:-------------------|:----------------------------|
| INTERVALO_CHEGADA_H | Tempo entre a chegada de um navio e a do anterior (ETA − ETA anterior) | horas     | 1327 | Registro histórico | Derivado das ETAs ordenadas |
| PERM_H              | Permanência no berço (ETD − ETA)                                       | horas     | 1328 | Registro histórico | Derivado de ETD e ETA       |
| ESLORA_METRES       | Comprimento total do navio                                             | metros    | 1328 | Registro histórico | Coluna original             |

## Hipóteses e limitações

- **ETA e ETD são horários estimados/programados** informados à Autoridade Portuária, não horários medidos por
  satélite (AIS). O dataset não informa se, nas escalas concluídas, eles foram substituídos pelos horários efetivos.
- A permanência (ETD − ETA) inclui as manobras de entrada/saída e eventual espera; o dataset não separa essas etapas.
- Escalas não concluídas (solicitadas, autorizadas etc.) foram mantidas como demanda; a permanência delas é a programada.
- A boca (`MANEGA_METRES`) e o calado (`CALAT_METRES`) não foram usados: a boca falta em mais da metade do porto.
