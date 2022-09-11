from pathlib import Path

from draw import Painter
from keyboard import SplitLayout
from parse import parse_keyboard, preprocess

_config = Path(__file__).parents[1]

keyboard = (_config / "config/cradio.keymap").absolute()
keyboard = parse_keyboard(preprocess(keyboard.read_text()))
layout = SplitLayout(3, 5, 2)
painter = Painter(keyboard=keyboard, layout=layout)
(_config / "keymap.svg").write_text(painter.draw_keyboard())
