import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc


from tardisdash.get_data import get_data

external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    # dbc.themes.BOOTSTRAP,
]

app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
)

plots = get_data.convergence()

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
                figure=plots.plasma_updates(),
                id="plasma",
            )
        ),
        html.Div(
            dcc.Graph(
                figure=plots.spectrum_updates(),
                id="spectrum",
            )
        ),
    ]
)


def run(host="127.0.0.1", debug=True):
    app.run_server(debug=debug, host=host, port=3004)


if __name__ == "__main__":
    run()
