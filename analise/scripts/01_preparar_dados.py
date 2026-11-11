"""ETAPA 2 — Coleta e organização dos dados.

Entrada : CSV bruto de escalas do Porto de Barcelona (2025).
Saídas  : resultados/01_dados/
  - base_dados_modelo.xlsx  -> planilha entregável (metadados + todas as variáveis)
  - escalas_conteineres.csv -> escalas limpas do recorte do modelo
  - variaveis/*.dst         -> 1 valor por linha, para abrir no Arena Input Analyzer
  - log_limpeza.md          -> o que foi removido e por quê
"""
import numpy as np
import pandas as pd

from comum import (SEMENTE, TERMINAIS, carregar_bruto, limites_iqr, limpar_porto, pasta,
                   recorte_conteineres, tec_horas, ORDEM_TERM)

OUT = pasta("01_dados")
(OUT / "variaveis").mkdir(exist_ok=True)
log = ["# Log de limpeza dos dados\n"]

bruto = carregar_bruto()
log.append(f"- Registros no CSV bruto: **{len(bruto)}**")
n_dup = bruto["ESCALANUM"].duplicated().sum()
log.append(f"- Escalas duplicadas (mesmo `ESCALANUM` listado em dois terminais): **{n_dup}** → mantida 1 cópia")
log.append(f"- Escalas não concluídas (`ESCALAESTAT` ≠ Finalitzada): "
           f"**{(bruto.drop_duplicates('ESCALANUM')['ESCALAESTAT'] != 'Finalitzada').sum()}** → removidas")
porto = limpar_porto(bruto)
log.append(f"- Escalas válidas no porto inteiro: **{len(porto)}**")

cont = recorte_conteineres(porto)
log.append(f"- Recorte do modelo (porta-contêineres em {', '.join(TERMINAIS.values())}): **{len(cont)}** escalas")
log.append(f"- Período coberto (ETA): {cont.ETA.min():%d/%m/%Y} a {cont.ETA.max():%d/%m/%Y}")

# ---------------------------------------------------------------------------
# Valores atípicos de permanência: regra 3×IQR por terminal (outlier extremo).
# Estadias muito longas costumam ser reparos, paradas técnicas ou espera
# comercial — não fazem parte da operação normal de carga/descarga.
# ---------------------------------------------------------------------------
cont["OUTLIER_PERM"] = False
for t, g in cont.groupby("TERMINAL"):
    _, sup = limites_iqr(g["PERM_H"], k=3)
    cont.loc[g.index, "OUTLIER_PERM"] = g["PERM_H"] > sup
    log.append(f"  - {t}: limite superior 3×IQR = {sup:.1f} h → {(g['PERM_H'] > sup).sum()} escalas marcadas como atípicas")

# ---------------------------------------------------------------------------
# DADOS SINTÉTICOS — tempos de manobra (praticagem + reboque).
# O dataset não registra manobras. Hipótese física: tempo = parcela fixa
# (embarque do prático, amarração) + parcela proporcional ao comprimento + ruído.
#   Entrada: 0,30 h + 0,0020 h/m × eslora + N(0; 0,08)   (≈ 36–80 min)
#   Saída  : 0,20 h + 0,0017 h/m × eslora + N(0; 0,07)   (≈ 25–65 min)
# Mínimo de 0,25 h. As escalas reais fornecem a eslora de cada navio.
# ---------------------------------------------------------------------------
rng = np.random.default_rng(SEMENTE)
L = cont["ESLORA_METRES"].to_numpy()
cont["MAN_ENT_H"] = np.maximum(0.25, 0.30 + 0.0020 * L + rng.normal(0, 0.08, len(L))).round(3)
cont["MAN_SAI_H"] = np.maximum(0.25, 0.20 + 0.0017 * L + rng.normal(0, 0.07, len(L))).round(3)
# Tempo de operação no cais = permanência total − manobras (derivado)
cont["OPER_H"] = (cont["PERM_H"] - cont["MAN_ENT_H"] - cont["MAN_SAI_H"]).round(3)
log.append(f"- Operação no cais ≤ 0 após descontar manobras: {(cont['OPER_H'] <= 0).sum()} escalas (marcadas como atípicas)")
cont.loc[cont["OPER_H"] <= 0, "OUTLIER_PERM"] = True

cols = ["ESCALANUM", "VAIXELLNOM", "IMO", "TERMINAL", "TERMINALNOM", "MOLLCODI", "ETA", "ETD",
        "PERM_H", "OUTLIER_PERM", "ESLORA_METRES", "CALAT_METRES", "MANEGA_METRES", "CLASSE",
        "N_REBOC", "MAN_ENT_H", "MAN_SAI_H", "OPER_H", "PORTORIGENNOM", "PORTDESTINOM",
        "VAIXELLBANDERANOM", "CONSIGNATARI"]
cont[cols].to_csv(OUT / "escalas_conteineres.csv", index=False)
porto.to_csv(OUT / "escalas_porto_limpo.csv", index=False)

# ---------------------------------------------------------------------------
# Variáveis do modelo (uma série por variável)
# ---------------------------------------------------------------------------
ok = cont[~cont["OUTLIER_PERM"]]
var = {
    "TEC_GERAL": (tec_horas(cont["ETA"]), "h", "Real", "Tempo entre chegadas consecutivas de porta-contêineres (todos os terminais)"),
    **{f"TEC_{t}": (tec_horas(cont.loc[cont.TERMINAL == t, "ETA"]), "h", "Real",
                    f"Tempo entre chegadas no terminal {t}") for t in ORDEM_TERM},
    "PERM_GERAL": (ok["PERM_H"], "h", "Real", "Permanência no porto (ETD − ETA), sem atípicos"),
    "OPER_GERAL": (ok["OPER_H"], "h", "Real − sintético", "Operação no cais (permanência − manobras), sem atípicos"),
    **{f"OPER_{t}": (ok.loc[ok.TERMINAL == t, "OPER_H"], "h", "Real − sintético",
                     f"Operação no cais no terminal {t}, sem atípicos") for t in ORDEM_TERM},
    "ESLORA": (cont["ESLORA_METRES"], "m", "Real", "Comprimento do navio"),
    "CALADO": (cont["CALAT_METRES"], "m", "Real", "Calado do navio"),
    "MANOBRA_ENTRADA": (cont["MAN_ENT_H"], "h", "SINTÉTICO", "Manobra de entrada/atracação (prático + rebocadores)"),
    "MANOBRA_SAIDA": (cont["MAN_SAI_H"], "h", "SINTÉTICO", "Manobra de desatracação/saída (prático + rebocadores)"),
}
meta = []
for nome, (s, un, origem, desc) in var.items():
    s = pd.Series(s).reset_index(drop=True)
    np.savetxt(OUT / "variaveis" / f"{nome}.dst", s.to_numpy(), fmt="%.4f")
    metodo = {"Real": "Registro histórico — Autoritat Portuària de Barcelona (dados abertos, 2025)",
              "SINTÉTICO": "Gerado por modelo físico (parcela fixa + proporcional à eslora + ruído normal), semente 2026",
              "Real − sintético": "Derivado: permanência real menos manobras sintéticas"}[origem]
    meta.append({"Variável": nome, "Descrição": desc, "Unidade": un, "Origem": origem,
                 "Método de obtenção": metodo, "N observações": len(s)})
meta = pd.DataFrame(meta)

with pd.ExcelWriter(OUT / "base_dados_modelo.xlsx") as xw:
    meta.to_excel(xw, sheet_name="LEIA-ME", index=False)
    cont[cols].to_excel(xw, sheet_name="escalas_conteineres", index=False)
    for nome, (s, *_rest) in var.items():
        pd.DataFrame({nome: pd.Series(s).reset_index(drop=True)}).to_excel(xw, sheet_name=nome[:31], index=False)

log.append("\n## Variáveis geradas\n")
log.append(meta.to_markdown(index=False))
(OUT / "log_limpeza.md").write_text("\n".join(log), encoding="utf-8")
print("\n".join(log))
