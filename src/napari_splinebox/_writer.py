"""
This module is an example of a barebones writer plugin for napari.

It implements the Writer specification.
see: https://napari.org/stable/plugins/guides.html?#writers

Replace code below according to your needs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Sequence, Tuple, Union

import splinebox

import napari_splinebox._main as _main

if TYPE_CHECKING:
    DataType = Union[Any, Sequence[Any]]
    FullLayerData = Tuple[DataType, dict, str]


def write_single_shapes_layer(path: str, data: Any, meta: dict) -> List[str]:
    """Writes a single image layer.

    Parameters
    ----------
    path : str
        A string path indicating where to save the image file.
    data : The layer data
        The `.data` attribute from the napari layer.
    meta : dict
        A dictionary containing all other attributes from the napari layer
        (excluding the `.data` layer attribute).

    Returns
    -------
    [path] : A list containing the string path to the saved file.
    """
    splines = []
    for i in range(len(data)):
        spline = _main.spline_from_layer_tuple(data, meta, i)
        splines.append(spline)

    splinebox.spline_curves.splines_to_json(path, splines)
    return [path]


def write_multiple_layers(path: str, data: List[FullLayerData]) -> List[str]:
    """Writes multiple layers of different types.

    Parameters
    ----------
    path : str
        A string path indicating where to save the data file(s).
    data : A list of layer tuples.
        Tuples contain three elements: (data, meta, layer_type)
        `data` is the layer data
        `meta` is a dictionary containing all other metadata attributes
        from the napari layer (excluding the `.data` layer attribute).
        `layer_type` is a string, eg: "image", "labels", "surface", etc.

    Returns
    -------
    [path] : A list containing (potentially multiple) string paths to the saved file(s).
    """

    # implement your writer logic here ...

    # return path to any file(s) that were successfully written
    return [path]
