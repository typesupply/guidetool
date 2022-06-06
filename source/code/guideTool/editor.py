import pprint
import AppKit
import ezui
from mojo.UI import getDefault, CurrentGlyphWindow
from fontParts.fontshell import RGuideline
from lib.fontObjects.fontPartsWrappers import RGuideline
from mojo.extensions import getExtensionDefault
from mojo.events import postEvent
from .defaults import extensionIdentifier
from .smart import parseRules
from .compatibility import getGuidelineLibValue, setGuidelineLibValue

numberTextFieldWidth = 50
noColor = (1.0, 1.0, 1.0, 1.0)

class GuidelineEditorController(ezui.WindowController):

    def build(self, guideline, glyph, glyphEditor):
        self.guideline = guideline
        self.glyph = glyph
        self.editor = glyphEditor

        self.defaultColors = getExtensionDefault(extensionIdentifier + ".swatchColors")

        positionValueType = "number"
        roundTo = getDefault("glyphViewRoundValues", defaultClass=int)
        if roundTo >= 1:
            positionValueType = "integer"

        colorSwatchItems = [
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
            colorSwatchItems.append(
                dict(
                    identifier=f"color_{i}",
                    image=image,
                    callback="colorSwatchesPullDownButtonCallback"
                )
            )

        content = """
        = TwoColumnForm

        : Level:
        ( ) Font @levelRadioButtons
        ( ) Glyph

        : Name:
        [__] @nameTextField

        : Position:
        * HorizontalStack
        > [__] @xPositionTextField
        > [__] @yPositionTextField

        : Angle:
        * HorizontalStack
        > [__]° @angleTextField
        > (Italic Angle) @italicAnglePushButton

        : Color:
        * HorizontalStack
        > * ColorWell @colorColorWell
        > (...) @colorSwatchesPullDownButton

        : Magnetic:
        --X-- @magneticSlider

        :
        [ ] Show Measurements @measurementsCheckbox

        : Rules:
        [[__]] @rulesTextEditor
        """
        descriptionData = dict(
            content=dict(
                titleColumnWidth=75,
                itemColumnWidth=175
            ),
            levelRadioButtons=dict(
                selected=not guideline.naked().isGlobal
            ),
            nameTextField=dict(
                value=guideline.name
            ),
            xPositionTextField=dict(
                width=numberTextFieldWidth,
                valueType=positionValueType,
                value=guideline.x
            ),
            yPositionTextField=dict(
                width=numberTextFieldWidth,
                valueType=positionValueType,
                value=guideline.y
            ),
            angleTextField=dict(
                width=numberTextFieldWidth,
                valueType="number",
                value=guideline.angle,
            ),
            colorColorWell=dict(
                width=numberTextFieldWidth,
                color=guideline.color
            ),
            colorSwatchesPullDownButton=dict(
                itemDescriptions=colorSwatchItems
            ),
            magneticSlider=dict(
                minValue=2,
                maxValue=20,
                value=guideline.magnetic
            ),
            measurementsCheckbox=dict(
                value=guideline.showMeasurements
            ),
            rulesTextEditor=dict(
                height=100
            )
        )

        self.w = ezui.EZPopUp(
            content=content,
            descriptionData=descriptionData,
            controller=self,
            parent=glyphEditor
        )
        self.haveStartedUndo = False
        self.previousData = self.w.getItemValues()
        self.enableRulesEditor(startup=True)

    def started(self):
        self.w.open()

    def enableRulesEditor(self, startup=False):
        rulesEditor = self.w.getItem("rulesTextEditor")
        editable = self.guideline.glyph is None
        if not startup:
            if rulesEditor.getNSTextView().isEditable() == editable:
                return
        if not editable:
            rules = ""
        else:
            rules = getGuidelineLibValue(
                self.guideline,
                extensionIdentifier + ".rules",
                ""
            )
        rulesEditor.set(rules)
        rulesEditor.getNSTextView().setEditable_(editable)

    def colorSwatchesPullDownButtonCallback(self, sender):
        button = self.w.getItem("colorSwatchesPullDownButton")
        identifier = button.getMenuItemIdentifier(sender)
        if identifier == "default":
            color = None
        else:
            i = int(identifier.split("_")[-1])
            color = self.defaultColors[i]
        colorWell = self.w.getItem("colorColorWell")
        # XXX
        if color is None:
            color = noColor
        colorWell.set(color)
        form = self.w.getItem("content")
        self.contentCallback(form)

    def italicAnglePushButtonCallback(self, sender):
        angleTextField = self.w.getItem("angleTextField")
        angle = self.glyph.font.info.italicAngle
        if angle is None:
            angle = 0
        angle += 90
        angleTextField.set(angle)
        form = self.w.getItem("content")
        self.contentCallback(form)

    def contentCallback(self, sender):
        glyph = self.glyph
        font = glyph.font
        guideline = self.guideline
        isGlobal = guideline.naked().isGlobal
        data = self.w.getItemValues()
        if data == self.previousData:
            return
        self.previousData = data
        if not self.haveStartedUndo:
            guideline.naked().prepareUndo("Change Guideline")
            self.haveStartedUndo = True
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
                # XXX mark the text as invalid
                # parsed will be an error string
                pass
            else:
                setGuidelineLibValue(
                    guideline,
                    extensionIdentifier + ".rules",
                    rules
                )
        self.enableRulesEditor()
        postEvent(
            extensionIdentifier + ".guidelineEditedInEditor",
            guideline=self.guideline
        )

    def windowWillClose(self, sender):
        if self.haveStartedUndo:
            self.guideline.naked().performUndo()


if __name__ == "__main__":
    editor = CurrentGlyphWindow()
    glyph = CurrentGlyph()
    font = glyph.font
    guideline = font.guidelines[0]
    GuidelineEditorController(guideline, glyph, editor.getGlyphView())