from dataclasses import dataclass
from functools import cached_property

_code_to_text = {
    "space": "␣",
    "spc": "␣",
    "hash": "#",
    "bslh": "\\",
    "fslh": "/",
    "dollar": "$",
    "dllr": "$",
    "amps": "&amp;",
    "tilde": "~",
    "excl": "!",
    "qmark": "?",
    "pscrn": "□",
    "printscreen": "□",
    "plus": "+",
    "kp_plus": "+",
    "minus": "-",
    "pipe": "|",
    "star": "*",
    "under": "_",
    "equal": "=",
    "kp_equal": "=",
    "percent": "%",
    "prcnt": "%",
    "dot": ".",
    "comma": ",",
    "semi": ";",
    "scln": ";",
    "dqt": '"',
    "double_quotes": '"',
    "semi": ";",
    "sqt": "'",
    "lshift": "shift",
    "rshift": "shift",
    "lctrl": "ctrl",
    "rctrl": "ctrl",
    "lalt": "alt",
    "ralt": "altgr",
    "lgui": "❖",
    "rgui": "❖",
    "enter": "↵",
    "ret": "↵",
    "left": "🡰",
    "right": "🡲",
    "down": "🡳",
    "up": "🡱",
    "esc": "⎋",
    "del": "⌦",
    "bspc": "⌫",
    "at": "@",
    "caret": "^",
    "lbkt": "[",
    "rbkt": "]",
    "lbrc": "{",
    "rbrc": "}",
    "lpar": "(",
    "rpar": ")",
    "grave": "`",
    "home": "⇱",
    "end": "⇲",
    "pg_up": "⇞",
    "pg_dn": "⇟",
    "tab": "⇥",
    "bt_sel": "sel",
    "bt_prv": "◄",
    "bt_nxt": "►",
    "bt_clr": "⎚",
    "c_vol_dn": "▆▄▁",
    "c_vol_up": "▁▄▆",
    "c_prev": "⏮",
    "c_next": "⏭",
    "c_play": "▶",
} | {f"n{n}": str(n) for n in range(10)}


def code_to_text(code):
    code = str(code).lower()
    return _code_to_text.get(code, code.upper())


modifier_alias = {
    "LCTRL": "c",
    "RCTRL": "c",
    "LALT": "a",
    "RALT": "ra",
    "LSHIFT": "s",
    "RSHIFT": "s",
    "RGUI": "❖",
    "LGUI": "❖",
}
hyper = {m for m in modifier_alias if m.startswith("L")}


@dataclass(slots=True, init=False)
class Key:
    behavior: str
    args: list[str | int]
    is_pressed: bool = False
    is_transparent: bool = False
    are_mods_comb: bool = False

    def __init__(
        self,
        behavior: str,
        args: list[str | int | list[str]],
    ):
        self.behavior = behavior
        self.args = args

        self.is_pressed = False
        self.is_transparent = False
        self.are_mods_comb = False

    def combine_modifiers(self):
        out = []
        tmp = []
        for arg in self.args:
            if isinstance(arg, str) and arg.startswith("__"):
                tmp.append(arg[2:])
            else:
                if tmp:
                    tmp.append(arg)
                    out.append(tmp)
                    tmp = []
                else:
                    out.append(arg)

        self.are_mods_comb = True
        self.args = out

    def __str__(self):
        if not self.are_mods_comb:
            self.combine_modifiers()
        match self.behavior:
            case "kp":
                code = self.args[0]
                return self.arg_to_str(code)
            case "none":
                return "✗"
            case "caps_word":
                return "⇪"
            case "bootloader":
                return "↻"
            case "reset":
                return "↺"
            case "mt":
                return f"{self.arg_to_str(self.args[0])} ─── {self.arg_to_str(self.args[1])}"
            case _:
                return (
                    f'{self.behavior} {" ".join(self.arg_to_str(a) for a in self.args)}'
                )

    def arg_to_str(self, arg):
        match arg:
            case int(_):
                return str(arg)
            case str(_):
                return code_to_text(arg)
            case list(_):
                if set(arg) == hyper:
                    return "hyper"
                parts = [modifier_alias.get(p, p) for p in arg]
                return f"{'+'.join(parts[:-1])}+{code_to_text(parts[-1])}"


@dataclass(slots=True)
class Layer:
    name: str
    keys: list[Key]

    def __str__(self):
        return self.name.replace('"', "")


class Keyboard:
    layers: list[Layer]

    def __init__(self, layers):
        self.layers = list(layers)
        self._evaluate_behaviors()

    def _evaluate_behaviors(self):
        for layer_idx, layer in enumerate(self.layers):
            for key_idx, key in enumerate(layer.keys):
                match key.behavior:
                    case "trans":
                        upper = self.layers[layer_idx - 1].keys[key_idx]
                        key.behavior = upper.behavior
                        key.args = upper.args
                        key.is_transparent = True
                    case "lt":
                        key.behavior = "kp"
                        lay_idx = key.args[0]
                        key.args = key.args[1:]
                        self.layers[lay_idx].keys[key_idx].is_pressed = True

                    case "to":
                        lay_idx = key.args[0]
                        assert type(lay_idx) == int, (layer_idx, key_idx, lay_idx)
                        key.args[0] = str(self.layers[lay_idx])

    def __iter__(self):
        return iter(self.layers)

    def __len__(self):
        return len(self.layers)


class SplitLayout:
    def __init__(self, height, width, thumbs=0):
        assert thumbs < width, "How are you typing?"
        self.width = width
        self.height = height
        self.thumbs = thumbs
        self.row_legth = 2 * width

    @property
    def amount_of_keys(self):
        return (self.width * self.height + self.thumbs) * 2

    def key_coord(
        self,
        key_index,
        key_width,
        key_height,
        half_separation,
    ):
        matrix_size = self.height * self.row_legth
        if key_index < matrix_size:
            x_pos = key_index % self.row_legth
            y_pos = key_index // self.row_legth
        else:
            y_pos = self.height
            thumb_index = key_index - matrix_size
            x_pos = (self.width - self.thumbs) + thumb_index
        side = 0 if x_pos < self.width else 1
        return (
            x_pos * key_width + half_separation * side,
            y_pos * key_height,
        )

    def size(self, key_width, key_height, half_separation):
        return (
            self.width * key_width * 2 + half_separation,
            (self.height + (1 if self.thumbs else 0)) * key_height,
        )
