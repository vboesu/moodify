import random
import math
import numpy as np

from .color import Color
from .helpers import random_color, noise, shift_hue


class BasePalette:
    def __init__(self, initial_color=None, n=5, **kwargs):
        self.initial_color = initial_color
        self.n = n
        self.palette = None

        if self.initial_color is None:
            self.initial_color = random_color()

        if not isinstance(self.initial_color, Color):
            self.initial_color = Color(self.initial_color)

        # Generate automatically
        self.generate()

    def sort(self):
        """Sort palette based on lightness"""
        self.palette = sorted(self.palette, key=lambda x: (x.lightness, x.hue))

    def generate(self):
        """Generate palette based on palette mode"""
        pass

    @property
    def json(self):
        return [
            {
                "name": c.name,
                "formats": {
                    "hex": c.hex,
                    "rgb": c.out("rgb"),
                    "hsl": c.out("hsl"),
                    "hsv": c.out("hsv"),
                },
                "lightness": c.lightness,
            }
            for c in self.palette
        ]


class ShiftPalette(BasePalette):
    def fill_colors(self, colors, iterations="auto", use="all"):
        # Generates shades of the existing colors

        if use != "all" and type(use) in [list, tuple, np.ndarray]:
            colors = colors[use[0] : use[1]]

        # Determine iterations based on missing number of colors
        iterations = (
            math.ceil(self.n / (self.n - len(colors)))
            if iterations == "auto"
            else iterations
        )

        if self.n > len(colors):
            fill = []
            for color in colors:
                for _ in range(iterations):
                    fill.append(color.shade())

            # Append sample of the created shades to fill to n colors
            if fill:
                colors += random.sample(fill, self.n - len(colors))

        return colors

    def generate(self, n_shifts, luminance_min=20, luminance_max=80):
        # Create a palette that takes an input color and creates a hue shift palette out of it
        h, s, l = self.initial_color.out("hsl")

        # Clip lightness
        l = min(max(l, luminance_min), luminance_max)
        self.palette = [self.initial_color]

        for i in range(1, n_shifts):
            shift = i * 360 / n_shifts
            self.palette.append(
                Color((shift_hue(h, noise(shift)), s, l), format_in="hsl")
            )

        # Add a significantly lighter shade of hue by going through two rounds of lighter shades
        light = self.initial_color.shade("lighter").shade("lighter")

        # Fill until at least n colors are reached
        if self.n > n_shifts + 1:
            self.palette = self.fill_colors(self.palette)[: self.n - 1]

        self.palette += [light]

        self.sort()
        return self.palette


class Monochromatic(BasePalette):
    mode = "monochromatic"

    def generate(self):
        # Take the hue and value, only edit saturation
        h, _, v = self.initial_color.out("hsv")
        dist = np.linspace(15, 85, self.n)

        # Value has to be between 85 and 100, otherwise the palette makes no sense
        v = min(max(v, 85), 100)

        # Create colors according to linear distribution
        self.palette = [Color((h, s, v), format_in="hsv") for s in dist]
        self.sort()
        return self.palette


class Analogous(BasePalette):
    mode = "analogous"

    def generate(self):
        # Take n neighboring hues
        h, s, v = self.initial_color.out("hsv")
        start = -1 * ((self.n - 1) / 2) * 10
        end = ((self.n - 1) / 2) * 10

        dist = np.linspace(start, end, self.n)

        # Saturation has to be greater than 50
        s = max(s, 50)

        # Create colors according to linear distribution
        self.palette = [Color((shift_hue(h, h_), s, v), format_in="hsv") for h_ in dist]
        self.sort()
        return self.palette


class Compound(ShiftPalette):
    mode = "compound"

    def generate(self, n_shifts=3):
        # Shift hues by 150 and 210 (Y-shape) and generate shades
        h, s, l = self.initial_color.out("hsl")

        # Clip lightness
        l = min(max(l, 20), 80)
        self.palette = [self.initial_color]

        # Shift
        for i in [150, 210]:
            self.palette.append(Color((shift_hue(h, noise(i)), s, l), format_in="hsl"))

        # Fill additional colors
        self.palette = self.fill_colors(self.palette)
        self.sort()
        return self.palette


class Complementary(ShiftPalette):
    mode = "complementary"

    def generate(self, n_shifts=2):
        return super().generate(n_shifts)


class Triadic(ShiftPalette):
    mode = "triadic"

    def generate(self, n_shifts=3):
        return super().generate(n_shifts)


class Tetradic(ShiftPalette):
    mode = "tetradic"

    def generate(self, n_shifts=4):
        return super().generate(n_shifts)


class UI(ShiftPalette):
    mode = "ui"

    def generate(self, n_shifts=-1):
        # Create a color palette according to the following scheme
        # 1. Create vibrant color (primary color)
        # 2. Create light color (secondary color) with h = 1.h, 5 < 1.s < 10 and 90 < 1.l < 100
        # 3. Create accent color (tertiary color) with 1.h + 30 < h < 1.h + 40, s = 1.s and 1.l + 5 < l < 1.l + 10
        # 4. For remaining: create complementary color, fill with shade of primary, tertiary and complementary

        h, s, l = self.initial_color.out("hsl")

        # Clip saturation and brightness
        s = min(max(s, 55), 75)
        l = min(max(l, 50), 80)

        secondary = Color((h, noise(7.5, 2.5), noise(95)), format_in="hsl")
        tertiary = Color(
            (shift_hue(h, noise(35)), s, noise(l + 7.5, 2.5)), format_in="hsl"
        )

        self.palette = [self.initial_color, secondary, tertiary]

        if self.n > 3:
            # Create complementary color, from triadic
            triad = Triadic(self.initial_color, n=3)
            comp = random.choice(triad.palette[1:])
            self.palette.append(comp)

        # Fill additional colors
        self.palette = self.fill_colors([self.initial_color, tertiary, comp])[
            : self.n - 1
        ] + [secondary]
        self.sort()
        return self.palette


class AutoPalette(BasePalette):
    def __new__(self, initial_color=None, n=5, **kwargs):
        # Return palette based on random mode
        return MAP.get(random.choice(list(MAP.keys())))(
            initial_color=initial_color, n=n, **kwargs
        )


MAP = {
    "monochromatic": Monochromatic,
    "compound": Compound,
    "analogous": Analogous,
    "complementary": Complementary,
    "triadic": Triadic,
    "tetradic": Tetradic,
    "ui": UI,
}


def get_palette(mode="auto", initial_color=None, n=5, **kwargs):
    return MAP.get(mode, AutoPalette)(initial_color=initial_color, n=n, **kwargs)