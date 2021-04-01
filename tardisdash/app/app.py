from os import execlp
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from tardis import plasma, run_tardis
import time
from tardisdash.get_data.get_data import convergence, detect_change
import plotly.graph_objects as go
from collections import defaultdict

external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    dbc.themes.BOOTSTRAP,
]

app = dash.Dash(
    external_stylesheets=external_stylesheets,
)

plots = convergence()
plasma_plot = plots.plasma_updates()
spectrum_plot = plots.spectrum_updates()
plasma_iteration_plot = plots.plasma_iteration()

index = 0
percentage_done = 0
spec_ind = 0
y_dict_w = defaultdict(list)
y_dict_t_rad = defaultdict(list)
changed = False

X = list(range(1, 61))  # TODO: from the config file
SHELLS = [0, 5, 10, 15]


def fire_callback(old_value, new_value):
    global changed
    changed = True


app.layout = html.Div(
    [
        html.Div(
            html.P(
                "Tardis Simulation Dashboard",
                style={
                    "font-size": "40px",
                    # "fontFamily": "monospace",
                    "letter-spacing": "5px",
                    "text-align": "center",
                    "font-weight": "light",
                    "color": "#525252",
                },
            )
        ),
        html.Div(
            html.Div(
                dbc.Progress(
                    id="progress",
                    animated=True,
                    style={
                        # "height": "30px",
                        "display": "center",
                        "text-align": "center",
                    },
                )
            ),
            style={
                # "border": "3px #5c5c5c solid",
                "padding-top": "5px",
                "padding-left": "110px",
                "padding-right": "120px",
                "padding-bottom": "20px",
            },
        ),
        html.Div(
            html.Div(
                dcc.Graph(
                    figure=plasma_plot,
                    id="plasma",
                    style={
                        "width": "100%",
                        "height": "100%",
                    },
                )
            ),
            style={
                "width": "100%",
                # "height": "1000px",
                # "border": "3px #5c5c5c solid",
                "padding-top": "5px",
                "padding-left": "30px",
                "padding-right": "20px",
                "padding-bottom": "20px",
                "overflow": "hidden",
            },
        ),
        html.Div(
            [
                html.Div(
                    html.Div(
                        dcc.Graph(
                            figure=spectrum_plot,
                            id="spectrum",
                            style={
                                "width": "100%",
                                "height": "100%",
                            },
                        )
                    ),
                    style={
                        "width": "50%",
                        # "height": "1000px",
                        "display": "inline-block",
                        # "border": "3px #5c5c5c solid",
                        "padding-top": "5px",
                        "padding-left": "10px",
                        "padding-right": "20px",
                        "padding-bottom": "20px",
                        "overflow": "hidden",
                    },
                ),
                html.Div(
                    html.Div(
                        dcc.Graph(
                            figure=plasma_iteration_plot,
                            id="plasma iteration",
                            style={
                                "width": "100%",
                                "height": "100%",
                            },
                        )
                    ),
                    style={
                        "width": "50%",
                        "display": "inline-block",
                        "padding-top": "5px",
                        "padding-left": "10px",
                        "padding-right": "20px",
                        "padding-bottom": "20px",
                        "overflow": "hidden",
                    },
                ),
            ],
            style={
                "width": "100%",
                "display": "inline-block",
                "padding-top": "5px",
                "padding-left": "10px",
                "padding-right": "20px",
                "padding-bottom": "20px",
                "overflow": "hidden",
            },
        ),
        html.Div(
            dcc.Interval(
                id="interval-component",
                interval=1 * 1000,
                n_intervals=0,
            )
        ),
        html.Div(id="no input", style={"display": "none"}),
        html.Div(id="no output", style={"display": "none"}),
    ]
)


def update_convergence(sim):
    """
    simulation callback
    """
    global index, percentage_done, spec_ind, y_dict_w, y_dict_t_rad
    index += 2
    spec_ind += 1
    percentage_done += 1.66666666667

    # updating colors
    plasma_plot["data"][index - 1]["line"]["color"] = "#9cc2ff"
    plasma_plot["data"][index - 2]["line"]["color"] = "#9cc2ff"
    spectrum_plot["data"][spec_ind - 1]["line"]["color"] = "#9cc2ff"

    # updating t_rad subplot
    plasma_plot.add_scatter(
        x=sim.model.velocity.value.tolist(),
        y=sim.model.t_rad.value.tolist(),
        line_color="#00378f",
        row=1,
        col=2,
    )
    # updating w subplot
    plasma_plot.add_scatter(
        x=sim.model.velocity.value.tolist(),
        y=sim.model.w.tolist(),
        line_color="#00378f",
        row=1,
        col=1,
    )
    # updating spectrum plot
    spectrum_plot.add_scatter(
        x=sim.runner.spectrum.wavelength.value.tolist()[0::80],
        y=sim.runner.spectrum.luminosity_density_lambda.value.tolist()[0::80],
        line_color="#00378f",
    )

    for ind in SHELLS:
        y_dict_w[f"Shell-{ind}"].append(sim.model.w.tolist()[ind])
        y_dict_t_rad[f"Shell-{ind}"].append(sim.model.t_rad.value.tolist()[ind])

    with plasma_iteration_plot.batch_update():
        for trace in range(2 * len(SHELLS)):
            plasma_iteration_plot.data[trace].x = X

            if plasma_iteration_plot.data[trace].xaxis == "x":
                plasma_iteration_plot.data[trace].y = y_dict_w[
                    plasma_iteration_plot.data[trace].name
                ]
            else:
                plasma_iteration_plot.data[trace].y = y_dict_t_rad[
                    plasma_iteration_plot.data[trace].name
                ]


plasma_change = detect_change()
plasma_change.register_callback(fire_callback)

plasma_change.value = plasma_plot


@app.callback(
    dash.dependencies.Output("no input", "children"),
    dash.dependencies.Input("no output", "children"),
)
def update_live_plots(_):
    sim = run_tardis(
        "tardis_example.yml",
        simulation_callbacks=[[update_convergence]],
    )
    return


@app.callback(
    [
        dash.dependencies.Output("plasma", "figure"),
        dash.dependencies.Output("spectrum", "figure"),
        dash.dependencies.Output("plasma iteration", "figure"),
        dash.dependencies.Output("progress", "value"),
    ],
    dash.dependencies.Input("interval-component", "n_intervals"),
)
def update_plasma(n):
    if changed:
        return (
            plasma_plot,
            spectrum_plot,
            plasma_iteration_plot,
            percentage_done,
        )

    else:
        return (
            None,
            None,
            None,
            percentage_done,
        )


def run(host="127.0.0.1", debug=True):
    app.run_server(debug=debug, host=host, port=9003)


if __name__ == "__main__":
    run()
