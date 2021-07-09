from mojo.extensions import registerExtensionDefaults
try:
    from .smart import parseRules
except ImportError:
    from smart import parseRules

extensionIdentifier = "com.typesupply.GuideTool"

macros = """
> lowercase
category: Ll

> uppercase
category: Lu
name: *.uc

> smallcaps
name: *.sc*

> accents
name: circumflex
name: caron
name: tilde
name: breve
name: dotaccent
name: ring
name: hungarumlaut
name: ogonek
name: grave
name: acute
name: dieresis
name: macron
name: cedilla

> numbers
category: Nd

> tabular:
name: *.tab*

> currency
name: dollar
name: cent
name: sterling
name: yen
name: Euro
name: uni20A9
name: numbersign
name: degree

> fractions
name: percent
name: perthousand
name: fraction
name: *.num
name: *.den

> legal
name: section
name: paragraph
name: copyright
name: uni24C5

> math
name: minus
name: notequal
name: lessequal
name: greaterequal
name: approxequal
name: multiply
name: plus
name: less
name: equal
name: greater
name: plusminus
name: divide

> containers
name: parenleft
name: parenright
name: bracketleft
name: bracketright
name: braceleft
name: braceright

> slashes
name: slash
name: backslash
name: bar
name: brokenbar

> punctuation
name: comma
name: period
name: ellipsis
name: colon
name: semicolon
name: periodcentered
name: question
name: questiondown
name: exclam
name: exclamdown

> dashes
name: hyphen
name: endash
name: emdash
name: bullet
name: underscore

> asterisk
name: asterisk
name: dagger
name: daggerdbl

> quotes
name: quotedblleft
name: quotedblright
name: quoteleft
name: quoteright
name: quotesingle
name: quotedbl
name: quotesinglbase
name: quotedblbase

> guillemot
name: guillemotleft
name: guillemotright
name: guilsinglleft
name: guilsinglright
"""

defaultMacros = {}
current = None
for line in macros.splitlines():
    line = line.split("#")[0].strip()
    if not line:
        continue
    if line.startswith(">"):
        current = line[1:].strip()
        defaultMacros[current] = []
    else:
        defaultMacros[current].append(line)
for name, lines in defaultMacros.items():
    rules = parseRules("\n".join(lines))
    assert isinstance(rules, dict)
    defaultMacros[name] = rules

# Registry
# --------

defaults = {
    "smartMacros" : defaultMacros,
    "snapToPoint" : True,
    "snapToFuturePoint" : True,
    "wantItalicAngle" : True,
    "highlightAlphaScale" : 0.15,
    "swatchColors" : [
        (1, 0, 0, 0.5),
        (0, 1, 0, 1),
        (0, 0, 1, 1),
        (1, 1, 0, 1),
        (1, 0, 1, 1),
        (0, 1, 1, 1)
    ]
}

defaults = {
    extensionIdentifier + "." + key : value
    for key, value in defaults.items()
}

def main():
    registerExtensionDefaults(defaults)