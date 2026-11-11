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
