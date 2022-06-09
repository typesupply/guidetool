import AppKit
import ezui
from mojo.extensions import getExtensionDefault
from mojo.UI import getDefault
from mojo.events import postEvent
from .defaults import extensionIdentifier
from .smart import parseRules
from .compatibility import getGuidelineLibValue, setGuidelineLibValue

numberTextFieldWidth = 50
noColor = (1.0, 1.0, 1.0, 1.0)

class GuideToolGuidelineEditor(ezui.TwoColumnForm):

    font = None
    glyph = None
    guideline = None

    def __init__(self,
            callback=None,
            identifier=None,
            container=None,
            controller=None,
            descriptionData={},
            onlyFontLevel=False
        ):
        callback = ezui.tools.callback.findCallback(
            callback,
            identifier=identifier,
            controller=controller
        )
        self.externalCallback = callback
        self.onlyFontLevel = onlyFontLevel
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

        levelContents = ""
        if not onlyFontLevel:
            levelContents = """
            : Level:
            ( ) Font @levelRadioButtons
            ( ) Glyph
            """

        contents = f"""
        {levelContents}

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
            levelRadioButtons=dict(),
            nameTextField=dict(),
            xPositionTextField=dict(
                width=numberTextFieldWidth,
                valueType=positionValueType
            ),
            yPositionTextField=dict(
                width=numberTextFieldWidth,
                valueType=positionValueType
            ),
            angleTextField=dict(
                width=numberTextFieldWidth,
                valueType="number"
            ),
            colorColorWell=dict(
                width=numberTextFieldWidth
            ),
            colorSwatchesPullDownButton=dict(
                itemDescriptions=colorSwatchItems
            ),
            magneticSlider=dict(
                minValue=2,
                maxValue=20
            ),
            measurementsCheckbox=dict(),
            rulesTextEditor=dict(
                height=100
            )
        )
        contents = ezui.tools.normalizeContentDescriptions(
            contents,
            descriptionData
        )
        super().__init__(
            contents=contents,
            descriptionData=descriptionData,
            identifier=identifier,
            titleColumnWidth=75,
            itemColumnWidth=175,
            callback=self.internalCallback,
            container=container,
            controller=self
        )
        self.haveStartedUndo = False
        self.previousData = self.getItemValues()
        self.enableRulesEditor(startup=True)

    def internalCallback(self, sender):
        if self.guideline is None:
            return
        glyph = self.glyph
        font = self.font
        guideline = self.guideline
        isGlobal = guideline.naked().isGlobal
        data = self.getItemValues()
        if data == self.previousData:
            return
        self.previousData = data
        if not self.haveStartedUndo:
            guideline.naked().prepareUndo("Change Guideline")
            self.haveStartedUndo = True
        name = data["nameTextField"]
        if not name:
            name = None
        x = data["xPositionTextField"]
        if x is None:
            x = guideline.x
        y = data["yPositionTextField"]
        if y is None:
            y = guideline.y
        angle = data["angleTextField"]
        if angle is None:
            angle = guideline.angle
        color = data["colorColorWell"]
        if color == noColor:
            color = None
        magnetic = data["magneticSlider"]
        measurements = data["measurementsCheckbox"]
        rules = data["rulesTextEditor"]
        wantsGlobal = True
        if not self.onlyFontLevel:
            wantsGlobal = not data["levelRadioButtons"]
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
        guideline.x = x
        guideline.y = y
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
        if self.externalCallback is not None:
            self.externalCallback(self)

    def enableRulesEditor(self, startup=False):
        rulesEditor = self.getItem("rulesTextEditor")
        if self.guideline is None:
            rules = ""
            editable = False
        else:
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
        button = self.getItem("colorSwatchesPullDownButton")
        identifier = button.getMenuItemIdentifier(sender)
        if identifier == "default":
            color = None
        else:
            i = int(identifier.split("_")[-1])
            color = self.defaultColors[i]
        colorWell = self.getItem("colorColorWell")
        # XXX
        if color is None:
            color = noColor
        colorWell.set(tuple(color))
        self.internalCallback(self)

    def italicAnglePushButtonCallback(self, sender):
        angleTextField = self.getItem("angleTextField")
        angle = self.font.info.italicAngle
        if angle is None:
            angle = 0
        angle += 90
        angleTextField.set(angle)
        self.internalCallback(self)

    def setObjects(self, font, glyph, guideline):
        self.font = font
        self.glyph = glyph
        self.guideline = guideline
        color = guideline.color
        if color is None:
            color = noColor
        isGlobal = guideline.naked().isGlobal
        rules = ""
        if isGlobal:
            rules = getGuidelineLibValue(
                self.guideline,
                extensionIdentifier + ".rules",
                ""
            )
        data = dict(
            nameTextField=guideline.name,
            xPositionTextField=guideline.x,
            yPositionTextField=guideline.y,
            angleTextField=guideline.angle,
            colorColorWell=color,
            magneticSlider=guideline.magnetic,
            measurementsCheckbox=guideline.showMeasurements,
            rulesTextEditor=rules
        )
        if not self.onlyFontLevel:
            data["levelRadioButtons"] = not isGlobal
        self.setItemValues(data)

    def closeUndoState(self):
        if self.haveStartedUndo:
            self.guideline.naked().performUndo()

ezui.registerClass("GuideToolGuidelineEditor", GuideToolGuidelineEditor)
