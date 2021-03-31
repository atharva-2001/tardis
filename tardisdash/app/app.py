from os import execlp
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from tardis import plasma, run_tardis
import time
from tardisdash.get_data.get_data import convergence
import plotly.graph_objects as go


external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    # dbc.themes.BOOTSTRAP,
]

app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
)

mathjax = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML"
app.scripts.append_script({"external_url": mathjax})

plots = convergence()
plasma_plot = plots.plasma_updates()
spectrum_plot = plots.spectrum_updates()

index = 0
percentage_done = 0
spec_ind = 0
changed = False


app.layout = html.Div(
    [
        html.Div(
            [
                dbc.Progress(
                    value=80,
                    id="animated-progress",
                    striped=True,
                    animated=True,
                )
            ]
        ),
        html.Div(
            dcc.Graph(
                figure=plasma_plot,
                id="plasma",
            )
        ),
        html.Div(
            dcc.Graph(
                figure=spectrum_plot,
                id="spectrum",
            )
        ),
        html.Div(
            dcc.Interval(
                id="interval-component",
                interval=1 * 1000,  # in milliseconds
                n_intervals=0,
            )
        ),
        html.Div(id="no input", style={"display": "none"}),
        html.Div(id="no output", style={"display": "none"}),
    ]
)


class detect_change:
    """
    detects change in a value
    copied from: https://stackoverflow.com/a/51885354/11974464
    """

    def __init__(self, initial_value=0):
        self._value = initial_value
        self._callbacks = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        global changed
        old_value = self._value
        self._value = new_value
        changed = False
        self._notify_observers(old_value, new_value)

    def _notify_observers(self, old_value, new_value):
        for callback in self._callbacks:
            callback(old_value, new_value)

    def register_callback(self, callback):
        self._callbacks.append(callback)


def update_convergence(sim):
    """
    simulation callback
    """
    global index, percentage_done, spec_ind
    index += 2
    spec_ind += 1
    percentage_done += 5

    # updating colors
    plasma_plot["data"][index - 1]["line"]["color"] = "#7dafff"
    plasma_plot["data"][index - 2]["line"]["color"] = "#7dafff"
    spectrum_plot["data"][spec_ind - 1]["line"]["color"] = "#7dafff"

    # updating t_rad subplot
    plasma_plot.add_scatter(
        x=sim.model.velocity.value.tolist(),
        y=sim.model.t_rad.value.tolist(),
        line_color="#0062ff",
        row=1,
        col=2,
    )
    # updating w subplot
    plasma_plot.add_scatter(
        x=sim.model.velocity.value.tolist(),
        y=sim.model.w.tolist(),
        line_color="#0062ff",
        row=1,
        col=1,
    )
    # updating spectrum plot
    spectrum_plot.add_scatter(
        x=sim.runner.spectrum.wavelength.value.tolist()[0::80],
        y=sim.runner.spectrum.luminosity_density_lambda.value.tolist()[0::80],
        line_color="#0000ff",
    )
    fire_callback_from_convergence()


def fire_callback(old_value, new_value):
    global changed
    changed = True

    return_plots(input=None)


def fire_callback_from_convergence():
    return_plots(input=None)


def return_plots(input):
    return plasma_plot


plasma_change = detect_change()
plasma_change.register_callback(fire_callback)
plasma_change.value = plasma_plot

# app.callback(
#     dash.dependencies.Output("plasma", "figure"),
#     dash.dependencies.Input("no output", "children"),
# )(return_plots)


@app.callback(
    # [
    #     dash.dependencies.Output("plasma", "figure"),
    #     dash.dependencies.Output("spectrum", "figure"),
    # ],
    # [
    #     dash.dependencies.Input("plasma", "figure"),
    #     dash.dependencies.Input("spectrum", "figure"),
    # ],
    dash.dependencies.Output("no input", "children"),
    dash.dependencies.Input("no output", "children"),
)
def update_live_plots(_):
    # time.sleep(20)
    sim = run_tardis(
        "tardis_example.yml",
        simulation_callbacks=[[update_convergence]],
    )
    return


@app.callback(
    [
        dash.dependencies.Output("plasma", "figure"),
        dash.dependencies.Output("spectrum", "figure"),
    ],
    dash.dependencies.Input("interval-component", "n_intervals"),
)
def update_plasma(n):
    if changed:
        return plasma_plot, spectrum_plot
    else:
        return None


def run(host="127.0.0.1", debug=True):
    app.run_server(debug=debug, host=host, port=3001)


if __name__ == "__main__":
    run()
