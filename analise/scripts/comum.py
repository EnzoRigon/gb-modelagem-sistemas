"""Funções e constantes compartilhadas por todos os scripts da análise.

Carrega o CSV bruto do Porto de Barcelona, faz a limpeza básica e define
o recorte usado no modelo (navios porta-contêineres nos 3 terminais de contêineres).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]          # pasta gbfinal/
CSV_BRUTO = RAIZ / "b8966d7a-d570-4256-bd1b-b5757ad3a0d6.csv"
RES = RAIZ / "analise" / "resultados"

SEMENTE = 2026  # semente fixa -> dados sintéticos reprodutíveis

# Terminais de contêineres e seus códigos curtos usados no modelo Arena
TERMINAIS = {
    "TERMINAL CATALUNYA SA": "TCAT",
    "APM TERMINALS BARCELONA, S.L.U.": "APM",
    "TERMINAL PORT NOU SA": "PNOU",
}
ORDEM_TERM = ["TCAT", "APM", "PNOU"]

# Hipótese de número de rebocadores por classe de comprimento (eslora)
CLASSES_ESLORA = [(0, 150, "Pequeno (<150 m)", 1),
                  (150, 250, "Médio (150–250 m)", 2),
                  (250, 1e9, "Grande (≥250 m)", 3)]

plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 150, "font.size": 10,
                     "axes.grid": True, "grid.alpha": .3,
                     "axes.spines.top": False, "axes.spines.right": False})


def pasta(nome: str) -> Path:
    p = RES / nome
    p.mkdir(parents=True, exist_ok=True)
    return p


def carregar_bruto() -> pd.DataFrame:
    df = pd.read_csv(CSV_BRUTO, decimal=",", encoding="utf-8-sig", low_memory=False)
    for c in ["ETA", "ETD", "ETAUTC", "ETDUTC"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["PERM_H"] = (df["ETD"] - df["ETA"]).dt.total_seconds() / 3600
    return df


def limpar_porto(df: pd.DataFrame) -> pd.DataFrame:
    """Escalas válidas do porto inteiro (todos os tipos de navio)."""
    d = df.drop_duplicates("ESCALANUM")                 # mesma escala listada em 2 terminais
    d = d[d["ESCALAESTAT"] == "Finalitzada"]            # só escalas concluídas
    d = d.dropna(subset=["ETA", "ETD"])
    d = d[d["PERM_H"] > 0]
    return d.sort_values("ETA").reset_index(drop=True)


def recorte_conteineres(df_porto: pd.DataFrame) -> pd.DataFrame:
    d = df_porto[(df_porto["VAIXELLTIPUS"] == "Portacontenidors")
                 & df_porto["TERMINALNOM"].isin(TERMINAIS)].copy()
    d["TERMINAL"] = d["TERMINALNOM"].map(TERMINAIS)
    d["CLASSE"] = pd.cut(d["ESLORA_METRES"], [c[0] for c in CLASSES_ESLORA] + [1e9],
                         right=False, labels=[c[2] for c in CLASSES_ESLORA])
    d["N_REBOC"] = pd.cut(d["ESLORA_METRES"], [c[0] for c in CLASSES_ESLORA] + [1e9],
                          right=False, labels=[c[3] for c in CLASSES_ESLORA]).astype(int)
    return d.sort_values("ETA").reset_index(drop=True)


def tec_horas(eta: pd.Series) -> pd.Series:
    """Tempo entre chegadas consecutivas (h)."""
    return eta.sort_values().diff().dt.total_seconds().div(3600).dropna().reset_index(drop=True)


def limites_iqr(x, k=1.5):
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr


def salvar_fig(fig, caminho):
    fig.tight_layout()
    fig.savefig(caminho)
    plt.close(fig)
