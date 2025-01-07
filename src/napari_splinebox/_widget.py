import collections
from typing import TYPE_CHECKING

import magicgui
import napari.utils
import numpy as np
import pandas as pd
import splinebox
from magicgui.widgets import Container, create_widget

import napari_splinebox._main as _main

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
                str(splinebox.basis_functions.B1()),
                str(splinebox.basis_functions.B3()),
                str(splinebox.basis_functions.Exponential(M=5)),
                str(splinebox.basis_functions.CatmullRom()),
            ),
            value=str(splinebox.basis_functions.B3()),
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
        self._comb_height_widget = magicgui.widgets.create_widget(
            50.0, label="Height of curvature comb:"
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
        self._shapes_layer_widget.changed.connect(
            self._callback_change_shapes_layer
        )
        self._basis_function_widget.changed.connect(
            self._update_properties_and_layers
        )
        self._point_type_widget.changed.connect(
            self._update_properties_and_layers
        )
        self._steps_widget.changed.connect(self._update_spline_layer)
        self._comb_height_widget.changed.connect(self._update_spline_layer)
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
                self._comb_height_widget,
                self._arc_length_sampling_widget,
                self._pixel_size_widget,
                self._save_folder_widget,
                self._save_file_name_widget,
                self._save_extension_widget,
                self._save_widget,
            ]
        )

    def _get_curvature_layer(self):
        shapes_layer = self._shapes_layer_widget.value
        curvature_layer_name = f"{shapes_layer.name} curvature"
        if curvature_layer_name not in self._viewer.layers:
            self._viewer.add_shapes(
                edge_color="blue",
                edge_width=2,
                opacity=0.5,
                name=curvature_layer_name,
            )
        return self._viewer.layers[curvature_layer_name]

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

    def _callback_change_shapes_layer(self):
        self._update_spline_layer(update_all=True)
        shapes_layer = self._shapes_layer_widget.value
        shapes_layer.events.data.connect(
            self._callback_change_in_shapes_layer_data
        )
        # This is a hack because there is no event for selected_data
        # https://github.com/napari/napari/issues/6886
        shapes_layer.events.highlight.connect(
            self._callback_change_in_shapes_layer_selected_data
        )

    def _callback_change_in_shapes_layer_data(self, event):
        shapes_layer = self._shapes_layer_widget.value

        if event.action == "adding":
            pass
        elif event.action == "added":
            self._update_properties_and_layers()
        elif event.action == "removing":
            pass
        elif event.action == "removed":
            spline_layer = self._get_spline_layer()
            spline_layer.selected_data = shapes_layer.selected_data
            spline_layer.remove_selected()
        elif event.action == "changed":
            self._update_properties_and_layers()

    def _update_properties_and_layers(self):
        self._set_properties()
        self._update_spline_layer()

    def _set_properties(self):
        shapes_layer = self._shapes_layer_widget.value
        new_properties = shapes_layer.properties

        for i in shapes_layer.selected_data:
            if "basis_function" not in new_properties:
                new_properties["basis_function"] = np.array(
                    [self._basis_function_widget.value]
                )
                new_properties["point_type"] = np.array(
                    [self._point_type_widget.value]
                )
            elif i < len(new_properties["basis_function"]):
                new_properties["basis_function"][
                    i
                ] = self._basis_function_widget.value
                new_properties["point_type"][i] = self._point_type_widget.value
            elif i == len(new_properties["basis_function"]):
                basis_functions = list(new_properties["basis_function"])
                basis_functions.append(self._basis_function_widget.value)
                new_properties["basis_function"] = basis_functions
                point_types = list(new_properties["point_type"])
                point_types.append(self._point_type_widget.value)
                new_properties["point_type"] = point_types
            else:
                raise RuntimeError(
                    f"selected shape {i} but the basis function property has length {len(new_properties['basis_function'])}"
                )
        shapes_layer.properties = new_properties

    def _update_spline_layer(self, update_all=False):
        """
        Update all updates all splines even if they are not selected.
        """
        shapes_layer = self._shapes_layer_widget.value
        if update_all:
            selected = set(np.arange(len(shapes_layer.data)))
        else:
            selected = shapes_layer.selected_data

        spline_layer = self._get_spline_layer()
        # curvature_layer = self._get_curvature_layer()

        for i in selected:
            # spline_layer.selected_data = {i}
            # curvature_layer.selected_data = {i}

            spline = _main.spline_from_shapes_layer(
                self._shapes_layer_widget.value, i
            )

            max_t = spline.M if spline.closed else spline.M - 1
            step_size = 1 / (self._steps_widget.value + 1)
            t = np.linspace(0, max_t, round(max_t / step_size) + 1)

            values = spline.eval(t)
            if i < len(spline_layer.data):
                new_data = spline_layer.data
                new_data[i] = values
                spline_layer.data = new_data
                spline_layer.refresh()
            else:
                spline_layer.add_paths(values)

            # normals = spline.normal(t)
            # curvature = spline.curvature(t)
            # max_comb_height = self._comb_height_widget.value
            # d = max_comb_height / np.max(np.abs(curvature))
            # comb = values + d * curvature[:, np.newaxis] * normals

            # curvature_layer.add_paths(comb)
            # for p in range(0, len(comb), 7):
            #     curvature_layer.add_paths(
            #         np.stack([values[p], comb[p]], axis=0)
            #     )

    def _callback_change_in_shapes_layer_selected_data(self):
        shapes_layer = self._shapes_layer_widget.value
        if len(shapes_layer.properties) == 0:
            return
        selected = list(shapes_layer.selected_data)
        if len(selected) == 1:
            index = selected[0]
            self._basis_function_widget.value = shapes_layer.properties[
                "basis_function"
            ][index]
            self._point_type_widget.value = shapes_layer.properties[
                "point_type"
            ][index]
        elif len(selected) > 1:
            pass

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
