from tardis import run_tardis
import plotly.graph_objects as go


class convergence:
    # def __init__(self, sim):
    #     self.sim = sim

    def plasma_updates(self):
        # making subplots
        fig = go.FigureWidget().set_subplots(1, 2)
        fig.add_scatter(row=1, col=1)
        fig.add_scatter(row=1, col=2)

        # updating axes
        fig["layout"]["yaxis"]["title"] = r"W"
        fig["layout"]["xaxis"]["title"] = r"Shell Velocity"

        fig["layout"]["yaxis2"]["title"] = r"T_rad"
        fig["layout"]["xaxis2"]["title"] = r"Shell Velocity"

        fig["layout"]["yaxis2"]["range"] = [9000, 14000]
        fig["layout"]["xaxis"]["showexponent"] = "all"
        fig["layout"]["xaxis2"]["showexponent"] = "all"
        fig["layout"]["xaxis"]["exponentformat"] = "e"
        fig["layout"]["xaxis2"]["exponentformat"] = "e"

        fig = fig.update_layout(showlegend=False)
        self.plasma_subplots = fig
        return fig

    def spectrum_updates(self):
        fig = go.FigureWidget()
        fig.add_scatter(x=list(range(500, 20000))[0::80])

        fig.update_yaxes(title_text=r"Luminosity", range=[0, 7e39])
        fig.update_xaxes(title_text=r"Wavelength")

        fig.update_layout(showlegend=False)
        self.spectrum_fig = fig
        return fig

    # def add_scatter_plot(self, fig, **kwargs):
    #     fig.add_scatter(
    #         x=kwargs["x"], y=kwargs["y"], line_color=kwargs["line_color"]
    #     )
    #     return fig

    # def update_line_color(self, fig, index, color="#7dafff"):
    #     fig["data"][index]["line"]["color"] = color


# plots = convergence(sim)

# plasma_plot = plots.plasma_updates()
# spectrum_plot = plots.spectrum_updates()

index = 0
percentage_done = 0


def update_convergence(sim, plasma_plot, spectrum_plot):
    global index, percentage_done
    index += 2
    percentage_done += 5

    # updating colors
    plasma_plot["data"][index - 1]["line"]["color"] = "#7dafff"
    plasma_plot["data"][index - 2]["line"]["color"] = "#7dafff"
    spectrum_plot["data"][index - 2]["line"]["color"] = "#7dafff"

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
