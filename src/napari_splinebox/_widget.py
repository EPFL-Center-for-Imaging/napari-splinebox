import collections
from typing import TYPE_CHECKING

import magicgui
import numpy as np
import pandas as pd
import splinebox
from magicgui.widgets import Container, create_widget

if TYPE_CHECKING:
    import napari


class SplineBox(Container):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self._viewer = viewer

        self._shapes_layer_widget = create_widget(
            label="Shapes layer", annotation="napari.layers.Shapes"
        )
        self._basis_function_widget = magicgui.widgets.ComboBox(
            choices=(
                splinebox.basis_functions.B1,
                splinebox.basis_functions.B3,
                splinebox.basis_functions.Exponential,
                splinebox.basis_functions.CatmullRom,
            ),
            value=splinebox.basis_functions.B3,
            label="Basis function:",
        )
        self._point_type_widget = magicgui.widgets.ComboBox(
            choices=("Knots", "Control points"),
            value="Knots",
            label="Point type:",
        )
        self._steps_widget = magicgui.widgets.create_widget(
            100, label="Sampling steps between points:"
        )
        self._arc_length_sampling_widget = magicgui.widgets.CheckBox(
            text="Arc length sampling (slow, only click before saving)"
        )
        self._pixel_size_widget = magicgui.widgets.create_widget(
            1.0, label="Pixel size:"
        )
        self._save_folder_widget = magicgui.widgets.FileEdit(
            mode="d", label="Folder"
        )
        self._save_file_name_widget = magicgui.widgets.LineEdit(
            label="File name", value="spline"
        )
        self._save_extension_widget = magicgui.widgets.ComboBox(
            choices=(".csv",), label="File extension"
        )
        self._save_widget = magicgui.widgets.PushButton(text="Save")

        # connect your callbacks
        self._shapes_layer_widget.changed.connect(self._change_shapes_layer)
        self._basis_function_widget.changed.connect(self._update_spline_layer)
        self._point_type_widget.changed.connect(self._update_spline_layer)
        self._steps_widget.changed.connect(self._update_spline_layer)
        self._arc_length_sampling_widget.changed.connect(
            self._update_spline_layer
        )
        self._save_widget.changed.connect(self._save)

        # append into/extend the container with your widgets
        self.extend(
            [
                self._shapes_layer_widget,
                self._basis_function_widget,
                self._point_type_widget,
                self._steps_widget,
                self._arc_length_sampling_widget,
                self._pixel_size_widget,
                self._save_folder_widget,
                self._save_file_name_widget,
                self._save_extension_widget,
                self._save_widget,
            ]
        )

    def _get_spline_layer(self):
        shapes_layer = self._shapes_layer_widget.value
        spline_layer_name = f"{shapes_layer.name} spline"
        if spline_layer_name not in self._viewer.layers:
            self._viewer.add_shapes(
                edge_color="blue",
                edge_width=2,
                name=spline_layer_name,
            )
        return self._viewer.layers[spline_layer_name]

    def _change_shapes_layer(self):
        self._update_spline_layer()
        self._shapes_layer_widget.value.events.data.connect(
            self._update_spline_layer
        )

    def _update_spline_layer(self):
        spline_layer = self._get_spline_layer()
        spline_layer.selected_data = set(range(len(spline_layer.shape_type)))
        spline_layer.remove_selected()
        splines = []
        ts = []
        for i, shape_type in enumerate(
            self._shapes_layer_widget.value.shape_type
        ):
            if shape_type not in ["path", "polygon"]:
                print(f"Cannot convert shape type {shape_type} into a spline.")
                continue
            closed = shape_type == "polygon"
            points = self._shapes_layer_widget.value.data[i]
            M = points.shape[0]
            if (
                self._basis_function_widget.value
                == splinebox.basis_functions.Exponential
            ):
                basis_function = self._basis_function_widget.value(M)
            else:
                basis_function = self._basis_function_widget.value()
            if basis_function.support > M:
                print(
                    f"You need to create at least {basis_function.support} points for this basis function."
                )
                return
            spline = splinebox.spline_curves.Spline(
                M=M,
                basis_function=basis_function,
                closed=closed,
            )
            if self._point_type_widget.value == "Knots":
                spline.knots = points
            elif self._point_type_widget.value == "Control points":
                spline.control_points = points
            else:
                raise ValueError(
                    f"Unkown point type {self._point_type_widget.value}"
                )

            max_t = points.shape[0] if closed else points.shape[0] - 1
            if self._arc_length_sampling_widget.value:
                length = spline.arc_length()
                step_size = length / (max_t * (self._steps_widget.value + 1))
                lengths = np.linspace(0, length, round(length / step_size) + 1)
                t = spline.arc_length_to_parameter(lengths)
            else:
                step_size = 1 / (self._steps_widget.value + 1)
                t = np.linspace(0, max_t, round(max_t / step_size) + 1)

            values = spline.eval(t)
            spline_layer.add_paths(values)
            splines.append(spline)
            ts.append(t)
        return splines, ts

    def _save(self):
        folder = self._save_folder_widget.value
        file_name = self._save_file_name_widget.value
        extension = self._save_extension_widget.value
        path = folder / (file_name + extension)
        splines, ts = self._update_spline_layer()
        pixel_size = self._pixel_size_widget.value
        dict_df = collections.defaultdict(list)
        for spline_id, (spline, t) in enumerate(zip(splines, ts)):
            dict_df["ID"].extend([spline_id] * len(t))
            values = spline.eval(t)
            # TODO extend to higher dimension
            dict_df["t"].extend(t)
            dict_df["y"].extend(values[:, 0] * pixel_size)
            dict_df["x"].extend(values[:, 1] * pixel_size)
            dict_df["length"].extend(spline.arc_length(t) * pixel_size)
            dict_df["curvature"].extend(spline.curvature(t) / pixel_size)
        df = pd.DataFrame(dict_df)
        df.to_csv(path)
