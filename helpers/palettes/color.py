import math
import random
import numpy as np

from .names import color_name

EXPAND = {"hsl": (360, 100, 100), "hsv": (360, 100, 100), "rgb": (255, 255, 255)}
COLOR_FORMATS = {
    "hex": ([str], [6, 7]),
    "hsl": ([tuple, list, np.ndarray], [3]),
    "hsv": ([tuple, list, np.ndarray], [3]),
    "rgb": ([tuple, list, np.ndarray], [3]),
}


def expand(val, form):
    """Convert values from [0, 1] to [0, 255], [0, 360], [0, 100]"""
    if form not in EXPAND:
        raise ValueError(f"Invalid format {form}")
    return tuple(int(a * b) for a, b in zip(val, EXPAND[form]))


def collapse(val, form):
    """Convert values from [0, 255], [0, 360], [0, 100] to [0, 1]"""
    if form not in EXPAND:
        raise ValueError(f"Invalid format {form}")
    return tuple(a / b for a, b in zip(val, EXPAND[form]))


class Color:
    def __init__(self, value, format_in="hex"):
        self.format_in = format_in.lower()

        # Validate format
        if not format_in in COLOR_FORMATS:
            raise ValueError(
                f"format_in has to be in {COLOR_FORMATS.keys()}, received {format_in}"
            )

        # Validate value format
        if type(value) not in COLOR_FORMATS[format_in][0]:
            raise TypeError(
                f"value has to be of type in {COLOR_FORMATS[format_in][0]}, received {type(value)}"
            )

        # Validate value length
        if len(value) not in COLOR_FORMATS[format_in][1]:
            raise ValueError(
                f"value has to be of length in {COLOR_FORMATS[format_in][1]}, received {len(value)}"
            )

        setattr(self, self.format_in, value)

        if self.format_in != "hex":
            self.hex = self._convert(value, format_in=self.format_in)

    def __str__(self):
        return f"#{self.out()}"

    @property
    def name(self):
        return color_name(self.out("rgb"))

    @property
    def hue(self):
        return self.out("hsl")[0]

    @property
    def lightness(self):
        return self.out("hsl")[2]

    @classmethod
    def batch(self, colors, format_in="hex"):
        return list(map(lambda x: Color(x, format_in=format_in), colors))

    def shade(self, mode="auto"):
        MODES = ["auto", "lighter", "darker"]

        # Validate mode
        if mode not in MODES:
            raise ValueError(f"mode has to be in {MODES}, received {mode}")

        h, s, l = self.out("hsl")

        if mode == "auto":
            # Generate complementary lightness with bias towards creating lighter shade
            if l > 60:
                return self.shade(mode="darker")
            else:
                return self.shade(mode="lighter")

        elif mode == "darker":
            new_l = max(l - random.randint(10, 20), 0)

        elif mode == "lighter":
            new_l = min(l + random.randint(10, 20), 100)

        return Color((h, s, new_l), format_in="hsl")

    def _convert(self, value, format_out="hex", format_in="hex"):
        # Source for hsl/hsv conversions (adapted): https://gist.github.com/mathebox/e0805f72e7db3269ec22

        # HEX to RGB
        if format_out == "rgb":
            value = value.lstrip("#")
            return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))

        # HEX to HSV
        elif format_out == "hsv":
            r, g, b = collapse(self.out("rgb"), "rgb")
            high = max(r, g, b)
            low = min(r, g, b)
            h = s = v = high

            d = high - low
            s = 0 if high == 0 else d / high

            if high == low:
                h = 0.0
            else:
                h = {
                    r: (g - b) / d + (6 if g < b else 0),
                    g: (b - r) / d + 2,
                    b: (r - g) / d + 4,
                }[high]
                h /= 6

            return expand((h, s, v), "hsv")

        # HEX to HSL
        elif format_out == "hsl":
            # Convert to HSV first
            res = self.out("hsv")
            h, s, v = collapse(res, "hsv")
            l = 0.5 * v * (2 - s)
            s = v * s / (1 - math.fabs(2 * l - 1)) if l < 1 and l > 0 else 0

            return expand((h, s, l), "hsl")

        # Anything to HEX
        elif format_out == "hex":
            if format_in == "rgb":
                return "%02x%02x%02x" % tuple(value)

            elif format_in == "hsv":
                h, s, v = collapse(value, "hsv")

                i = math.floor(h * 6)
                f = h * 6 - i
                p = v * (1 - s)
                q = v * (1 - f * s)
                t = v * (1 - (1 - f) * s)

                res = [
                    (v, t, p),
                    (q, v, p),
                    (p, v, t),
                    (p, q, v),
                    (t, p, v),
                    (v, p, q),
                ][int(i % 6)]

                res = expand(res, "rgb")
                return self._convert(res, "hex", "rgb")

            elif format_in == "hsl":
                # Convert to HSV
                h, s, l = collapse(value, "hsl")
                v = (2 * l + s * (1 - math.fabs(2 * l - 1))) / 2
                s = 2 * (v - l) / v

                res = expand((h, s, v), "hsv")
                return self._convert(res, "hex", "hsv")

    def out(self, format_out="hex"):
        """Return self in color format"""
        if not format_out in COLOR_FORMATS:
            raise ValueError(
                f"format has to be in {COLOR_FORMATS.keys()}, received {format_out}"
            )

        if not hasattr(self, format_out) or getattr(self, format_out) is None:
            setattr(self, format_out, self._convert(self.hex, format_out=format_out))

        # Convert to string or tuple, depending on output format
        return COLOR_FORMATS[format_out][0][0](getattr(self, format_out))