"""Funções compartilhadas: leitura do CSV bruto, regra de atípicos e salvamento de figuras."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]          # pasta gbfinal/
CSV_BRUTO = RAIZ / "b8966d7a-d570-4256-bd1b-b5757ad3a0d6.csv"
RES = RAIZ / "analise" / "resultados"

# Tradução dos valores categóricos do CSV (catalão -> português)
TRAD_TIPO = {
    "Transbordadors": "Ferry",
    "Portacontenidors": "Porta-contêineres",
    "Tancs": "Navio-tanque",
    "Passatge": "Passageiros (cruzeiro)",
    "Ro-Ro": "Ro-Ro",
    "Car-carrier": "Transporte de veículos",
    "Càrrega (Lo-Lo)": "Carga geral (Lo-Lo)",
    "Petroliers": "Petroleiro",
    "Granelers": "Graneleiro",
}
TRAD_ESTADO = {
    "Sol·licitada": "Solicitada",
    "Autoritzada": "Autorizada",
    "Confirmada": "Confirmada",
    "Fondeig Previ": "Fundeio prévio",
    "Iniciada": "Iniciada",
    "Finalitzada": "Finalizada",
}

plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 150, "font.size": 10,
                     "axes.grid": True, "grid.alpha": .3,
                     "axes.spines.top": False, "axes.spines.right": False})


def pasta(nome: str = "") -> Path:
    p = RES / nome
    p.mkdir(parents=True, exist_ok=True)
    return p


def carregar_bruto() -> pd.DataFrame:
    df = pd.read_csv(CSV_BRUTO, decimal=",", encoding="utf-8-sig", low_memory=False)
    for c in ["ETA", "ETD"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["PERM_H"] = (df["ETD"] - df["ETA"]).dt.total_seconds() / 3600
    return df


def limites_iqr(x, k=1.5):
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr


def salvar_fig(fig, caminho):
    fig.tight_layout()
    fig.savefig(caminho)
    plt.close(fig)
