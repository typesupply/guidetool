import AppKit
import ezui
from mojo.extensions import (
    registerExtensionDefaults,
    getExtensionDefault,
    setExtensionDefault,
    removeExtensionDefault
)
from mojo.events import postEvent
import objc
objc.setVerbose(True)

extensionIdentifier = "com.typesupply.GuideTool"

defaultMacros = """
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
""".strip()

# Registry
# --------

defaults = {
    "smartMacros" : defaultMacros,
    "snapToPoint" : True,
    "snapToFuturePoint" : True,
    "wantItalicAngle" : True,
    "highlightAlphaScale" : 0.15,
    "swatchColors" : [
        (1, 0, 0, 1),
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

# Window
# ------

class GuideToolDefaultsWindowController(ezui.WindowController):

    def build(self):
        extensionIdentifierLength = len(extensionIdentifier) + 1
        settings = {
            key[extensionIdentifierLength:] : getExtensionDefault(key)
            for key in defaults.keys()
        }

        itemWidth = 200

        # highlight alpha
        highlightAlphaScaleDescription = dict(
            identifier="highlightAlphaScale",
            type="Slider",
            minValue=0,
            maxValue=1.0,
            value=settings["highlightAlphaScale"]
        )

        # snap to point
        snapToDescription = dict(
            identifier="snapTo",
            type="Checkboxes",
            checkboxDescriptions=[
                dict(
                    identifier="snapToPoint",
                    text="Point",
                    value=settings["snapToPoint"],
                ),
                dict(
                    identifier="snapToFuturePoint",
                    text="Future Point",
                    value=settings["snapToFuturePoint"],
                )
            ]
        )

        # want italic angle
        wantItalicAngleDescription = dict(
            identifier="wantItalicAngle",
            type="RadioButtons",
            text=[
                "90°",
                "Italic Angle"
            ],
            selected=settings["wantItalicAngle"]
        )

        # colors
        colorsDescription = dict(
            identifier="colorsTable",
            type="Table",
            columnDescriptions=[
                dict(
                    identifier="color",
                    cellDescription=dict(
                        cellType="ColorWell",
                    ),
                    editable=True
                )
            ],
            items=[
                {
                    "color" : tuple(color)
                }
                for color in settings["swatchColors"]
            ],
            footerDescription=[
                dict(
                    identifier="colorsTableAddRemoveButton",
                    type="AddRemoveButton"
                )
            ],
            showColumnTitles=False,
            width=itemWidth,
            height=100
        )

        # macros
        macrosDescription = dict(
            identifier="smartMacros",
            type="TextEditor",
            text=settings["smartMacros"],
            width=itemWidth,
            height=200
        )

        # window
        windowContent = dict(
            identifier="settingsForm",
            type="TwoColumnForm",
            contentDescriptions=[
                dict(
                    type="Item",
                    text="Selection Highlight:",
                    itemDescription=highlightAlphaScaleDescription
                ),
                dict(
                    type="Item",
                    text="Snap To:",
                    itemDescription=snapToDescription
                ),
                dict(
                    type="Item",
                    text="Vertical Angle:",
                    itemDescription=wantItalicAngleDescription
                ),
                dict(
                    type="Item",
                    text="Colors:",
                    itemDescription=colorsDescription
                ),
                dict(
                    type="Item",
                    text="Macros:",
                    itemDescription=macrosDescription
                ),
            ]
        )
        windowDescription = dict(
            type="Window",
            size=("auto", "auto"),
            title="Guide Tool Settings",
            contentDescription=windowContent
        )
        self.w = ezui.makeItem(
            windowDescription,
            controller=self
        )

    def started(self):
        self.w.open()

    def settingsFormCallback(self, sender):
        self.storeSettings()

    def colorsTableAddRemoveButtonAddCallback(self, sender):
        table = self.w.findItem("colorsTable")
        item = dict(
            color=(0, 0, 0, 1)
        )
        items = table.get()
        items.append(item)
        table.set(items)
        self.storeSettings()

    def colorsTableAddRemoveButtonRemoveCallback(self, sender):
        table = self.w.findItem("colorsTable")
        selection = table.getSelectedIndexes()
        items = table.get()
        for index in reversed(sorted(selection)):
            del items[index]
        table.set(items)
        self.storeSettings()

    def storeSettings(self):
        settings = self.w.get()["settingsForm"]
        settings["swatchColors"] = [
            item["color"]
            for item in
            settings.pop("colorsTable")
        ]
        for key, value in settings.pop("snapTo").items():
            settings[key] = value
        for key, value in settings.items():
            key = extensionIdentifier + "." + key
            setExtensionDefault(key, value)
        postEvent(
            extensionIdentifier + ".defaultsChanged"
        )


def main():
    registerExtensionDefaults(defaults)
    # XXX
    # very early development stored a dict
    key = extensionIdentifier + ".smartMacros"
    value = getExtensionDefault(key)
    if not isinstance(value, str):
        setExtensionDefault(key, defaultMacros)

