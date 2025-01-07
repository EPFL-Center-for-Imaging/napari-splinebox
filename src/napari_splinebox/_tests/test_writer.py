import numpy as np
import splinebox

from napari_splinebox import write_single_shapes_layer


def test_write_single_shapes_layer(tmpdir):
    path = str(tmpdir / "testfile.json")
    data = [
        np.random.rand(5, 2) * 10,
        np.random.rand(10, 3) * 100,
        np.random.rand(7, 3) * 100,
    ]
    meta = {
        "shape_type": ["polygon", "path", "path"],
        "properties": {
            "basis_function": ["B3", "Exponential", "CatmullRom"],
            "point_type": ["Control points", "Control points", "Knots"],
        },
    }
    write_single_shapes_layer(path, data, meta)

    splines = splinebox.spline_curves.splines_from_json(path)

    assert len(splines) == len(data)

    for i, spline in enumerate(splines):
        if meta["shape_type"][i] == "polygon":
            assert spline.closed
        elif meta["shape_type"][i] == "path":
            assert not spline.closed
        else:
            raise ValueError

        assert meta["properties"]["basis_function"][i] == str(
            spline.basis_function
        )

        if meta["properties"]["point_type"][i] == "Control points":
            np.testing.assert_allclose(data[i], spline.control_points)
        else:
            test_spline = splinebox.spline_curves.Spline(
                M=data[i].shape[0],
                basis_function=splinebox.basis_functions.basis_function_from_name(
                    meta["properties"]["basis_function"][i]
                ),
                closed=meta["shape_type"][i] == "polygon",
            )
            test_spline.knots = data[i]
            np.testing.assert_allclose(
                test_spline.control_points, spline.control_points
            )
