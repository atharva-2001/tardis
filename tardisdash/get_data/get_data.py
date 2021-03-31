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
