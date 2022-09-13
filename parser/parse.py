from io import StringIO
from pathlib import Path

from pcpp.preprocessor import Action, OutputDirective, Preprocessor
from tree_sitter import Language, Parser

from keyboard import Key, Keyboard, Layer


class PP(Preprocessor):
    def on_include_not_found(
        self, is_malformed, is_system_include, curdir, includepath
    ):
        raise OutputDirective(Action.IgnoreAndPassThrough)


preprocessor = PP()

preprocessor.line_directive = "//"  # Show comment instead of directive

# Define preappliad modifiers
preprocessor.define("LA(ARG)  __a  ARG")
preprocessor.define("LS(ARG)  __s  ARG")
preprocessor.define("LC(ARG)  __c  ARG")
preprocessor.define("LG(ARG)  __g  ARG")


preprocessor.define("RA(ARG) __ra ARG")
preprocessor.define("RS(ARG) __s ARG")
preprocessor.define("RG(ARG) __g ARG")
preprocessor.define("RC(ARG) __c ARG")

Language.build_library(
    # Store the library in the `build` directory
    "build/parser_lib.so",
    ["tree-sitter-devicetree"],
)

parser = Parser()
devicetree = Language("build/parser_lib.so", "devicetree")
parser.set_language(devicetree)

keymap_query = devicetree.query(
    """
    (
        (node (property
               value:(string_literal) @compatible_value)
            (node) @layer
        )
    (#match? @compatible_value "zmk,keymap")
    )
    """
)


layer_query = devicetree.query(
    """
    (
        (node
          name: (identifier) @name

         (property
               value:(string_literal) @label)?
         (property
               value:(integer_cells) @cells)
        )
    )
    """
)


def preprocess(text):
    preprocessor.parse(text)
    preprocessed = StringIO()
    preprocessor.write(preprocessed)
    # print(preprocessed.getvalue().encode())
    return preprocessed.getvalue().encode()


def _parse_cells(cells):
    keys = []
    for val in cells.named_children:
        type = val.type
        text = val.text.decode()
        match type:
            case "reference":
                key = Key(behavior=text[1:], args=[])
                keys.append(key)
            case "identifier":
                keys[-1].args.append(text)
            case "integer_literal":
                keys[-1].args.append(int(text))
    return keys


def _parse_layers(layer_nodes):
    for layer in layer_nodes:
        captures = {k: v for v, k in layer_query.captures(layer)}
        name = (captures.get("label") or captures.get("name")).text.decode()
        cells = captures.get("cells")
        yield Layer(name=name, keys=_parse_cells(cells))


def parse_keyboard(text):
    tree = parser.parse(text)

    captures = keymap_query.captures(tree.root_node)
    layers = (node for node, name in captures if name == "layer")

    return Keyboard(_parse_layers(layers))
