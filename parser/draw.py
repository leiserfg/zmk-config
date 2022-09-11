from textwrap import dedent

from keyboard import Key, Keyboard, Layer, SplitLayout


def inline(text):
    return dedent(text).replace("\n", " ")


class Painter:
    def __init__(
        self,
        keyboard: Keyboard,
        layout: SplitLayout,
        key_radius=10,
        key_width=58,
        key_height=55,
        z_fraq=0.15,
        half_sep_fraq=0.5,
    ):
        (
            self.keyboard,
            self.layout,
            self.key_radius,
            self.key_width,
            self.key_height,
        ) = (keyboard, layout, key_radius, key_width, key_height)
        self.z = key_height * z_fraq
        self.half_sep = key_width * half_sep_fraq
        self.key_face_height = self.key_height - self.z

    def _text(self, x, y, text, *, font_size, font_color="black"):
        return inline(
            f"""
            <text
            text-anchor="middle"
            dominant-baseline="middle"
                      style="fill:{font_color};font-size:{font_size}px"
            x="{x}"
            y="{y}"
            >{text}</text>"""
        )

    def _rect(self, x, y, w, h, r, text="", fill="white", font_color="black"):
        rect_elem = inline(
            f"""
            <rect
            x="{x}"
            y="{y}"
            width="{w}"
            height="{h}"
            rx="{r}"
            style="fill:{fill};stroke:black;stroke-width:0.4;"/>
            """
        )
        words = str(text).split()
        line_spacing = h / 3
        shift = (h - (len(words) - 1) * line_spacing) / 2
        texts = "\n".join(
            self._text(
                x + w / 2,
                y + shift + line_spacing * i,
                word,
                font_color=font_color,
                font_size=line_spacing,
            )
            for i, word in enumerate(words)
        )
        return rect_elem + "\n" + texts

    def draw_released_key(self, x, y, text, font_color):
        return self._rect(
            x,
            y + self.z,
            self.key_width,
            self.key_face_height,
            self.key_radius,
            fill="black",
        ) + self._rect(
            x,
            y,
            self.key_width,
            self.key_face_height,
            self.key_radius,
            text=text,
            font_color=font_color,
        )

    def draw_pressed_key(self, x, y, text, font_color):
        return self._rect(
            x,
            y + self.z,
            self.key_width,
            self.key_face_height,
            self.key_radius,
            text=text,
            font_color=font_color,
        )

    def draw_layer(self, layer, y_offset):
        drawings = []
        for idx, key in enumerate(layer.keys):
            x, y = self.layout.key_coord(
                idx, self.key_width, self.key_height, self.half_sep
            )
            font_color = "#aaa" if key.is_transparent else "black"
            if key.is_pressed:
                drawings.append(self.draw_pressed_key(x, y + y_offset, key, font_color))
            else:
                drawings.append(
                    self.draw_released_key(x, y + y_offset, key, font_color)
                )
        return "\n".join(drawings)

    def draw_keyboard(self):
        board_w, board_h = self.layout.size(
            self.key_width, self.key_height, self.half_sep
        )
        total_h = (board_h + self.key_height) * len(self.keyboard)
        head = inline(
            f"""
            <svg
             width="{board_w}"
             height="{total_h}"
             viewBox="0 0 {board_w} {total_h}"
             xmlns="http://www.w3.org/2000/svg"
             style="
             font-family: SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace;
             font-size: {self.key_face_height/3}px;
             font-kerning: normal;
             text-rendering: optimizeLegibility;">"""
        )
        tail = "</svg>"
        return (
            head
            + "\n"
            + "\n".join(
                (
                    self._text(
                        board_w / 2,
                        idx * board_h + (idx + 0.5) * self.key_height,
                        str(layer),
                        font_size=self.key_height / 2,
                    )
                    + "/n"
                    + self.draw_layer(
                        layer, idx * board_h + (idx + 1) * self.key_height
                    )
                )
                for idx, layer in enumerate(self.keyboard)
            )
            + "\n"
            + tail
        )


def main():
    from pathlib import Path

    from parse import parse_keyboard, preprocess

    _here = Path(__file__).parent

    keyboard = (_here / "../zmk-config/config/cradio.keymap").absolute()
    keyboard = parse_keyboard(preprocess(keyboard.read_text()))
    layout = SplitLayout(3, 5, 2)
    painter = Painter(keyboard=keyboard, layout=layout)
    print(painter.draw_keyboard())


if __name__ == "__main__":
    main()
