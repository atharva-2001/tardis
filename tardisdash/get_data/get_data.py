from tardis import run_tardis
import plotly.graph_objects as go


class convergence:
    # def __init__(self, sim):
    #     self.sim = sim

    def plasma_updates(self):
        # making subplots
        fig = go.FigureWidget().set_subplots(1, 2, horizontal_spacing=0.05)
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

        fig = fig.update_layout(
            showlegend=False,
            height=300,
            margin={
                "t": 0,
                "r": 0,
                "l": 0,
                "b": 0,
            },
        )
        self.plasma_subplots = fig
        return fig

    def spectrum_updates(self):
        fig = go.FigureWidget()
        fig.add_scatter()

        fig.update_yaxes(title_text=r"Luminosity", range=[0, 7e39])
        fig.update_xaxes(title_text=r"Wavelength")

        fig.update_layout(
            showlegend=False,
            height=500,
            margin={"pad": 0, "t": 0, "r": 0, "l": 0, "b": 0},
            xaxis=dict(range=[500, 12000]),
        )
        self.spectrum_fig = fig
        return fig

    def plasma_iteration(self):
        line_colors = ["#7fcdbb", "#1d91c0", "#225ea8", "#081d58"]
        shells = [0, 5, 10, 15]
        fig = go.FigureWidget().set_subplots(
            2, 1, shared_xaxes=True, vertical_spacing=0.08
        )

        for i, line_color in zip(shells, line_colors):
            fig.add_scatter(
                name=f"Shell-{i}",
                mode="lines",
                line_color=line_color,
                row=1,
                col=1,
            )
            fig.add_scatter(
                name=f"Shell-{i}",
                mode="lines",
                line_color=line_color,
                row=2,
                col=1,
            )

        # updating axes
        fig = fig.update_layout(
            showlegend=False,
            yaxis=dict(title=r"W"),
            yaxis2=dict(title=r"T_rad"),
            xaxis=dict(
                visible=False,
                zeroline=False,
                range=[1, 20],
                dtick=2,
                title=r"Iteration Number",
            ),
            xaxis2=dict(
                visible=True,
                showgrid=False,
                zeroline=False,
                range=[1, 20],
                dtick=2,
                title=r"Iteration Number",
            ),
            height=500,
            margin={"pad": 0, "t": 0, "r": 0, "l": 0, "b": 0},
        )
        return fig


# plots = convergence(sim)

# plasma_plot = plots.plasma_updates()
# spectrum_plot = plots.spectrum_updates()

# index = 0
# percentage_done = 0


# def update_convergence(sim, plasma_plot, spectrum_plot):
#     global index, percentage_done
#     index += 2
#     percentage_done += 5

#     # updating colors
#     plasma_plot["data"][index - 1]["line"]["color"] = "#7dafff"
#     plasma_plot["data"][index - 2]["line"]["color"] = "#7dafff"
#     spectrum_plot["data"][index - 2]["line"]["color"] = "#7dafff"

#     # updating t_rad subplot
#     plasma_plot.add_scatter(
#         x=sim.model.velocity.value.tolist(),
#         y=sim.model.t_rad.value.tolist(),
#         line_color="#0062ff",
#         row=1,
#         col=2,
#     )
#     # updating w subplot
#     plasma_plot.add_scatter(
#         x=sim.model.velocity.value.tolist(),
#         y=sim.model.w.tolist(),
#         line_color="#0062ff",
#         row=1,
#         col=1,
#     )

#     # updating spectrum plot
#     spectrum_plot.add_scatter(
#         x=sim.runner.spectrum.wavelength.value.tolist()[0::80],
#         y=sim.runner.spectrum.luminosity_density_lambda.value.tolist()[0::80],
#         line_color="#0000ff",
#     )
