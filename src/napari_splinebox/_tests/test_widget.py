# def test_image_threshold_widget(make_napari_viewer):
#     viewer = make_napari_viewer()
#     layer = viewer.add_image(np.random.random((100, 100)))
#     my_widget = ImageThreshold(viewer)
#
#     # because we saved our widgets as attributes of the container
#     # we can set their values without having to "interact" with the viewer
#     my_widget._image_layer_combo.value = layer
#     my_widget._threshold_slider.value = 0.5
#
#     # this allows us to run our functions directly and ensure
#     # correct results
#     my_widget._threshold_im()
#     assert len(viewer.layers) == 2
