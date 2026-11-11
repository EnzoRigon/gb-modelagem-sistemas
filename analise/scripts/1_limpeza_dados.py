"""PASSO 1 — Limpeza e organização dos dados (Etapa 2 do enunciado).

Entrada : CSV bruto de escalas do Porto de Barcelona (2025), na raiz do projeto.
Saídas em analise/resultados/1_dados_limpos/:
  - escalas_porto_limpas.csv     -> porto inteiro, limpo, com colunas traduzidas/derivadas
  - escalas_TCAT_conteineres.csv -> BASE DO MODELO: porta-contêineres no Terminal Catalunya
  - base_dados_TCAT.xlsx         -> planilha entregável (LEIA-ME + dados + log)
  - qualidade_dados_brutos.csv   -> valores ausentes/problemas por coluna do CSV bruto
  - LIMPEZA.md                   -> procedimento passo a passo + explicação das colunas criadas
"""
import numpy as np
import pandas as pd

from comum import TRAD_ESTADO, TRAD_TIPO, carregar_bruto, limites_iqr, pasta

OUT = pasta("1_dados_limpos")
CORTE = 300  # m — divide navios "menores" e "maiores"
passos = []  # (etapa, descrição, motivo, registros restantes, removidos)


def passo(desc, motivo, df, antes):
    passos.append({"Passo": len(passos), "Ação": desc, "Motivo": motivo,
                   "Registros restantes": len(df), "Removidos": antes - len(df)})


# ---------------------------------------------------------------- 0. leitura e diagnóstico
bruto = carregar_bruto()
n0 = len(bruto)
passo("Leitura do CSV bruto", "Dados abertos da Autoridade Portuária de Barcelona, 33 colunas", bruto, n0)

eta_utc = pd.to_datetime(bruto["ETAUTC"], errors="coerce")
qual = pd.DataFrame({
    "Coluna": bruto.columns.drop("PERM_H"),
    "Valores ausentes": [int(bruto[c].isna().sum()) for c in bruto.columns.drop("PERM_H")],
})
qual["% ausente"] = (100 * qual["Valores ausentes"] / n0).round(2)
qual["Valores distintos"] = [bruto[c].nunique() for c in qual.Coluna]
obs = {
    "MANEGA_METRES": "Boca (largura) não informada na maioria dos registros; NÃO usada na análise",
    "TERMINALCODI": "Escala sem terminal atribuído no registro (o dataset não informa o motivo); não afeta o TCAT",
    "TERMINALNOM": "Idem TERMINALCODI",
    "MOLLMODULS": "Módulos do cais não informados",
    "MMSI": "Identificador de rádio ausente; não afeta a análise",
    "MESINFO": "Link do MarineTraffic ausente; não afeta a análise",
    "CALAT_METRES": f"{int((bruto.CALAT_METRES == 0).sum())} registros com calado = 0 (valor faltante gravado como zero)",
    "PORTDESTICODI": f"{int((bruto.PORTDESTICODI == 'ZZZZZ').sum())} registros com destino 'ZZZZZ' = desconhecido",
    "ESCALANUM": f"{int(bruto.ESCALANUM.duplicated().sum())} números de escala repetidos (mesma escala em 2 terminais)",
    "ETA": "Horário local de Barcelona; difere de ETAUTC em 1 h (inverno) ou 2 h (verão)",
    "ANYESCALA": f"{int((bruto.ANYESCALA == 2024).sum())} escalas com ano 2024 mas chegada em 2025 (provavelmente escala registrada ainda em 2024)",
}
qual["Observação"] = qual.Coluna.map(obs).fillna("")
qual.to_csv(OUT / "qualidade_dados_brutos.csv", index=False)

# ---------------------------------------------------------------- 1. limpeza do porto inteiro
d = bruto.drop_duplicates("ESCALANUM")
passo("Remover escalas duplicadas (mesmo ESCALANUM)",
      "A mesma escala aparece listada em dois terminais (ex.: SETRAM e AUTOTERMINAL); manter 1 cópia", d, n0)
antes = len(d)
d = d.dropna(subset=["ETA", "ETD"])
passo("Remover registros sem ETA ou ETD", "Sem as datas não há como calcular intervalos nem permanência", d, antes)
antes = len(d)
d = d[d.PERM_H > 0]
passo("Remover permanência ≤ 0 (ETD antes da ETA)", "Erro de digitação/registro", d, antes)
antes = len(d)
d = d[d.ETA.dt.year == 2025]
passo("Manter chegadas (ETA) em 2025", "Período de estudo = ano de 2025", d, antes)
passo("Manter todos os estados da escala (não remove nada)",
      "Toda escala pedida representa demanda; filtrar só as 'Finalitzada' esvaziaria dezembro "
      "(escalas do fim do ano ainda em andamento na extração)", d, len(d))

d = d.sort_values("ETA").reset_index(drop=True).copy()
d["TIPO_NAVIO"] = d.VAIXELLTIPUS.map(TRAD_TIPO).fillna(d.VAIXELLTIPUS)
d["ESTADO_ESCALA"] = d.ESCALAESTAT.map(TRAD_ESTADO).fillna(d.ESCALAESTAT)
d["CONCLUIDA"] = d.ESCALAESTAT == "Finalitzada"
d["MES"] = d.ETA.dt.month
d["TERMINALNOM"] = d.TERMINALNOM.fillna("(sem terminal)")
d["PERM_H"] = d.PERM_H.round(4)
d.to_csv(OUT / "escalas_porto_limpas.csv", index=False)
n_porto = len(d)

# ---------------------------------------------------------------- 2. recorte do modelo (TCAT)
antes = len(d)
t = d[d.TERMINALNOM == "TERMINAL CATALUNYA SA"]
passo("Recorte: só o Terminal Catalunya (TCAT)", "Terminal escolhido para o modelo", t, antes)
antes = len(t)
t = t[t.VAIXELLTIPUS == "Portacontenidors"].copy()
passo("Recorte: só navios porta-contêineres",
      f"Remove {antes - len(t)} navios de carga geral (Lo-Lo) que também atracam no TCAT", t, antes)

t = t.sort_values("ETA").reset_index(drop=True)
t["INTERVALO_CHEGADA_H"] = t.ETA.diff().dt.total_seconds().div(3600).round(4)
t["GRUPO_TAMANHO"] = np.where(t.ESLORA_METRES >= CORTE, f">= {CORTE} m", f"< {CORTE} m")
t["ATIPICO_MODERADO"] = False
t["ATIPICO_EXTREMO"] = False
for g, sub in t.groupby("GRUPO_TAMANHO"):
    _, sup15 = limites_iqr(sub.PERM_H, 1.5)
    _, sup3 = limites_iqr(sub.PERM_H, 3)
    t.loc[sub.index, "ATIPICO_MODERADO"] = sub.PERM_H > sup15
    t.loc[sub.index, "ATIPICO_EXTREMO"] = sub.PERM_H > sup3
passo("Marcar atípicos de permanência por grupo de tamanho (não remove)",
      "Regra de Tukey: moderado > Q3 + 1,5×IQR; extremo > Q3 + 3×IQR. Extremos ficam fora do ajuste "
      "de distribuição, mas continuam contando como chegadas", t, len(t))

COLS_MODELO = ["ESCALANUM", "VAIXELLNOM", "IMO", "TIPO_NAVIO", "ESTADO_ESCALA", "CONCLUIDA", "MOLLCODI",
               "ETA", "ETD", "MES", "INTERVALO_CHEGADA_H", "PERM_H", "ESLORA_METRES", "CALAT_METRES",
               "GRUPO_TAMANHO", "ATIPICO_MODERADO", "ATIPICO_EXTREMO", "PORTORIGENNOM", "PORTDESTINOM",
               "VAIXELLBANDERANOM", "CONSIGNATARI"]
t[COLS_MODELO].to_csv(OUT / "escalas_TCAT_conteineres.csv", index=False)

# ---------------------------------------------------------------- 3. planilha entregável
variaveis = pd.DataFrame([
    {"Variável": "INTERVALO_CHEGADA_H", "Descrição": "Tempo entre a chegada de um navio e a do anterior (ETA − ETA anterior)",
     "Unidade": "horas", "N": int(t.INTERVALO_CHEGADA_H.notna().sum()),
     "Origem": "Registro histórico", "Método": "Derivado das ETAs ordenadas"},
    {"Variável": "PERM_H", "Descrição": "Permanência no berço (ETD − ETA)", "Unidade": "horas",
     "N": len(t), "Origem": "Registro histórico", "Método": "Derivado de ETD e ETA"},
    {"Variável": "ESLORA_METRES", "Descrição": "Comprimento total do navio", "Unidade": "metros",
     "N": len(t), "Origem": "Registro histórico", "Método": "Coluna original"},
])
variaveis["Fonte"] = "Autoritat Portuària de Barcelona — dados abertos de escalas, 2025"
log = pd.DataFrame(passos)
with pd.ExcelWriter(OUT / "base_dados_TCAT.xlsx") as xw:
    variaveis.to_excel(xw, sheet_name="LEIA-ME", index=False)
    t[COLS_MODELO].to_excel(xw, sheet_name="escalas_TCAT", index=False)
    log.to_excel(xw, sheet_name="log_limpeza", index=False)
    qual.to_excel(xw, sheet_name="qualidade_dados_brutos", index=False)

# ---------------------------------------------------------------- 4. documentação
n_mod = int(t.ATIPICO_MODERADO.sum()); n_ext = int(t.ATIPICO_EXTREMO.sum())
estados = t.ESTADO_ESCALA.value_counts()
md = f"""# Limpeza e organização dos dados

> Gerado automaticamente por `analise/scripts/1_limpeza_dados.py`. Os números abaixo saem do próprio código.

## Origem dos dados

| Item | Descrição |
|---|---|
| Fonte | Autoritat Portuària de Barcelona — portal de dados abertos, conjunto de **escalas de navios** |
| Arquivo | `b8966d7a-d570-4256-bd1b-b5757ad3a0d6.csv` (raiz do projeto) |
| Período | Chegadas (ETA) de 01/01/2025 a 31/12/2025 |
| Tamanho | {n0:,} registros × 33 colunas |
| Método de obtenção | **Registro histórico** (fonte secundária). Nenhum dado é sintético |
| Significado de cada coluna | ver `dicionario_dados.md` na raiz do projeto |

## Procedimento de limpeza (passo a passo)

{log.to_markdown(index=False)}

**Resultado:** {n_porto:,} escalas válidas no porto inteiro (`escalas_porto_limpas.csv`) e
**{len(t):,} escalas** de porta-contêineres no TCAT (`escalas_TCAT_conteineres.csv`), a base do modelo.

Estados das escalas mantidas no TCAT: {', '.join(f'{k}: {v}' for k, v in estados.items())}.

## Qualidade do CSV bruto

Colunas com problemas (lista completa em `qualidade_dados_brutos.csv`):

{qual[qual['Observação'] != ''][['Coluna', 'Valores ausentes', '% ausente', 'Observação']].to_markdown(index=False)}

Nenhum desses problemas afeta as 3 variáveis do modelo (ETA, ETD e ESLORA_METRES estão 100% preenchidas no TCAT).

## Arquivos gerados

| Arquivo | Linhas | O que é |
|---|---|---|
| `escalas_porto_limpas.csv` | {n_porto:,} | Porto inteiro, limpo. Todas as colunas originais + as colunas criadas abaixo. Usado no panorama por tipo de navio |
| `escalas_TCAT_conteineres.csv` | {len(t):,} | **Base do modelo.** Usado para gerar os 5 gráficos |
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
| `GRUPO_TAMANHO` | texto | `< {CORTE} m` ou `>= {CORTE} m`, pela `ESLORA_METRES` |
| `ATIPICO_MODERADO` | sim/não | Permanência acima de Q3 + 1,5×IQR **do seu grupo de tamanho** ({n_mod} navios) |
| `ATIPICO_EXTREMO` | sim/não | Permanência acima de Q3 + 3×IQR do seu grupo ({n_ext} navios). Ficam fora do ajuste de distribuição |

As 4 últimas (`INTERVALO_CHEGADA_H` em diante) existem só em `escalas_TCAT_conteineres.csv`. A tabela do modelo mantém só as colunas úteis
(identificação, datas, as 3 variáveis, origem/destino, bandeira e consignatário).

## As 3 variáveis do estudo (requisito: ≥ 200 observações cada)

{variaveis.drop(columns='Fonte').to_markdown(index=False)}

## Hipóteses e limitações

- **ETA e ETD são horários estimados/programados** informados à Autoridade Portuária, não horários medidos por
  satélite (AIS). O dataset não informa se, nas escalas concluídas, eles foram substituídos pelos horários efetivos.
- A permanência (ETD − ETA) inclui as manobras de entrada/saída e eventual espera; o dataset não separa essas etapas.
- Escalas não concluídas (solicitadas, autorizadas etc.) foram mantidas como demanda; a permanência delas é a programada.
- A boca (`MANEGA_METRES`) e o calado (`CALAT_METRES`) não foram usados: a boca falta em mais da metade do porto.
"""
(OUT / "LIMPEZA.md").write_text(md, encoding="utf-8")
print(log.to_string(index=False))
