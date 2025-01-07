try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._reader import napari_get_reader
from ._widget import SplineBox
from ._writer import write_multiple_layers, write_single_shapes_layer

# from ._sample_data import make_sample_data

__all__ = (
    "napari_get_reader",
    "write_single_shapes_layer",
    "write_multiple_layers",
    # "make_sample_data",
    "SplineBox",
)
