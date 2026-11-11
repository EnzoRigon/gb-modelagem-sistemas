# Log de limpeza dos dados

- Registros no CSV bruto: **10309**
- Escalas duplicadas (mesmo `ESCALANUM` listado em dois terminais): **187** → mantida 1 cópia
- Escalas não concluídas (`ESCALAESTAT` ≠ Finalitzada): **84** → removidas
- Escalas válidas no porto inteiro: **10038**
- Recorte do modelo (porta-contêineres em TCAT, APM, PNOU): **2141** escalas
- Período coberto (ETA): 01/01/2025 a 31/12/2025
  - APM: limite superior 3×IQR = 48.9 h → 5 escalas marcadas como atípicas
  - PNOU: limite superior 3×IQR = 117.9 h → 0 escalas marcadas como atípicas
  - TCAT: limite superior 3×IQR = 69.5 h → 26 escalas marcadas como atípicas
- Operação no cais ≤ 0 após descontar manobras: 0 escalas (marcadas como atípicas)

## Variáveis geradas

| Variável        | Descrição                                                                   | Unidade   | Origem           | Método de obtenção                                                                           |   N observações |
|:----------------|:----------------------------------------------------------------------------|:----------|:-----------------|:---------------------------------------------------------------------------------------------|----------------:|
| TEC_GERAL       | Tempo entre chegadas consecutivas de porta-contêineres (todos os terminais) | h         | Real             | Registro histórico — Autoritat Portuària de Barcelona (dados abertos, 2025)                  |            2140 |
| TEC_TCAT        | Tempo entre chegadas no terminal TCAT                                       | h         | Real             | Registro histórico — Autoritat Portuària de Barcelona (dados abertos, 2025)                  |            1289 |
| TEC_APM         | Tempo entre chegadas no terminal APM                                        | h         | Real             | Registro histórico — Autoritat Portuària de Barcelona (dados abertos, 2025)                  |             656 |
| TEC_PNOU        | Tempo entre chegadas no terminal PNOU                                       | h         | Real             | Registro histórico — Autoritat Portuària de Barcelona (dados abertos, 2025)                  |             193 |
| PERM_GERAL      | Permanência no porto (ETD − ETA), sem atípicos                              | h         | Real             | Registro histórico — Autoritat Portuària de Barcelona (dados abertos, 2025)                  |            2110 |
| OPER_GERAL      | Operação no cais (permanência − manobras), sem atípicos                     | h         | Real − sintético | Derivado: permanência real menos manobras sintéticas                                         |            2110 |
| OPER_TCAT       | Operação no cais no terminal TCAT, sem atípicos                             | h         | Real − sintético | Derivado: permanência real menos manobras sintéticas                                         |            1264 |
| OPER_APM        | Operação no cais no terminal APM, sem atípicos                              | h         | Real − sintético | Derivado: permanência real menos manobras sintéticas                                         |             652 |
| OPER_PNOU       | Operação no cais no terminal PNOU, sem atípicos                             | h         | Real − sintético | Derivado: permanência real menos manobras sintéticas                                         |             194 |
| ESLORA          | Comprimento do navio                                                        | m         | Real             | Registro histórico — Autoritat Portuària de Barcelona (dados abertos, 2025)                  |            2141 |
| CALADO          | Calado do navio                                                             | m         | Real             | Registro histórico — Autoritat Portuària de Barcelona (dados abertos, 2025)                  |            2141 |
| MANOBRA_ENTRADA | Manobra de entrada/atracação (prático + rebocadores)                        | h         | SINTÉTICO        | Gerado por modelo físico (parcela fixa + proporcional à eslora + ruído normal), semente 2026 |            2141 |
| MANOBRA_SAIDA   | Manobra de desatracação/saída (prático + rebocadores)                       | h         | SINTÉTICO        | Gerado por modelo físico (parcela fixa + proporcional à eslora + ruído normal), semente 2026 |            2141 |