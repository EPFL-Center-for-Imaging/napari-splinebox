import numpy as np
import splinebox

from napari_splinebox import napari_get_reader


def test_reader_one_spline(tmp_path):
    # write a single spline to json
    test_file = str(tmp_path / "spline.json")
    M = 10
    spline = splinebox.spline_curves.Spline(
        M=M, basis_function=splinebox.basis_functions.B3(), closed=False
    )
    spline.control_points = np.random.rand(M + 2, 2) * 100
    spline.to_json(test_file)

    reader = napari_get_reader(test_file)
    assert callable(reader)

    # make sure we're delivering the right format
    layer_data_list = reader(test_file)
    assert isinstance(layer_data_list, list) and len(layer_data_list) > 0
    layer_data_tuple = layer_data_list[0]
    assert isinstance(layer_data_tuple, tuple) and len(layer_data_tuple) > 0

    # make sure the spline is correctly represented in the layer data tuple
    np.testing.assert_allclose(spline.control_points, layer_data_tuple[0][0])
    assert (
        str(spline.basis_function)
        == layer_data_tuple[1]["properties"]["basis_function"][0]
    )
    assert (
        layer_data_tuple[1]["properties"]["point_type"][0] == "Control points"
    )
    if spline.closed:
        assert layer_data_tuple[1]["shape_type"][0] == "polygon"
    else:
        assert layer_data_tuple[1]["shape_type"][0] == "path"


def test_reader_multiple_splines(tmp_path):
    test_file = str(tmp_path / "spline.json")
    splines = []
    M = 10
    spline = splinebox.spline_curves.Spline(
        M=M, basis_function=splinebox.basis_functions.B3(), closed=False
    )
    spline.control_points = np.random.rand(M + 2, 2) * 100
    splines.append(spline)

    M = 4
    spline = splinebox.spline_curves.Spline(
        M=M, basis_function=splinebox.basis_functions.B1(), closed=False
    )
    spline.control_points = np.random.rand(M, 3) * 100
    splines.append(spline)

    M = 5
    spline = splinebox.spline_curves.Spline(
        M=M,
        basis_function=splinebox.basis_functions.Exponential(M),
        closed=True,
    )
    spline.control_points = np.random.rand(M, 2) * 100
    splines.append(spline)

    M = 7
    spline = splinebox.spline_curves.Spline(
        M=M, basis_function=splinebox.basis_functions.CatmullRom(), closed=True
    )
    spline.control_points = np.random.rand(M, 3) * 100
    splines.append(spline)

    splinebox.spline_curves.splines_to_json(test_file, splines)

    reader = napari_get_reader(test_file)
    assert callable(reader)

    # make sure we're delivering the right format
    layer_data_list = reader(test_file)
    assert isinstance(layer_data_list, list) and len(layer_data_list) > 0
    layer_data_tuple = layer_data_list[0]
    assert isinstance(layer_data_tuple, tuple) and len(layer_data_tuple) > 0

    for i, spline in enumerate(splines):
        # make sure the spline is correctly represented in the layer data tuple
        np.testing.assert_allclose(
            spline.control_points, layer_data_tuple[0][i]
        )
        assert (
            str(spline.basis_function)
            == layer_data_tuple[1]["properties"]["basis_function"][i]
        )
        assert (
            layer_data_tuple[1]["properties"]["point_type"][i]
            == "Control points"
        )
        if spline.closed:
            assert layer_data_tuple[1]["shape_type"][i] == "polygon"
        else:
            assert layer_data_tuple[1]["shape_type"][i] == "path"


def test_get_reader_pass():
    reader = napari_get_reader("fake.file")
    assert reader is None
