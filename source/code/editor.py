import pprint
import AppKit
import ezui
from mojo.UI import getDefault, CurrentGlyphWindow
from fontParts.fontshell import RGuideline
from lib.fontObjects.fontPartsWrappers import RGuideline

import objc
objc.setVerbose(True)

numberTextFieldWidth = 50
noColor = (1.0, 1.0, 1.0, 1.0)

"""
- italic angle button
- undo state
- colors from prefs

Issues:
- window doesn't appear in correct place
- needs to be easier to get a colorwell to auto fit
- get item heights and set row height to max of those
- number value type doesn't work
- set colorwell color to None
- radio buttons height in grid
- pop up button isn't in the doc
- pull down example
- action button example
"""

class GuidelineEditorController(ezui.WindowController):

    def build(self, guideline, glyph, glyphEditor):
        self.guideline = guideline
        self.glyph = glyph
        self.editor = glyphEditor

        self.defaultColors = [
            (1, 0, 0, 0.5),
            (0, 1, 0, 1),
            (0, 0, 1, 1),
            (1, 1, 0, 1),
            (1, 0, 1, 1),
            (0, 1, 1, 1)
        ]

        # level: radio buttons
        levelDescription = dict(
            identifier="levelRadioButtons",
            type="RadioButtons",
            text=[
                "Font",
                "Glyph"
            ],
            selected=not guideline.naked().isGlobal
        )

        # name: text field
        nameDescription = dict(
            identifier="nameTextField",
            type="TextField",
            value=guideline.name
        )

        # position: text field, text field
        positionValueType = "number"
        roundTo = getDefault("glyphViewRoundValues", defaultClass=int)
        if roundTo >= 1:
            positionValueType = "integer"
        positionDescription = dict(
            # identifier="positionStack",
            type="HorizontalStack",
            contentDescriptions=[
                dict(
                    identifier="xPositionTextField",
                    type="TextField",
                    valueType=positionValueType,
                    width=numberTextFieldWidth,
                    value=guideline.x
                ),
                dict(
                    identifier="yPositionTextField",
                    type="TextField",
                    valueType=positionValueType,
                    width=numberTextFieldWidth,
                    value=guideline.y
                )
            ]
        )

        # angle: text field, label, button
        angleValueType = "number"
        angleDescription = dict(
            # identifier="angleStack",
            type="HorizontalStack",
            contentDescriptions=[
                dict(
                    identifier="angleTextField",
                    type="TextField",
                    value=guideline.angle,
                    valueType=angleValueType,
                    width=numberTextFieldWidth
                ),
                dict(
                    type="Label",
                    text="°"
                )
            ]
        )

        # color: color well, pull down
        colorWellDescription = dict(
            identifier="colorColorWell",
            type="ColorWell",
            height=25,
            width=numberTextFieldWidth,
            color=guideline.color
        )
        colorSwatches = [
            dict(
                identifier="default",
                text="Default",
                callback="colorSwatchesPullDownButtonCallback"
            )
        ]
        for i, color in enumerate(self.defaultColors):
            w = 50
            h = 5
            image = AppKit.NSImage.alloc().initWithSize_((w, h))
            image.lockFocus()
            AppKit.NSColor.whiteColor().set()
            AppKit.NSRectFill(((0, 0), (w, h)))
            AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(*color).set()
            AppKit.NSRectFillUsingOperation(
                ((0, 0), (w, h)),
                AppKit.NSCompositeSourceOver
            )
            image.unlockFocus()
            colorSwatches.append(
                dict(
                    identifier=f"color_{i}",
                    image=image,
                    callback="colorSwatchesPullDownButtonCallback"
                )
            )
        colorSwatchesDescription = dict(
            identifier="colorSwatchesPullDownButton",
            type="ActionButton",
            itemDescriptions=colorSwatches
        )
        colorDescription = dict(
            # identifier="colorStack",
            type="HorizontalStack",
            contentDescriptions=[
                colorWellDescription,
                colorSwatchesDescription
            ]
        )

        # magnetic: slider
        magneticDescription = dict(
            identifier="magneticSlider",
            type="Slider",
            minValue=2,
            maxValue=20,
            value=guideline.magnetic
        )

        # measurements: checkbox
        measurementDescription = dict(
            identifier="measurementsCheckbox",
            type="Checkbox",
            text="Show Measurements",
            value=guideline.showMeasurements
        )

        # window
        windowContent = dict(
            identifier="guidelineForm",
            type="TwoColumnForm",
            contentDescriptions=[
                dict(
                    type="Item",
                    text="Level:",
                    itemDescription=levelDescription
                ),
                dict(
                    type="Item",
                    text="Name:",
                    itemDescription=nameDescription
                ),
                dict(
                    type="Item",
                    text="Position:",
                    itemDescription=positionDescription
                ),
                dict(
                    type="Item",
                    text="Angle:",
                    itemDescription=angleDescription
                ),
                dict(
                    type="Item",
                    text="Color:",
                    itemDescription=colorDescription
                ),
                dict(
                    type="Item",
                    text="Magnetic:",
                    itemDescription=magneticDescription
                ),
                dict(
                    type="Item",
                    itemDescription=measurementDescription
                )
            ]
        )
        windowDescription = dict(
            type="PopUp",
            size=("auto", "auto"),
            contentDescription=windowContent,
            parent=glyphEditor
        )
        self.w = ezui.makeItem(
            windowDescription,
            controller=self
        )

    def started(self):
        self.w.open()

    def colorSwatchesPullDownButtonCallback(self, sender):
        button = self.w.findItem("colorSwatchesPullDownButton")
        identifier = button.getMenuItemIdentifier(sender)
        if identifier == "default":
            color = None
        else:
            i = int(identifier.split("_")[-1])
            color = self.defaultColors[i]
        colorWell = self.w.findItem("colorColorWell")
        # XXX
        if color is None:
            color = noColor
        colorWell.set(color)
        form = self.w.findItem("guidelineForm")
        self.guidelineFormCallback(form)

    def guidelineFormCallback(self, sender):
        glyph = self.glyph
        font = glyph.font
        guideline = self.guideline
        isGlobal = guideline.naked().isGlobal
        data = self.w.get()["guidelineForm"]
        wantsGlobal = not data["levelRadioButtons"]
        name = data["nameTextField"]
        if not name:
            name = None
        x = data["xPositionTextField"]
        y = data["yPositionTextField"]
        angle = data["angleTextField"]
        color = data["colorColorWell"]
        magnetic = data["magneticSlider"]
        measurements = data["measurementsCheckbox"]
        if color == noColor:
            color = None
        if isGlobal != wantsGlobal:
            if wantsGlobal:
                glyph.removeGuideline(guideline)
                guideline = font.appendGuideline(
                    guideline=guideline.copy()
                )
            else:
                font.removeGuideline(guideline)
                guideline = glyph.appendGuideline(
                    guideline=guideline.copy()
                )
            self.guideline = guideline
        guideline.name = name
        guideline.position = (x, y)
        guideline.angle = angle
        guideline.color = color
        guideline.magnetic = magnetic
        guideline.showMeasurements = measurements


if __name__ == "__main__":
    editor = CurrentGlyphWindow()
    glyph = CurrentGlyph()
    font = glyph.font
    guideline = font.guidelines[0]
    GuidelineEditorController(guideline, glyph, editor.getGlyphView())