import inspect

import pytest

from quickticket.errors import ImageDimensionsExceeded, ImageDimensionsTooSmall

MIN_SIZE = (128, 128)
MAX_SIZE = (6684, 6684)


@pytest.mark.parametrize(
    "size",
    [
        (0, 0),
        (127, 128),
        (128, 127),
        (64, 640),
        # Width is within bounds, so a lexicographic comparison would accept this
        (200, 64),
    ],
)
def test_image_dimensions_too_small_raise_if_below(size: tuple[int, int]) -> None:
    with pytest.raises(ImageDimensionsTooSmall) as exc_info:
        ImageDimensionsTooSmall.raise_if_below(size, min_size=MIN_SIZE)

    exc = exc_info.value
    assert exc.size == size
    assert exc.min_size == MIN_SIZE
    assert str(exc) == f"Image dimensions too small: {size[0]}x{size[1]} < 128x128"


@pytest.mark.parametrize(
    "size",
    [
        (128, 128),
        (129, 128),
        (128, 129),
        (200, 128),
        (6684, 6684),
    ],
)
def test_image_dimensions_too_small_accepts(size: tuple[int, int]) -> None:
    ImageDimensionsTooSmall.raise_if_below(size, min_size=MIN_SIZE)


@pytest.mark.parametrize(
    "size",
    [
        (6685, 6684),
        (6684, 6685),
        (8192, 8192),
        (0, 8192),
        # Width is within bounds, so a lexicographic comparison would accept this
        (128, 6685),
    ],
)
def test_image_dimensions_exceeded_raise_if_above(size: tuple[int, int]) -> None:
    with pytest.raises(ImageDimensionsExceeded) as exc_info:
        ImageDimensionsExceeded.raise_if_above(size, max_size=MAX_SIZE)

    exc = exc_info.value
    assert exc.size == size
    assert exc.max_size == MAX_SIZE
    assert str(exc) == f"Image dimensions too large: {size[0]}x{size[1]} > 6684x6684"


@pytest.mark.parametrize(
    "size",
    [
        (6684, 6684),
        (6683, 6684),
        (6684, 6683),
        (128, 6684),
        (128, 128),
    ],
)
def test_image_dimensions_exceeded_accepts(size: tuple[int, int]) -> None:
    ImageDimensionsExceeded.raise_if_above(size, max_size=MAX_SIZE)


def test_image_dimension_limits_are_keyword_only() -> None:
    # Intentional keyword-only parameters to avoid mis-ordering arguments
    below = inspect.signature(ImageDimensionsTooSmall.raise_if_below).parameters
    above = inspect.signature(ImageDimensionsExceeded.raise_if_above).parameters
    assert below["min_size"].kind is inspect.Parameter.KEYWORD_ONLY
    assert above["max_size"].kind is inspect.Parameter.KEYWORD_ONLY
