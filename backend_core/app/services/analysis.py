import numpy as np
from scipy import stats
from sklearn.metrics import mean_squared_error, mean_absolute_error


def build_design_matrix(matrix):
    """
    Constrói matriz de regressão com:
    - intercepto
    - termos lineares
    - interações de 2 fatores
    """
    X = np.array(matrix, dtype=float)
    n, k = X.shape

    columns = []
    names = []

    columns.append(np.ones(n))
    names.append("Intercepto")

    for i in range(k):
        columns.append(X[:, i])
        names.append(f"X{i+1}")

    for i in range(k):
        for j in range(i + 1, k):
            columns.append(X[:, i] * X[:, j])
            names.append(f"X{i+1}:X{j+1}")

    X_model = np.column_stack(columns)
    return X_model, names


def build_model_equation(terms):
    if not terms:
        return "Y ="

    pieces = ["Y ="]

    for i, term in enumerate(terms):
        coef = term["value"]
        name = term["term"]

        if name == "Intercepto":
            pieces.append(f"{coef:.4f}")
            continue

        signal = "+" if coef >= 0 else "-"
        label = name.replace(":", "*")
        value = abs(coef)
        pieces.append(f" {signal} {value:.4f}{label}")

    return "".join(pieces)


def _group_replicates(matrix, responses):
    """
    Agrupa execuções com os mesmos níveis codificados.
    Retorna lista de grupos: [(x_tuple, [y1, y2, ...]), ...]
    """
    groups = {}
    for row, y in zip(matrix, responses):
        key = tuple(float(v) for v in row)
        groups.setdefault(key, []).append(float(y))
    return list(groups.items())


def _pure_error_and_lack_of_fit(matrix, responses, y_pred, df_error):
    """
    Calcula:
    - erro puro (pure error)
    - falta de ajuste (lack of fit)

    pure error = variação entre replicatas no mesmo ponto experimental
    lack of fit = SSE residual - pure error
    """
    groups = _group_replicates(matrix, responses)

    ss_pure_error = 0.0
    df_pure_error = 0

    for _, ys in groups:
        if len(ys) >= 2:
            y_mean = np.mean(ys)
            ss_pure_error += float(np.sum((np.array(ys) - y_mean) ** 2))
            df_pure_error += len(ys) - 1

    residuals = np.array(responses, dtype=float) - np.array(y_pred, dtype=float)
    sse = float(np.sum(residuals ** 2))

    ss_lack_of_fit = sse - ss_pure_error
    if ss_lack_of_fit < 0 and abs(ss_lack_of_fit) < 1e-10:
        ss_lack_of_fit = 0.0

    df_lack_of_fit = df_error - df_pure_error

    if df_lack_of_fit < 0:
        df_lack_of_fit = 0

    return {
        "ss_pure_error": float(ss_pure_error),
        "df_pure_error": int(df_pure_error),
        "ss_lack_of_fit": float(ss_lack_of_fit),
        "df_lack_of_fit": int(df_lack_of_fit),
    }


def regression_analysis(matrix, responses):
    """
    Executa regressão linear e ANOVA com separação de:
    - regressão
    - resíduo
    - erro puro
    - falta de ajuste

    Mantém compatibilidade com o frontend atual.
    """
    y = np.array(responses, dtype=float)

    X_model, names = build_design_matrix(matrix)
    n, p = X_model.shape

    beta, _, _, _ = np.linalg.lstsq(X_model, y, rcond=None)

    y_pred = X_model @ beta
    residuals = y - y_pred

    sse = float(np.sum(residuals ** 2))
    sst = float(np.sum((y - np.mean(y)) ** 2))
    ssr = float(sst - sse)

    if abs(ssr) < 1e-12:
        ssr = 0.0
    if abs(sse) < 1e-12:
        sse = 0.0

    r2 = float(1 - (sse / sst)) if sst > 0 else None

    df_total = n - 1
    df_model = p - 1
    df_error = n - p

    rmse = float(np.sqrt(mean_squared_error(y, y_pred)))
    mae = float(mean_absolute_error(y, y_pred))

    r2_adj = None
    terms = []

    # defaults
    anova_table = [
        {
            "source": "Regressão",
            "ss": ssr,
            "df": int(df_model),
            "ms": None,
            "f": None,
            "p_value": None,
        },
        {
            "source": "Resíduo",
            "ss": sse,
            "df": int(df_error),
            "ms": None,
            "f": None,
            "p_value": None,
        },
        {
            "source": "Total",
            "ss": sst,
            "df": int(df_total),
            "ms": None,
            "f": None,
            "p_value": None,
        },
    ]

    # ---------------- ANOVA global ----------------
    mse_residual = None
    F_model = None
    p_value_model = None

    if df_error > 0:
        r2_adj = float(1 - (1 - r2) * (n - 1) / df_error) if r2 is not None else None

        msr = ssr / df_model if df_model > 0 else None
        mse_residual = sse / df_error if df_error > 0 else None

        if msr is not None and mse_residual is not None and mse_residual > 0:
            F_model = msr / mse_residual
            p_value_model = float(1 - stats.f.cdf(F_model, df_model, df_error))

        anova_table = [
            {
                "source": "Regressão",
                "ss": ssr,
                "df": int(df_model),
                "ms": float(msr) if msr is not None else None,
                "f": float(F_model) if F_model is not None else None,
                "p_value": p_value_model,
            },
            {
                "source": "Resíduo",
                "ss": sse,
                "df": int(df_error),
                "ms": float(mse_residual) if mse_residual is not None else None,
                "f": None,
                "p_value": None,
            },
            {
                "source": "Total",
                "ss": sst,
                "df": int(df_total),
                "ms": None,
                "f": None,
                "p_value": None,
            },
        ]

    # ---------------- erro puro / falta de ajuste ----------------
    pe_info = _pure_error_and_lack_of_fit(matrix, responses, y_pred, df_error)
    ss_pe = pe_info["ss_pure_error"]
    df_pe = pe_info["df_pure_error"]
    ss_lof = pe_info["ss_lack_of_fit"]
    df_lof = pe_info["df_lack_of_fit"]

    ms_pe = None
    ms_lof = None
    f_lof = None
    p_lof = None

    if df_pe > 0:
        ms_pe = ss_pe / df_pe

    if df_lof > 0:
        ms_lof = ss_lof / df_lof

    if ms_lof is not None and ms_pe is not None and ms_pe > 0:
        f_lof = ms_lof / ms_pe
        p_lof = float(1 - stats.f.cdf(f_lof, df_lof, df_pe))

    # Se houver replicatas, acrescenta linhas clássicas de DOE
    if df_pe > 0 or df_lof > 0:
        anova_table = [
            {
                "source": "Regressão",
                "ss": ssr,
                "df": int(df_model),
                "ms": float(ssr / df_model) if df_model > 0 else None,
                "f": float(F_model) if F_model is not None else None,
                "p_value": p_value_model,
            },
            {
                "source": "Falta de ajuste",
                "ss": float(ss_lof),
                "df": int(df_lof),
                "ms": float(ms_lof) if ms_lof is not None else None,
                "f": float(f_lof) if f_lof is not None else None,
                "p_value": p_lof,
            },
            {
                "source": "Erro puro",
                "ss": float(ss_pe),
                "df": int(df_pe),
                "ms": float(ms_pe) if ms_pe is not None else None,
                "f": None,
                "p_value": None,
            },
            {
                "source": "Resíduo",
                "ss": sse,
                "df": int(df_error),
                "ms": float(mse_residual) if mse_residual is not None else None,
                "f": None,
                "p_value": None,
            },
            {
                "source": "Total",
                "ss": sst,
                "df": int(df_total),
                "ms": None,
                "f": None,
                "p_value": None,
            },
        ]

    # ---------------- erros padrão / t / p dos coeficientes ----------------
    # Preferência:
    # 1. usar MSE residual se > 0
    # 2. senão usar MS pure error se > 0
    # 3. senão não calcular inferência
    mse_for_inference = None
    df_for_inference = None

    if mse_residual is not None and mse_residual > 0 and df_error > 0:
        mse_for_inference = mse_residual
        df_for_inference = df_error
    elif ms_pe is not None and ms_pe > 0 and df_pe > 0:
        mse_for_inference = ms_pe
        df_for_inference = df_pe

    if mse_for_inference is not None and df_for_inference is not None:
        xtx_inv = np.linalg.pinv(X_model.T @ X_model)
        cov_matrix = mse_for_inference * xtx_inv
        std_errors = np.sqrt(np.diag(cov_matrix))

        for i, name in enumerate(names):
            se = float(std_errors[i]) if std_errors[i] is not None else None

            if se is not None and se > 0:
                t_value = float(beta[i] / se)
                p_value = float(2 * (1 - stats.t.cdf(abs(t_value), df_for_inference)))
            else:
                t_value = None
                p_value = None

            terms.append(
                {
                    "term": name,
                    "value": float(beta[i]),
                    "std_error": se,
                    "t_value": t_value,
                    "p_value": p_value,
                }
            )
    else:
        for i, name in enumerate(names):
            terms.append(
                {
                    "term": name,
                    "value": float(beta[i]),
                    "std_error": None,
                    "t_value": None,
                    "p_value": None,
                }
            )

    equation = build_model_equation(terms)

    message = None
    if df_error <= 0:
        message = (
            "Modelo saturado: coeficientes calculados, mas ANOVA inferencial, erro padrão, "
            "t e p-valor não podem ser estimados sem graus de liberdade residuais."
        )
    elif df_pe > 0 and ss_pe == 0:
        message = (
            "Há replicatas, mas o erro puro foi zero. Nesse caso, testes F baseados em erro puro "
            "podem resultar em valores indefinidos ou infinitos."
        )

    return {
        "r_squared": r2,
        "r_squared_adj": r2_adj,
        "rmse": rmse,
        "mae": mae,
        "equation": equation,
        "terms": terms,
        "anova": anova_table,
        "diagnostics": {
            "observed": [float(v) for v in y.tolist()],
            "predicted": [float(v) for v in y_pred.tolist()],
            "residuals": [float(v) for v in residuals.tolist()],
        },
        "is_saturated_model": df_error <= 0,
        "message": message,
    }