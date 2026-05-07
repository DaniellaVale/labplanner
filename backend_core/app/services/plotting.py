import matplotlib
matplotlib.use("Agg")

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # necessário para 3D


def generate_pareto(terms, output_file):
    names = []
    effects = []

    for term in terms:
        term_name = term.get("term", "")
        if term_name.lower() == "intercepto":
            continue

        names.append(term_name)
        effects.append(abs(float(term.get("value", 0))))

    if not names:
        raise ValueError("Não há termos suficientes para gerar o gráfico de Pareto.")

    plt.figure(figsize=(8, 5))
    plt.bar(names, effects)
    plt.title("Gráfico de Pareto dos Efeitos")
    plt.ylabel("Magnitude do efeito")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()


def generate_surface_plot(exp_data, analysis_result, output_file):
    doe_result = exp_data.get("doe_result", {})
    doe_request = exp_data.get("doe_request", {})

    matrix = doe_result.get("matrix", [])
    levels = doe_request.get("levels", [])

    if not matrix:
        raise ValueError("Matriz do experimento não encontrada.")

    k = len(matrix[0])
    if k != 2:
        raise ValueError("O gráfico de superfície está disponível apenas para experimentos com 2 fatores.")

    if len(levels) < 2:
        raise ValueError("Níveis reais dos fatores não encontrados.")

    terms = {t["term"]: t["value"] for t in analysis_result.get("terms", [])}

    b0 = float(terms.get("Intercepto", 0.0))
    b1 = float(terms.get("X1", 0.0))
    b2 = float(terms.get("X2", 0.0))
    b12 = float(terms.get("X1:X2", 0.0))

    x1_min = float(levels[0]["minimum"])
    x1_max = float(levels[0]["maximum"])
    x2_min = float(levels[1]["minimum"])
    x2_max = float(levels[1]["maximum"])

    x1_name = levels[0].get("name", "X1")
    x2_name = levels[1].get("name", "X2")

    x1_real = np.linspace(x1_min, x1_max, 100)
    x2_real = np.linspace(x2_min, x2_max, 100)
    X1_real, X2_real = np.meshgrid(x1_real, x2_real)

    def real_to_coded(val, vmin, vmax):
        return 2.0 * (val - vmin) / (vmax - vmin) - 1.0

    X1_coded = real_to_coded(X1_real, x1_min, x1_max)
    X2_coded = real_to_coded(X2_real, x2_min, x2_max)

    Z = b0 + b1 * X1_coded + b2 * X2_coded + b12 * X1_coded * X2_coded

    fig = plt.figure(figsize=(14, 6))

    # -------- painel 1: superfície 3D --------
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")

    surf = ax1.plot_surface(
        X1_real,
        X2_real,
        Z,
        cmap="viridis",
        edgecolor="none",
        antialiased=True,
        alpha=0.95,
    )

    responses = exp_data.get("responses") or []
    if responses and len(responses) == len(matrix):
        x_points = []
        y_points = []
        z_points = []

        for row, y in zip(matrix, responses):
            x1_c = float(row[0])
            x2_c = float(row[1])

            x1_r = (x1_c + 1.0) / 2.0 * (x1_max - x1_min) + x1_min
            x2_r = (x2_c + 1.0) / 2.0 * (x2_max - x2_min) + x2_min

            x_points.append(x1_r)
            y_points.append(x2_r)
            z_points.append(float(y))

        ax1.scatter(
            x_points,
            y_points,
            z_points,
            color="red",
            s=45,
            label="Pontos experimentais",
        )
        ax1.legend()

    ax1.set_title("Superfície de Resposta")
    ax1.set_xlabel(x1_name)
    ax1.set_ylabel(x2_name)
    ax1.set_zlabel("Resposta")

    # -------- painel 2: contorno --------
    ax2 = fig.add_subplot(1, 2, 2)

    contour_fill = ax2.contourf(
        X1_real,
        X2_real,
        Z,
        levels=20,
        cmap="viridis",
    )

    contour_lines = ax2.contour(
        X1_real,
        X2_real,
        Z,
        levels=10,
        colors="black",
        linewidths=0.7,
        alpha=0.7,
    )

    ax2.clabel(contour_lines, inline=True, fontsize=8)

    if responses and len(responses) == len(matrix):
        x_points_2d = []
        y_points_2d = []

        for row in matrix:
            x1_c = float(row[0])
            x2_c = float(row[1])

            x1_r = (x1_c + 1.0) / 2.0 * (x1_max - x1_min) + x1_min
            x2_r = (x2_c + 1.0) / 2.0 * (x2_max - x2_min) + x2_min

            x_points_2d.append(x1_r)
            y_points_2d.append(x2_r)

        ax2.scatter(
            x_points_2d,
            y_points_2d,
            color="red",
            s=35,
            label="Pontos experimentais",
        )
        ax2.legend()

    ax2.set_title("Mapa de Contorno")
    ax2.set_xlabel(x1_name)
    ax2.set_ylabel(x2_name)

    cbar = fig.colorbar(contour_fill, ax=[ax1, ax2], shrink=0.85, aspect=25, pad=0.08)
    cbar.set_label("Resposta")

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()