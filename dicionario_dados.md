# Dicionário de Dados — Escalas de Navios

Tabela com as escalas (atracações) previstas de navios no porto, com dados do navio, origem/destino, terminal, cais e datas estimadas de chegada e saída.

## Campos

| # | Campo | Tipo | Formato | Descrição |
|---|-------|------|---------|-----------|
| 1 | `ANYESCALA` | int | `AAAA` | Ano da escala |
| 2 | `TERMINALCODI` | text | | Código do terminal de destino |
| 3 | `VAIXELLBANDERACODI` | text | | Código da bandeira do navio |
| 4 | `ETD` | timestamp | `AAAA/MM/DD HH:mm:SS` | Data e hora estimadas de saída (horário local) |
| 5 | `VAIXELLNOM` | text | | Nome do navio |
| 6 | `CALAT_METRES` | float | metros | Calado do navio |
| 7 | `MANEGA_METRES` | float | metros | Boca (largura) do navio |
| 8 | `MESINFO` | text | | Informações adicionais |
| 9 | `TERMINALNOM` | text | | Nome do terminal de destino |
| 10 | `ETAHORA` | time | `HH:mm` | Hora estimada de chegada |
| 11 | `ETAUTC` | timestamp | `AAAA/MM/DD HH:mm:SS` | Data e hora estimadas de chegada em UTC |
| 12 | `ETADIA` | date | `AAAA/MM/DD` | Data estimada de chegada |
| 13 | `ETDUTC` | timestamp | `AAAA/MM/DD HH:mm:SS` | Data e hora estimadas de saída em UTC |
| 14 | `VAIXELLTIPUS` | text | | Tipo do navio segundo a classificação Lloyd's |
| 15 | `ETDHORA` | time | `HH:mm` | Hora estimada de saída |
| 16 | `PORTDESTICODI` | text | | Código do porto de destino do navio |
| 17 | `MOLLCODI` | text | | Código do cais de atracação |
| 18 | `MMSI` | int | 9 dígitos | Código MMSI (Maritime Mobile Service Identity) do navio |
| 19 | `IMO` | text | 7 dígitos | Número IMO do navio (identificador único internacional) |
| 20 | `PORTORIGENCODI` | text | | Código do porto de origem da escala |
| 21 | `ESCALAESTAT` | text | | Estado da escala (descrição) |
| 22 | `ESLORA_METRES` | float | metros | Comprimento total do navio |
| 23 | `PORTORIGENNOM` | text | | Nome do porto de origem da escala |
| 24 | `PORTDESTINOM` | text | | Nome do porto de destino do navio |
| 25 | `ESTOPERATIUID` | text | | Código do estado da escala |
| 26 | `MOLLMODULS` | text | | Módulos do cais de atracação |
| 27 | `ESCALANUM` | text | | Número da escala |
| 28 | `ETDDIA` | date | `AAAA/MM/DD` | Data estimada de saída |
| 29 | `ETA` | timestamp | `AAAA/MM/DD HH:mm:SS` | Data e hora estimadas de chegada (horário local) ¹ |
| 30 | `VAIXELLBANDERANOM` | text | | Nome do país de bandeira do navio |
| 31 | `CONSIGNATARI` | text | | Empresa consignatária (agente) do navio |
| 32 | `CALLSIGN` | text | | Indicativo de chamada de rádio do navio |

> O CSV também traz uma coluna `_id` (inteiro de 10310 a 20618), que não está na documentação original:
> é o identificador sequencial do registro no portal de dados abertos e não tem significado para a análise.

## Valores das colunas categóricas

Contagens no CSV bruto (10.309 registros, antes da limpeza).

### `VAIXELLTIPUS`: tipo do navio

| Valor no CSV | Tradução | Registros | O que é |
|---|---|---|---|
| Transbordadors | Ferry | 3.270 | Linhas regulares de passageiros + veículos |
| Portacontenidors | Porta-contêineres | 2.531 | Carga em contêineres, movimentada por guindastes de cais (**recorte do modelo**) |
| Tancs | Navio-tanque | 1.887 | Produtos líquidos (químicos, combustíveis refinados) |
| Passatge | Passageiros (cruzeiro) | 896 | Navios de cruzeiro |
| Ro-Ro | Ro-Ro | 527 | *Roll-on/roll-off*: carga sobre rodas que entra e sai por rampa |
| Car-carrier | Transporte de veículos | 445 | Navios-garagem para automóveis |
| Càrrega (Lo-Lo) | Carga geral (Lo-Lo) | 417 | *Lift-on/lift-off*: carga geral içada por guindaste |
| Petroliers | Petroleiro | 174 | Petróleo bruto e derivados |
| Granelers | Graneleiro | 162 | Granéis sólidos (grãos, cimento, minério) |

### `ESCALAESTAT` e `ESTOPERATIUID`: estado da escala

`ESTOPERATIUID` é a sigla de `ESCALAESTAT` (uma corresponde exatamente à outra). Ordem típica do ciclo de uma escala:

| Sigla | Valor no CSV | Tradução | Registros | Significado |
|---|---|---|---|---|
| S | Sol·licitada | Solicitada | 29 | O agente pediu a escala; aguarda autorização |
| A | Autoritzada | Autorizada | 3 | A Autoridade Portuária aprovou a escala |
| C | Confirmada | Confirmada | 2 | Escala confirmada (horário/cais definidos) |
| P | Fondeig Previ | Fundeio prévio | 6 | O navio chegou e está fundeado, esperando para atracar |
| I | Iniciada | Iniciada | 46 | O navio está no porto; a escala está em andamento |
| F | Finalitzada | Finalizada | 10.223 | O navio já saiu; escala concluída |

### Terminais e cais

| Coluna | Como ler |
|---|---|
| `TERMINALCODI` / `TERMINALNOM` | 38 terminais. Os principais: `F2` TERMINAL F2 (1.678), `6212` **TERMINAL CATALUNYA SA** (1.365, terminal do modelo), `7083` APM TERMINALS BARCELONA (677), `F1` TERMINAL F1 (664), `8156` GRIMALDI TERMINAL BARCELONA (463). **Vazio em 1.427 registros** (escala sem terminal atribuído) |
| `MOLLCODI` | Código do cais de atracação (ex.: `36A` = cais do TCAT, com 1.348 das 1.365 escalas do terminal) |
| `MOLLMODULS` | Faixa de módulos (trechos numerados) do cais que o navio ocupa. Ex.: `3-7` = do módulo 3 ao 7. Vazio em 1.449 registros |

### Portos, bandeiras e identificação

| Coluna | Como ler |
|---|---|
| `PORTORIGENCODI` / `PORTDESTICODI` | Código UN/LOCODE de 5 letras: 2 do país + 3 do local (ex.: `ESCAS` = Espanha, Castellón; `TRDIK` = Turquia, Dikili). **`ZZZZZ` = desconhecido** (449 registros no destino) |
| `PORTORIGENNOM` / `PORTDESTINOM` | Nome do porto; `Desconegut` = desconhecido |
| `VAIXELLBANDERACODI` | Código de 2 letras do país de bandeira (ex.: `LR` = Libéria, `MT` = Malta, `PA` = Panamá) |
| `VAIXELLBANDERANOM` | Nome do país **em catalão** (ex.: Libèria, Panamà, Antigua i Barbuda) |
| `ESCALANUM` | Número da escala + sufixo (ex.: `60958-1`). O sufixo vai de 1 a 5 (é 1 em 83% dos registros); o dataset não documenta o seu significado. **187 números aparecem duas vezes** (a mesma escala listada em dois terminais) |
| `MESINFO` | Na prática, é um **link para a página do navio no MarineTraffic** (ex.: `https://www.marinetraffic.com/en/ais/details/ships/mmsi:636020366`) |
| `MMSI` | Lido como número decimal (ex.: `636020366.0`); o `.0` não tem significado |

### Datas e medidas

| Coluna | Como ler |
|---|---|
| `ETA`, `ETD` | **Horário local de Barcelona.** `ETA − ETAUTC` = 1 h no inverno e 2 h no verão (horário de verão europeu) |
| `ANYESCALA` | Ano da escala. **700 registros têm 2024**, mas todos chegam (ETA) em 2025, provavelmente escalas registradas ainda em 2024 |
| `CALAT_METRES`, `MANEGA_METRES`, `ESLORA_METRES` | Em metros, com **vírgula decimal** no CSV (`"10,02"`). A boca (`MANEGA_METRES`) **falta em 63%** dos registros; o calado é `0` em 13 registros (valor faltante gravado como zero) |

O tratamento de cada um desses problemas está em `analise/resultados/1_dados_limpos/LIMPEZA.md`.

## Glossário

| Sigla / termo | Significado |
|---------------|-------------|
| ETA | *Estimated Time of Arrival* — hora estimada de chegada |
| ETD | *Estimated Time of Departure* — hora estimada de saída |
| UTC | Tempo Universal Coordenado |
| Escala | Passagem de um navio pelo porto, da chegada à saída |
| Calado | Distância vertical entre a linha d'água e o ponto mais baixo do casco |
| Boca (manga) | Largura máxima do navio |
| Eslora | Comprimento total do navio |
| Consignatário | Empresa que representa o armador no porto |
| MMSI | Identificador usado em rádio e AIS |
| IMO | Número permanente atribuído pela Organização Marítima Internacional |

## Observações

1. Na fonte original, `ETA` está descrito como "data e hora estimada de **saída**". Pelo nome do campo e pela relação com `ETADIA`/`ETAHORA`, trata-se da **chegada**; a descrição foi corrigida aqui.
2. Os nomes dos campos estão em catalão (ex.: *vaixell* = navio, *moll* = cais, *codi* = código, *nom* = nome, *any* = ano).
3. `ETA`/`ETD` e seus desdobramentos (`*DIA`, `*HORA`) são redundantes entre si; `ETAUTC`/`ETDUTC` são as mesmas datas convertidas para UTC.
