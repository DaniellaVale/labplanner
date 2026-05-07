import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

CSV_FILE = "results_k6.csv"
OUTPUT_DIR = Path("k6_graphs")
OUTPUT_DIR.mkdir(exist_ok=True)

# =========================
# Configuração global
# =========================
plt.rcParams["font.family"] = "Arial"
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "white"
plt.rcParams["savefig.facecolor"] = "white"
plt.rcParams["savefig.edgecolor"] = "white"

AXIS_LINEWIDTH = 1.5
LINEWIDTH = 1.8
LABEL_SIZE = 12
TICK_SIZE = 11
TITLE_SIZE = 11

df = pd.read_csv(CSV_FILE)

# Converter timestamp corretamente (k6 usa ns)
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ns")

# Criar tempo relativo (segundos desde início)
df["time_s"] = (df["timestamp"] - df["timestamp"].min()).dt.total_seconds()


def style_axes(ax):
    """Aplica o estilo solicitado ao gráfico."""
    # Sem linhas de grade
    ax.grid(False)

    # Remove bordas superior e direita
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Eixos em preto com espessura 1.5
    ax.spines["left"].set_color("black")
    ax.spines["bottom"].set_color("black")
    ax.spines["left"].set_linewidth(AXIS_LINEWIDTH)
    ax.spines["bottom"].set_linewidth(AXIS_LINEWIDTH)

    # Ticks em preto
    ax.tick_params(
        axis="both",
        colors="black",
        width=AXIS_LINEWIDTH,
        length=5,
        labelsize=TICK_SIZE
    )

    # Sem moldura extra
    ax.patch.set_edgecolor("none")


def add_bottom_title(fig, text):
    """Adiciona o título abaixo da figura."""
    fig.text(
        0.5, 0.02, text,
        ha="center", va="bottom",
        fontsize=TITLE_SIZE,
        fontname="Arial",
        color="black"
    )


# ========================
# LATÊNCIA
# ========================
lat = df[df["metric_name"] == "http_req_duration"].copy()
lat_group = lat.groupby(pd.cut(lat["time_s"], bins=50), observed=False)["metric_value"].mean()

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(
    range(len(lat_group)),
    lat_group.values,
    color="black",
    linewidth=LINEWIDTH
)

ax.set_xlabel("Tempo (intervalos)", fontsize=LABEL_SIZE, fontname="Arial", color="black")
ax.set_ylabel("Latência média (ms)", fontsize=LABEL_SIZE, fontname="Arial", color="black")

style_axes(ax)
add_bottom_title(fig, "Latência média sob teste de carga")

plt.tight_layout(rect=(0, 0.07, 1, 1))
plt.savefig(OUTPUT_DIR / "latencia_corrigida.png", dpi=300, bbox_inches="tight")
plt.close()

# ========================
# THROUGHPUT
# ========================
req = df[df["metric_name"] == "http_reqs"].copy()
req_group = req.groupby(pd.cut(req["time_s"], bins=50), observed=False).size()

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(
    range(len(req_group)),
    req_group.values,
    color="black",
    linewidth=LINEWIDTH
)

ax.set_xlabel("Tempo (intervalos)", fontsize=LABEL_SIZE, fontname="Arial", color="black")
ax.set_ylabel("Requisições por intervalo", fontsize=LABEL_SIZE, fontname="Arial", color="black")

style_axes(ax)
add_bottom_title(fig, "Throughput sob teste de carga")

plt.tight_layout(rect=(0, 0.07, 1, 1))
plt.savefig(OUTPUT_DIR / "throughput_corrigido.png", dpi=300, bbox_inches="tight")
plt.close()

print("Gráficos corrigidos gerados com sucesso!")