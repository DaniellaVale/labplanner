from __future__ import annotations

import math
import os
import time

import flet as ft
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000").rstrip("/")
PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000").rstrip("/")


def main(page: ft.Page):
    page.title = "LabPlanner"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20
    page.window_width = 1200
    page.window_height = 900
    page.theme_mode = ft.ThemeMode.DARK

    title = ft.Text(
        "LabPlanner - Planejamento Experimental",
        size=28,
        weight=ft.FontWeight.BOLD,
    )

    state = {
        "selected_experiment": None,
        "response_fields": [],
    }

    # ---------------- API ----------------

    def api_create_experiment(payload: dict):
        response = requests.post(
            f"{BACKEND_URL}/experiments/",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()

        try:
            data = response.json()
        except Exception:
            return None

        if isinstance(data, dict):
            return data

        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                return data[0]
            return None

        return None

    def api_list_experiments():
        response = requests.get(f"{BACKEND_URL}/experiments/", timeout=60)
        response.raise_for_status()
        return response.json()

    def api_get_experiment(exp_id: str):
        response = requests.get(f"{BACKEND_URL}/experiments/{exp_id}", timeout=60)
        response.raise_for_status()
        return response.json()

    def api_update_responses(exp_id: str, responses: list[float]):
        response = requests.put(
            f"{BACKEND_URL}/experiments/{exp_id}/responses",
            json={"responses": responses},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def api_get_analysis(exp_id: str):
        response = requests.get(
            f"{BACKEND_URL}/experiments/{exp_id}/analysis",
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    # ---------------- criação ----------------

    exp_name_field = ft.TextField(label="Nome do experimento", width=400, value="")

    design_type_dropdown = ft.Dropdown(
        label="Tipo de planejamento",
        width=260,
        value="Fatorial 2k",
        options=[
            ft.dropdown.Option("Fatorial 2k"),
            ft.dropdown.Option("Fatorial 3k"),
            ft.dropdown.Option("Fatorial fracionado"),
            ft.dropdown.Option("Composto Central"),
            ft.dropdown.Option("Box-Behnken"),
        ],
    )

    num_factors_field = ft.TextField(
        label="Número de fatores (k)",
        width=180,
        value="2",
    )

    replicates_field = ft.TextField(
        label="Replicatas por ensaio",
        width=200,
        value="1",
    )

    fractionality_field = ft.TextField(
        label="Nível de fracionamento (p)",
        width=220,
        value="1",
        visible=False,
    )

    center_points_field = ft.TextField(
        label="Replicatas do ponto central",
        width=220,
        value="0",
        visible=True,
    )

    design_info_text = ft.Text("", size=14)
    create_status = ft.Text("", selectable=True)
    result_text = ft.Text("", selectable=True)

    factors_container = ft.Column(spacing=10)

    def map_design_type(ui_value: str) -> str:
        mapping = {
            "Fatorial 2k": "fatorial_2k",
            "Fatorial 3k": "fatorial_3k",
            "Fatorial fracionado": "fatorial_fracionado",
            "Composto Central": "composto_central",
            "Box-Behnken": "box_behnken",
        }
        return mapping[ui_value]

    def update_design_info():
        try:
            design_ui = design_type_dropdown.value
            k = int(num_factors_field.value)
            reps = int(replicates_field.value or "1")
            centers = int(center_points_field.value or "0")

            if reps < 1:
                design_info_text.value = "Replicatas por ensaio devem ser >= 1."
                return

            if centers < 0:
                design_info_text.value = "Replicatas do ponto central devem ser >= 0."
                return

            if design_ui == "Fatorial 2k":
                base = 2 ** k
                total = base * reps + centers
                design_info_text.value = (
                    f"Planejamento selecionado: 2^{k} | ensaios base = {base} | total com replicatas = {total}"
                )

            elif design_ui == "Fatorial 3k":
                base = 3 ** k
                total = base * reps + centers
                design_info_text.value = (
                    f"Planejamento selecionado: 3^{k} | ensaios base = {base} | total com replicatas = {total}"
                )

            elif design_ui == "Fatorial fracionado":
                p = int(fractionality_field.value)
                if p >= k:
                    design_info_text.value = "Planejamento fracionado inválido: p deve ser menor que k."
                else:
                    base = 2 ** (k - p)
                    total = base * reps + centers
                    design_info_text.value = (
                        f"Planejamento selecionado: 2^({k}-{p}) | ensaios base = {base} | total com replicatas = {total}"
                    )

            elif design_ui == "Composto Central":
                base = (2 ** k) + (2 * k)
                total = base * reps + centers
                design_info_text.value = (
                    f"Planejamento selecionado: CCD com {k} fatores | ensaios base = {base} | total com replicatas = {total}"
                )

            elif design_ui == "Box-Behnken":
                if k < 3:
                    design_info_text.value = "Box-Behnken requer pelo menos 3 fatores."
                else:
                    base = 4 * math.comb(k, 2)
                    total = base * reps + centers
                    design_info_text.value = (
                        f"Planejamento selecionado: Box-Behnken com {k} fatores | ensaios base = {base} | total com replicatas = {total}"
                    )

            else:
                design_info_text.value = ""

        except Exception:
            design_info_text.value = ""

    def build_factor_fields():
        factors_container.controls.clear()
        try:
            k = int(num_factors_field.value)
            if k < 2:
                raise ValueError
        except Exception:
            factors_container.controls.append(
                ft.Text(
                    "Informe um número de fatores válido (inteiro >= 2).",
                    color=ft.Colors.RED,
                )
            )
            page.update()
            return

        rows = []
        for i in range(k):
            row = ft.Row(
                controls=[
                    ft.TextField(label=f"Nome do fator {i + 1}", width=250, value=f"X{i + 1}"),
                    ft.TextField(label="Mínimo", width=150, value="0"),
                    ft.TextField(label="Máximo", width=150, value="10"),
                ]
            )
            rows.append(row)

        factors_container.controls.extend(rows)
        update_design_info()
        page.update()

    def on_design_change(e):
        selected = design_type_dropdown.value
        fractionality_field.visible = selected == "Fatorial fracionado"

        if selected in ("Composto Central", "Box-Behnken"):
            if (center_points_field.value or "").strip() in ("", "0"):
                center_points_field.value = "3"

        update_design_info()
        page.update()

    def on_k_change(e):
        build_factor_fields()

    def on_p_change(e):
        update_design_info()
        page.update()

    def build_levels_payload():
        levels = []
        for row in factors_container.controls:
            if not isinstance(row, ft.Row):
                continue

            name_field = row.controls[0]
            min_field = row.controls[1]
            max_field = row.controls[2]

            name = name_field.value.strip()
            minimum = float(min_field.value)
            maximum = float(max_field.value)

            if not name:
                raise ValueError("Todos os fatores precisam ter nome.")
            if minimum >= maximum:
                raise ValueError(f"No fator '{name}', o mínimo deve ser menor que o máximo.")

            levels.append(
                {
                    "name": name,
                    "minimum": minimum,
                    "maximum": maximum,
                }
            )
        return levels

    # ---------------- seleção / visualização ----------------

    experiments_dropdown = ft.Dropdown(
        label="Experimentos salvos",
        width=500,
        options=[],
        value=None,
    )

    refresh_button = ft.OutlinedButton(
        "Recarregar experimentos",
        icon=ft.Icons.REFRESH,
    )

    details_text = ft.Text("Nenhum experimento selecionado.", selectable=True)

    design_table = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Execução"))],
        rows=[],
    )

    responses_title = ft.Text(
        "Respostas experimentais (Y)",
        size=18,
        weight=ft.FontWeight.BOLD,
    )

    responses_hint = ft.Text(
        "Selecione um experimento para preencher as respostas.",
        selectable=True,
    )

    responses_container = ft.Column(spacing=10)
    responses_status = ft.Text("", selectable=True)

    save_responses_button = ft.ElevatedButton("Salvar respostas")
    save_responses_button.disabled = True

    analysis_title = ft.Text(
        "Análise de regressão",
        size=18,
        weight=ft.FontWeight.BOLD,
    )

    analysis_status = ft.Text("Nenhuma análise calculada ainda.", selectable=True)
    r2_text = ft.Text("R²: -", selectable=True)

    coeff_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Termo")),
            ft.DataColumn(ft.Text("Coeficiente")),
        ],
        rows=[],
    )

    anova_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Fonte")),
            ft.DataColumn(ft.Text("SQ")),
            ft.DataColumn(ft.Text("gl")),
            ft.DataColumn(ft.Text("QM")),
            ft.DataColumn(ft.Text("F")),
            ft.DataColumn(ft.Text("p-valor")),
        ],
        rows=[],
    )

    # ---------------- Pareto ----------------

    pareto_title = ft.Text(
        "Gráfico de Pareto",
        size=18,
        weight=ft.FontWeight.BOLD,
    )

    pareto_status = ft.Text("Nenhum gráfico de Pareto disponível.", selectable=True)

    pareto_open_button = ft.OutlinedButton(
        "Abrir gráfico em nova aba",
        icon=ft.Icons.OPEN_IN_NEW,
        disabled=True,
    )

    pareto_url_label = ft.Text(
        "",
        selectable=True,
        visible=False,
    )

    def clear_pareto(message: str = "Nenhum gráfico de Pareto disponível."):
        pareto_status.value = message
        pareto_url_label.value = ""
        pareto_url_label.visible = False
        pareto_open_button.disabled = True
        page.update()

    def enable_pareto_link(exp_id: str):
        pareto_status.value = "Use o botão abaixo para abrir o gráfico em nova aba. Se não abrir, copie a URL."
        pareto_url_label.value = (
            f"{PUBLIC_BACKEND_URL}/experiments/{exp_id}/pareto.png?t={int(time.time())}"
        )
        pareto_url_label.visible = True
        pareto_open_button.disabled = False
        page.update()

    async def open_pareto_in_new_tab(e):
        url = (pareto_url_label.value or "").strip()
        if not url:
            pareto_status.value = "URL do gráfico não disponível."
            page.update()
            return

        try:
            await page.launch_url(url)
        except Exception:
            pareto_status.value = "Não foi possível abrir automaticamente. Copie a URL abaixo."
            page.update()

    pareto_open_button.on_click = open_pareto_in_new_tab

    # ---------------- Superfície ----------------

    surface_title = ft.Text(
        "Gráfico de Superfície",
        size=18,
        weight=ft.FontWeight.BOLD,
    )

    surface_status = ft.Text("Nenhum gráfico de superfície disponível.", selectable=True)

    surface_open_button = ft.OutlinedButton(
        "Abrir superfície em nova aba",
        icon=ft.Icons.OPEN_IN_NEW,
        disabled=True,
    )

    surface_url_label = ft.Text(
        "",
        selectable=True,
        visible=False,
    )

    def clear_surface(message: str = "Nenhum gráfico de superfície disponível."):
        surface_status.value = message
        surface_url_label.value = ""
        surface_url_label.visible = False
        surface_open_button.disabled = True
        page.update()

    def enable_surface_link(exp_id: str, exp_data: dict):
        doe_result = exp_data.get("doe_result", {})
        matrix = doe_result.get("matrix", [])

        if not matrix or len(matrix[0]) != 2:
            clear_surface("O gráfico de superfície está disponível apenas para experimentos com 2 fatores.")
            return

        surface_status.value = "Use o botão abaixo para abrir a superfície em nova aba. Se não abrir, copie a URL."
        surface_url_label.value = (
            f"{PUBLIC_BACKEND_URL}/experiments/{exp_id}/surface.png?t={int(time.time())}"
        )
        surface_url_label.visible = True
        surface_open_button.disabled = False
        page.update()

    async def open_surface_in_new_tab(e):
        url = (surface_url_label.value or "").strip()
        if not url:
            surface_status.value = "URL da superfície não disponível."
            page.update()
            return

        try:
            await page.launch_url(url)
        except Exception:
            surface_status.value = "Não foi possível abrir automaticamente. Copie a URL abaixo."
            page.update()

    surface_open_button.on_click = open_surface_in_new_tab

    # ---------------- auxiliares de limpeza/reset ----------------

    def clear_selected_experiment_views():
        state["selected_experiment"] = None
        details_text.value = "Nenhum experimento selecionado."
        design_table.columns = [ft.DataColumn(ft.Text("Execução"))]
        design_table.rows = []
        clear_response_inputs("Selecione um experimento para preencher as respostas.")
        clear_analysis()
        clear_pareto()
        clear_surface()

    def reset_form():
        exp_name_field.value = ""
        design_type_dropdown.value = "Fatorial 2k"
        num_factors_field.value = "2"
        replicates_field.value = "1"
        fractionality_field.value = "1"
        fractionality_field.visible = False
        center_points_field.value = "0"
        create_status.value = ""
        result_text.value = ""
        build_factor_fields()
        clear_selected_experiment_views()
        page.update()

    def start_new_experiment(e=None):
        experiments_dropdown.value = None
        reset_form()

    # ---------------- tabela ----------------

    def coded_to_real(coded_value: float, level: dict) -> float:
        min_v = float(level["minimum"])
        max_v = float(level["maximum"])
        return (coded_value + 1.0) / 2.0 * (max_v - min_v) + min_v

    def build_result_table(exp_data: dict):
        design_table.columns = [ft.DataColumn(ft.Text("Execução"))]
        design_table.rows = []

        if not isinstance(exp_data, dict):
            raise ValueError(f"Formato inválido de experimento: {type(exp_data)}")

        doe_result = exp_data.get("doe_result") or {}
        doe_request = exp_data.get("doe_request") or {}

        if not isinstance(doe_result, dict):
            raise ValueError(f"'doe_result' inválido: {type(doe_result)}")
        if not isinstance(doe_request, dict):
            raise ValueError(f"'doe_request' inválido: {type(doe_request)}")

        matrix_real = doe_result.get("matrix_real")
        matrix = doe_result.get("matrix", [])
        levels = doe_request.get("levels", [])

        if not isinstance(levels, list):
            levels = []

        data_matrix = matrix_real if matrix_real else matrix

        if not data_matrix:
            page.update()
            return

        factor_names = []
        for i, level in enumerate(levels):
            if isinstance(level, dict):
                factor_names.append(level.get("name", f"X{i + 1}"))
            else:
                factor_names.append(f"X{i + 1}")

        if not factor_names and data_matrix:
            factor_names = [f"X{i + 1}" for i in range(len(data_matrix[0]))]

        design_table.columns = [ft.DataColumn(ft.Text("Execução"))] + [
            ft.DataColumn(ft.Text(name)) for name in factor_names
        ]

        rows = []
        for i, row_values in enumerate(data_matrix):
            cells = [ft.DataCell(ft.Text(str(i + 1)))]
            for j, value in enumerate(row_values):
                if matrix_real:
                    cells.append(ft.DataCell(ft.Text(f"{float(value):.4f}")))
                else:
                    try:
                        if j < len(levels) and isinstance(levels[j], dict):
                            real_value = coded_to_real(float(value), levels[j])
                            cells.append(ft.DataCell(ft.Text(f"{real_value:.4f}")))
                        else:
                            cells.append(ft.DataCell(ft.Text(str(value))))
                    except Exception:
                        cells.append(ft.DataCell(ft.Text(str(value))))

            rows.append(ft.DataRow(cells=cells))

        design_table.rows = rows
        page.update()

    # ---------------- respostas ----------------

    def clear_response_inputs(message: str = "Selecione um experimento para preencher as respostas."):
        state["response_fields"] = []
        responses_hint.value = message
        responses_status.value = ""
        responses_container.controls.clear()
        save_responses_button.disabled = True
        page.update()

    def build_response_inputs(exp_data: dict):
        doe_result = exp_data.get("doe_result", {})
        matrix = doe_result.get("matrix", [])
        existing_responses = exp_data.get("responses") or []

        responses_container.controls.clear()
        response_fields = []

        if not matrix:
            state["response_fields"] = []
            responses_hint.value = "Este experimento não possui execuções."
            save_responses_button.disabled = True
            page.update()
            return

        responses_hint.value = f"Preencha as respostas para {len(matrix)} execuções."

        rows = []
        current_row = []

        for i in range(len(matrix)):
            initial_value = ""
            if i < len(existing_responses) and existing_responses[i] is not None:
                initial_value = str(existing_responses[i])

            tf = ft.TextField(
                label=f"Y{i + 1}",
                width=120,
                value=initial_value,
            )

            response_fields.append(tf)
            current_row.append(tf)

            if len(current_row) == 4:
                rows.append(ft.Row(controls=current_row, wrap=False))
                current_row = []

        if current_row:
            rows.append(ft.Row(controls=current_row, wrap=False))

        responses_container.controls.extend(rows)
        state["response_fields"] = response_fields
        save_responses_button.disabled = False
        responses_status.value = ""
        page.update()

    # ---------------- análise ----------------

    def clear_analysis(message: str = "Nenhuma análise calculada ainda."):
        analysis_status.value = message
        analysis_status.color = ft.Colors.GREY_400
        r2_text.value = "R²: -"
        coeff_table.rows = []
        anova_table.rows = []
        page.update()

    def _fmt_num(value, digits=6):
        if value is None:
            return "-"
        try:
            return f"{float(value):.{digits}f}"
        except Exception:
            return str(value)

    def _fmt_int(value):
        if value is None:
            return "-"
        try:
            return str(int(value))
        except Exception:
            return str(value)

    def load_analysis_for_experiment(exp_id: str):
        try:
            exp_data = api_get_experiment(exp_id)
            responses = exp_data.get("responses") or []

            if not responses:
                clear_analysis("Preencha e salve as respostas para calcular a análise.")
                return

            analysis_data = api_get_analysis(exp_id)

            r2_value = analysis_data.get("r_squared")
            if r2_value is None:
                r2_text.value = "R²: -"
            else:
                r2_text.value = f"R²: {r2_value:.4f}"

            terms = analysis_data.get("terms", [])
            coeff_table.rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(term.get("term", "-")))),
                        ft.DataCell(ft.Text(_fmt_num(term.get("value")))),
                    ]
                )
                for term in terms
            ]

            anova = analysis_data.get("anova", [])
            anova_table.rows = [
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row.get("source", "-")))),
                        ft.DataCell(ft.Text(_fmt_num(row.get("ss")))),
                        ft.DataCell(ft.Text(_fmt_int(row.get("df")))),
                        ft.DataCell(ft.Text(_fmt_num(row.get("ms")))),
                        ft.DataCell(ft.Text(_fmt_num(row.get("f")))),
                        ft.DataCell(ft.Text(_fmt_num(row.get("p_value")))),
                    ]
                )
                for row in anova
            ]

            if analysis_data.get("is_saturated_model"):
                analysis_status.value = analysis_data.get(
                    "message",
                    "Modelo saturado: coeficientes calculados, mas ANOVA inferencial indisponível.",
                )
                analysis_status.color = ft.Colors.ORANGE
            else:
                analysis_status.value = analysis_data.get("message") or "Análise calculada com sucesso."
                analysis_status.color = ft.Colors.GREEN

            page.update()

        except Exception as ex:
            clear_analysis(f"Análise indisponível: {str(ex)}")

    # ---------------- ações ----------------

    def on_save_responses(e):
        responses_status.value = ""
        try:
            exp = state["selected_experiment"]
            if not exp:
                raise ValueError("Nenhum experimento selecionado.")

            exp_id = exp["id"]
            values = []

            for tf in state["response_fields"]:
                raw = (tf.value or "").strip()
                if raw == "":
                    raise ValueError("Preencha todas as respostas Y.")
                values.append(float(raw.replace(",", ".")))

            api_update_responses(exp_id, values)

            responses_status.value = "Respostas salvas com sucesso."
            responses_status.color = ft.Colors.GREEN

            load_selected_experiment_by_id(exp_id)
            page.update()

        except Exception as ex:
            responses_status.value = f"Erro ao salvar respostas: {str(ex)}"
            responses_status.color = ft.Colors.RED
            page.update()

    save_responses_button.on_click = on_save_responses

    def load_selected_experiment_by_id(exp_id: str):
        try:
            exp_data = api_get_experiment(exp_id)
            state["selected_experiment"] = exp_data

            doe_result = exp_data.get("doe_result", {})
            details_text.value = (
                f"ID: {exp_data.get('id', '-')}\n"
                f"Nome: {exp_data.get('name', '-')}\n"
                f"Tipo: {doe_result.get('design_type', '-')}\n"
                f"Ensaios: {doe_result.get('rows', '-')}"
            )

            build_result_table(exp_data)
            build_response_inputs(exp_data)
            load_analysis_for_experiment(exp_id)

            responses = exp_data.get("responses") or []
            if responses:
                enable_pareto_link(exp_id)
                enable_surface_link(exp_id, exp_data)
            else:
                clear_pareto("Salve as respostas experimentais para gerar o gráfico de Pareto.")
                clear_surface("Salve as respostas experimentais para gerar o gráfico de superfície.")

            page.update()

        except Exception as ex:
            state["selected_experiment"] = None
            details_text.value = f"Erro ao carregar experimento: {str(ex)}"
            design_table.rows = []
            clear_response_inputs("Não foi possível carregar as respostas deste experimento.")
            clear_analysis("Não foi possível carregar a análise deste experimento.")
            clear_pareto("Não foi possível carregar o gráfico de Pareto.")
            clear_surface("Não foi possível carregar o gráfico de superfície.")
            page.update()

    def load_selected_experiment(e):
        exp_id = experiments_dropdown.value
        if not exp_id:
            clear_selected_experiment_views()
            page.update()
            return
        load_selected_experiment_by_id(exp_id)

    def refresh_experiments(selected_id: str | None = None, auto_select_first: bool = False):
        try:
            exps = api_list_experiments()

            exps = sorted(
                exps,
                key=lambda x: x.get("created_at") or "",
                reverse=True,
            )

            experiments_dropdown.options = [
                ft.dropdown.Option(
                    key=exp["id"],
                    text=f'{exp["name"]} ({exp["design_type"]}, {exp["rows"]} execuções)',
                )
                for exp in exps
            ]

            chosen_id = None

            if selected_id and any(exp["id"] == selected_id for exp in exps):
                chosen_id = selected_id
            elif experiments_dropdown.value and any(exp["id"] == experiments_dropdown.value for exp in exps):
                chosen_id = experiments_dropdown.value
            elif auto_select_first and exps:
                chosen_id = exps[0]["id"]

            if chosen_id:
                experiments_dropdown.value = chosen_id
                load_selected_experiment_by_id(chosen_id)
            else:
                experiments_dropdown.value = None
                clear_selected_experiment_views()

            page.update()

        except Exception as ex:
            details_text.value = f"Erro ao listar experimentos: {str(ex)}"
            clear_response_inputs("Erro ao carregar a lista de experimentos.")
            clear_analysis("Erro ao carregar a análise.")
            clear_pareto("Erro ao carregar o gráfico de Pareto.")
            clear_surface("Erro ao carregar o gráfico de superfície.")
            page.update()

    def create_experiment(e):
        result_text.value = ""
        create_status.value = ""
        page.update()

        try:
            exp_name = exp_name_field.value.strip()
            if not exp_name:
                raise ValueError("Informe o nome do experimento.")

            k = int(num_factors_field.value)
            design_type = map_design_type(design_type_dropdown.value)

            doe_request = {
                "design_type": design_type,
                "factors": k,
                "levels": build_levels_payload(),
                "replicates": int(replicates_field.value or "1"),
                "center_points": int(center_points_field.value or "0"),
            }

            if design_type == "fatorial_fracionado":
                p = int(fractionality_field.value)
                if p >= k:
                    raise ValueError("Para planejamento fracionado, p deve ser menor que k.")
                doe_request["fractionality"] = p

            payload = {
                "name": exp_name,
                "doe_request": doe_request,
            }

            response_data = api_create_experiment(payload)

            create_status.value = "Experimento criado com sucesso."
            create_status.color = ft.Colors.GREEN

            if isinstance(response_data, dict):
                doe_result = response_data.get("doe_result", {})
                design_label = doe_result.get(
                    "design_notation",
                    doe_result.get("design_type", doe_request["design_type"]),
                )

                result_text.value = (
                    f"Experimento criado com sucesso!\n"
                    f"Nome: {response_data.get('name', exp_name)}\n"
                    f"Tipo: {design_label}\n"
                    f"Fatores: {doe_result.get('factors', k)}\n"
                    f"Ensaios: {doe_result.get('rows', '-')}"
                )

                exp_id = response_data.get("id")
                if exp_id:
                    refresh_experiments(exp_id)
                else:
                    refresh_experiments()
            else:
                result_text.value = (
                    "Experimento criado com sucesso.\n"
                    "Atualizando lista de experimentos..."
                )
                refresh_experiments()

        except Exception as ex:
            create_status.value = f"Erro ao criar experimento: {str(ex)}"
            create_status.color = ft.Colors.RED
            result_text.value = f"Erro: {str(ex)}"
            page.update()

    # ---------------- bindings ----------------

    design_type_dropdown.on_change = on_design_change
    num_factors_field.on_change = on_k_change
    replicates_field.on_change = lambda e: update_design_info()
    fractionality_field.on_change = on_p_change
    center_points_field.on_change = lambda e: update_design_info()
    experiments_dropdown.on_change = load_selected_experiment
    refresh_button.on_click = lambda e: refresh_experiments()

    create_button = ft.ElevatedButton(
        "Criar experimento",
        icon=ft.Icons.SCIENCE,
        on_click=create_experiment,
    )

    rebuild_button = ft.OutlinedButton(
        "Atualizar fatores",
        icon=ft.Icons.REFRESH,
        on_click=lambda e: build_factor_fields(),
    )

    new_experiment_button = ft.OutlinedButton(
        "Novo experimento",
        icon=ft.Icons.ADD,
        on_click=start_new_experiment,
    )

    # ---------------- layout ----------------

    page.add(
        title,
        ft.Divider(),
        ft.Text("Criar novo experimento", size=20, weight=ft.FontWeight.BOLD),
        ft.Row([exp_name_field]),
        ft.Row(
            controls=[
                design_type_dropdown,
                num_factors_field,
                replicates_field,
                fractionality_field,
                center_points_field,
                rebuild_button,
            ]
        ),
        design_info_text,
        ft.Text("Configuração dos fatores", size=20, weight=ft.FontWeight.BOLD),
        factors_container,
        ft.Row([create_button, new_experiment_button]),
        create_status,
        result_text,
        ft.Divider(),
        ft.Text("Experimentos salvos", size=20, weight=ft.FontWeight.BOLD),
        ft.Row([experiments_dropdown, refresh_button]),
        details_text,
        ft.Text("Tabela do planejamento (valores reais)", size=18, weight=ft.FontWeight.BOLD),
        design_table,
        responses_title,
        responses_hint,
        responses_container,
        save_responses_button,
        responses_status,
        ft.Divider(),
        analysis_title,
        analysis_status,
        r2_text,
        ft.Text("Coeficientes do modelo", size=16, weight=ft.FontWeight.BOLD),
        coeff_table,
        ft.Text("Tabela ANOVA", size=16, weight=ft.FontWeight.BOLD),
        anova_table,
        ft.Divider(),
        pareto_title,
        pareto_status,
        pareto_open_button,
        pareto_url_label,
        ft.Divider(),
        surface_title,
        surface_status,
        surface_open_button,
        surface_url_label,
    )

    def on_route_change(e):
        reset_form()
        refresh_experiments(auto_select_first=False)

    page.on_route_change = on_route_change

    build_factor_fields()
    reset_form()
    refresh_experiments(auto_select_first=False)


if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
    )