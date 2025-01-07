"""
This module provides the functions for the conversion between shapes layers and splinebox.spline_curves.Spline.
"""

import math

import splinebox

DEFAULT_BASIS_FUNCTION = str(splinebox.basis_functions.B3())


def spline_from_layer_tuple(
    data,
    meta,
    index,
    default_basis_function=DEFAULT_BASIS_FUNCTION,
    default_point_type="Knots",
):
    shape_type = meta["shape_type"][index]
    if shape_type not in ["path", "polygon"]:
        raise RuntimeError(
            f"Cannot convert shape type {shape_type} into a spline."
        )

    closed = shape_type == "polygon"
    points = data[index]
    M = points.shape[0]

    if "basis_function" in meta["properties"]:
        basis_function_name = meta["properties"]["basis_function"][index]
    else:
        basis_function_name = default_basis_function
    basis_function = splinebox.basis_functions.basis_function_from_name(
        basis_function_name, M=M
    )

    if "point_type" in meta["properties"]:
        point_type = meta["properties"]["point_type"][index]
    else:
        point_type = default_point_type
    if point_type == "Control points" and not closed:
        M -= 2 * (math.ceil(basis_function.support / 2) - 1)

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

    if point_type == "Knots":
        spline.knots = points
    elif point_type == "Control points":
        spline.control_points = points
    else:
        raise ValueError(f"Unkown point type {point_type}")
    return spline


def spline_from_shapes_layer(
    layer,
    index=None,
    default_basis_function=DEFAULT_BASIS_FUNCTION,
    default_point_type="Knots",
):
    return spline_from_layer_tuple(
        layer.data,
        {"shape_type": layer.shape_type, "properties": layer.properties},
        index,
        default_basis_function=default_basis_function,
        default_point_type=default_point_type,
    )


def splines_from_shapes_layer(layer):
    splines = [
        spline_from_shapes_layer(layer, i) for i in range(len(layer.data))
    ]
    return splines
