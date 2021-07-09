import pprint
import AppKit
import ezui
from mojo.UI import getDefault, CurrentGlyphWindow
from fontParts.fontshell import RGuideline
from lib.fontObjects.fontPartsWrappers import RGuideline
from mojo.extensions import getExtensionDefault
from .defaults import extensionIdentifier
from .smart import parseRules

numberTextFieldWidth = 50
noColor = (1.0, 1.0, 1.0, 1.0)

class GuidelineEditorController(ezui.WindowController):

    def build(self, guideline, glyph, glyphEditor):
        self.guideline = guideline
        self.glyph = glyph
        self.editor = glyphEditor

        # self.defaultColors = getExtensionDefault(extensionIdentifier + ".swatchColors")
        self.defaultColors = [(1, 0, 0, 1)]

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
                ),
                dict(
                    identifier="italicAnglePushButton",
                    type="PushButton",
                    text="Italic Angle",
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

        # rules
        rulesDescription = dict(
            identifier="rules",
            type="TextEditor",
            text="",
            width=175,
            height=100
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
                ),
                dict(
                    type="Item",
                    text="Rules:",
                    itemDescription=rulesDescription
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
        self.enableRulesEditor(startup=True)

    def started(self):
        self.w.open()

    def enableRulesEditor(self, startup=False):
        rulesEditor = self.w.findItem("rules")
        editable = self.guideline.glyph is None
        if not startup:
            if rulesEditor.getNSTextView().isEditable() == editable:
                return
        if not editable:
            rules = ""
        else:
            rules = self.guideline.naked().lib.get(
                extensionIdentifier + ".rules",
                ""
            )
        rulesEditor.set(rules)
        rulesEditor.getNSTextView().setEditable_(editable)

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

    def italicAnglePushButtonCallback(self, sender):
        angleTextField = self.w.findItem("angleTextField")
        angle = self.glyph.font.info.italicAngle
        if angle is None:
            angle = 0
        angle += 90
        angleTextField.set(angle)
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
        rules = data["rules"]
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
        if wantsGlobal:
            parsed = parseRules(rules, macros={})
            if isinstance(parsed, str):
                print(parsed)
            else:
                guideline.naked().lib[
                    extensionIdentifier + ".rules"
                ] = rules
        self.enableRulesEditor()



if __name__ == "__main__":
    from defaults import extensionIdentifier
    from smart import parseRules

    editor = CurrentGlyphWindow()
    glyph = CurrentGlyph()
    font = glyph.font
    guideline = font.guidelines[0]
    GuidelineEditorController(guideline, glyph, editor.getGlyphView())