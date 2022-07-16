import json
import numpy as np

from pathlib import Path

path = Path(__file__).parent / "data/color_names.json"

COLOR_NAME_CACHE = {}
COLOR_NAMES = {}

# Load color names from json file
with path.open() as f:
    names = json.load(f)

for code, name in names.items():
    # RGB tuple as key
    color = tuple(map(int, code.split(",")))
    COLOR_NAMES[color] = name


def color_name(color):
    # Validate input
    if type(color) not in [list, tuple, np.ndarray] or len(color) != 3:
        raise ValueError(
            f"Requires RGB tuple or list of length 3, received {type(color)} of length {len(color)}"
        )

    # Convert all to tuple because they are hashable
    color = tuple(color)

    if color in COLOR_NAMES:
        return COLOR_NAMES[color]

    elif color not in COLOR_NAME_CACHE:
        # Find closest color
        colors_arr = np.array(list(COLOR_NAMES.keys()))
        color_arr = np.array(color)

        # Calculate euclidean distance to all colors
        distances = np.sqrt(np.sum((colors_arr - color_arr) ** 2, axis=1))

        # Save name of closest color to cache
        name = list(COLOR_NAMES.values())[distances.argmin()]
        COLOR_NAME_CACHE[color] = name

    return COLOR_NAME_CACHE[color]