import random

from .color import Color

RANDOM_COLOR_MODES = {
    "default": ((10, 90), (20, 80)),
    "pastel": ((25, 75), (60, 90)),
    "muted": ((40, 70), (10, 40)),
    "neon": ((90, 100), (40, 60)),
}

HUE_RANGES = {
    "random": (0, 360),
    "red": (-19, 20),
    "orange": (21, 40),
    "yellow": (41, 70),
    "green": (71, 160),
    "cyan": (161, 190),
    "blue": (191, 260),
    "violet": (261, 290),
    "pink": (291, 340),
}


def noise(center, distance=5):
    """Create random value within range of value"""
    return random.randint(center - distance, center + distance)


def shift_hue(hue, shift):
    return (hue + shift) % 360


def random_color(mode="default", hue_range="random"):
    """Create random color based on predefined color filters"""
    mode = mode.lower()
    hue_range = hue_range.lower()

    # Validate mode
    if mode not in RANDOM_COLOR_MODES:
        raise ValueError(
            f"mode has to be in {list(RANDOM_COLOR_MODES.keys())}, received {mode}"
        )

    # Validate hue range
    if hue_range not in HUE_RANGES:
        raise ValueError(
            f"hue_range has to be in {list(HUE_RANGES.keys())}, received {hue_range}"
        )

    hue = shift_hue(0, random.randint(*HUE_RANGES[hue_range]))

    res = (hue,) + tuple(
        random.randint(*value_range) for value_range in RANDOM_COLOR_MODES[mode]
    )
    return Color(res, format_in="hsl")